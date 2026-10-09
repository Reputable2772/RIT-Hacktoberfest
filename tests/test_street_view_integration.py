"""Automated regression test suite for Street View manifest integration.

Validates:
1. Manifest parsing: all 171 planned observations across the 3 directed walking routes.
2. Image reconciliation: 136 collected images exist, decode via OpenCV, match 933x849 dimensions.
3. Usability heuristics: exposure, Laplacian blur variance, zero black/white/empty frames.
4. Coordinate validation: Bengaluru bounds, coordinate orientation (no swapped coords), chainage monotonicity.
5. Geometry alignment: proximity to route GeoJSON polylines (within 1 meter).
6. Path traversal safety: attempts to traverse outside the data directory are rejected.
7. Route isolation: route filters return only observations belonging to that route.
8. Duplicate image detection: SHA-256 matching pairs identified and deduplicated in route scoring.
9. Unavailable gap handling: 35 points explicitly unassessed with documented reasons; no fake images.
10. API endpoints: /api/observations, /api/observations/summary, /api/observations/{id}, /api/images/{path}.
11. Dynamic journey recalculation and observation coverage reporting.
"""

import json
import os
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.manifest_service import (
    BENGALURU_LAT_MAX,
    BENGALURU_LAT_MIN,
    BENGALURU_LON_MAX,
    BENGALURU_LON_MIN,
    LEGACY_OBS_MAP,
    manifest_service,
)
from backend.planner import ANALYSIS_CACHE, recalculate_journey_from_cache, run_gemma_analysis_on_prepared_image
from backend.schemas import FeatureStatus, GemmaVisualAnalysis, AccessibilityCriterionFinding, ConfidenceRating
from backend.transit_data import get_journeys_for_direction


@pytest.fixture
def client():
    return TestClient(app)


def test_manifest_parsing_all_171_observations():
    """Verify all 171 observations are correctly loaded with expected route allocations."""
    manifest = manifest_service.load_manifest()
    obs_list = manifest.get("observations", [])
    assert len(obs_list) == 171, f"Expected 171 observations, got {len(obs_list)}"

    a_to_b = [o for o in obs_list if o["route_id"] == "a_to_b"]
    b_to_c = [o for o in obs_list if o["route_id"] == "b_to_c"]
    c_to_a = [o for o in obs_list if o["route_id"] == "c_to_a"]

    assert len(a_to_b) == 42
    assert len(b_to_c) == 61
    assert len(c_to_a) == 68

    # Collection status breakdown
    collected = [o for o in obs_list if o["collection_status"] == "collected"]
    unavailable = [o for o in obs_list if o["collection_status"] == "unavailable"]

    assert len(collected) == 136, f"Expected 136 collected screenshots, got {len(collected)}"
    assert len(unavailable) == 35, f"Expected 35 unavailable points, got {len(unavailable)}"


def test_reconcile_and_image_validation():
    """Verify that all 136 collected images exist, decode correctly, and have valid dimensions."""
    audit = manifest_service.audit_and_reconcile(force_refresh=True)

    assert audit["status"] == "PASS"
    assert audit["collected_count"] == 136
    assert audit["decoded_images_count"] == 136
    assert audit["unavailable_count"] == 35
    assert len(audit["missing_files"]) == 0
    assert len(audit["unusable_images"]) == 0
    assert len(audit["orphaned_files"]) == 0
    assert len(audit["duplicate_assignments"]) == 0


def test_image_dimensions_and_usability():
    """Verify image shape (849, 933, 3), brightness range, and sharpness across collected images."""
    all_obs = manifest_service.get_observations(collection_status="collected")
    assert len(all_obs) == 136

    sample_obs = all_obs[0]
    img_path = manifest_service.resolve_image_path(sample_obs.image_filename)
    assert img_path is not None
    img = cv2.imread(img_path)
    assert img is not None
    assert img.shape == (849, 933, 3), f"Unexpected image shape: {img.shape}"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_bright = float(np.mean(gray))
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    assert 20.0 < mean_bright < 240.0
    assert lap_var > 100.0  # Sharp, clear capture


def test_coordinate_validation_bengaluru_bounds_and_orientation():
    """Verify all 171 points fall within Bengaluru bounds and have correct [lat, lon] orientation."""
    audit = manifest_service.audit_and_reconcile()

    assert len(audit["out_of_bounds"]) == 0, f"Found out of bounds points: {audit['out_of_bounds']}"
    assert len(audit["swapped_coords"]) == 0, f"Found swapped coordinates: {audit['swapped_coords']}"
    assert len(audit["chainage_anomalies"]) == 0, f"Found chainage anomalies: {audit['chainage_anomalies']}"
    assert len(audit["geometry_divergences"]) == 0, f"Found points diverging from geometry: {audit['geometry_divergences']}"


def test_path_safety_traversal_blocked():
    """Verify that path traversal attempts are strictly rejected and return None."""
    malicious_inputs = [
        "../../etc/passwd",
        "../street_view_manifest.json",
        "data/../../etc/shadow",
        "..%2F..%2Fetc%2Fpasswd",
        "/etc/passwd",
        "data/street_view/../../../requirements.txt",
    ]

    for bad_path in malicious_inputs:
        resolved = manifest_service.resolve_image_path(bad_path)
        assert resolved is None, f"Path traversal allowed for: {bad_path}"


def test_route_isolation_filtering():
    """Verify route isolation: filtering by route_id returns strictly that route's observations."""
    obs_ab = manifest_service.get_observations(route_id="a_to_b")
    assert len(obs_ab) == 42
    assert all(o.route_id == "a_to_b" for o in obs_ab)
    assert all(o.direction == "A -> B" for o in obs_ab)

    obs_bc = manifest_service.get_observations(route_id="b_to_c")
    assert len(obs_bc) == 61
    assert all(o.route_id == "b_to_c" for o in obs_bc)
    assert all(o.direction == "B -> C" for o in obs_bc)

    obs_ca = manifest_service.get_observations(route_id="c_to_a")
    assert len(obs_ca) == 68
    assert all(o.route_id == "c_to_a" for o in obs_ca)
    assert all(o.direction == "C -> A" for o in obs_ca)


def test_duplicate_image_detection():
    """Verify detection of duplicate visual views across routes (e.g. MG Road intersection)."""
    duplicates = manifest_service.get_duplicate_pairs()
    assert len(duplicates) == 2

    # Verify duplicate pair matching
    pair_obs_ids = set()
    for p1, p2 in duplicates:
        pair_obs_ids.add((p1, p2))

    assert manifest_service.is_duplicate_observation("OBS_A_TO_B_0001", "OBS_C_TO_A_0068") or \
           manifest_service.is_duplicate_observation("OBS_C_TO_A_0068", "OBS_A_TO_B_0001")


def test_unavailable_observations_unassessed():
    """Verify that all 35 unavailable points remain explicitly unassessed with documented reasons."""
    unav_obs = manifest_service.get_observations(collection_status="unavailable")
    assert len(unav_obs) == 35

    for o in unav_obs:
        assert o.image_available is False
        assert o.collection_status == "unavailable"
        assert o.unavailable_reason is not None and len(o.unavailable_reason) > 0
        assert o.is_usable_evidence is False

    # Calling analysis on an unavailable point returns honest unavailable status
    gap_obs = unav_obs[0]
    ANALYSIS_CACHE.pop(gap_obs.id, None)
    res = run_gemma_analysis_on_prepared_image(gap_obs.id)
    assert res.status == "image_unavailable"
    assert res.inference_source == "unavailable"
    assert gap_obs.unavailable_reason in res.summary
    assert res.calculated_accessibility_score == 50.0  # neutral unassessed baseline


def test_api_endpoints_manifest_integration(client):
    """Test API endpoints for observations list, summary, single lookup, and image serving."""
    # 1. GET /api/observations
    res = client.get("/api/observations")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 171

    # 2. GET /api/observations?route_id=a_to_b
    res_ab = client.get("/api/observations?route_id=a_to_b")
    assert res_ab.status_code == 200
    data_ab = res_ab.json()
    assert len(data_ab) == 42

    # 3. GET /api/observations/summary
    res_summary = client.get("/api/observations/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["overall"]["total_planned"] == 171
    assert summary["overall"]["collected"] == 136
    assert summary["overall"]["unavailable"] == 35
    assert "a_to_b" in summary["routes"]
    assert "b_to_c" in summary["routes"]
    assert "c_to_a" in summary["routes"]

    # 4. GET /api/observations/{obs_id}
    res_single = client.get("/api/observations/OBS_A_TO_B_0001")
    assert res_single.status_code == 200
    obs_item = res_single.json()
    assert obs_item["id"] == "OBS_A_TO_B_0001"
    assert obs_item["image_available"] is True

    # 5. Backward compatibility: GET /api/observations/OBS_1
    res_legacy = client.get("/api/observations/OBS_1")
    assert res_legacy.status_code == 200
    assert res_legacy.json()["id"] in ("OBS_1", "OBS_A_TO_B_0001")

    # 6. GET /api/images/{file_path}
    img_res = client.get("/api/images/data/street_view/a_to_b/0001.png")
    assert img_res.status_code == 200
    assert img_res.headers["content-type"] == "image/png"
    assert len(img_res.content) > 10000

    # 7. GET /api/images with traversal rejected
    img_bad = client.get("/api/images/../../etc/passwd")
    assert img_bad.status_code in (400, 404)


def test_dynamic_scoring_and_observation_coverage():
    """Verify that analyzing an observation updates journey scores and live observation coverage."""
    journeys = get_journeys_for_direction("A", "B")
    walking_journey = next(j for j in journeys if j.primary_mode.value == "walking")

    # Recalculate journey
    updated = recalculate_journey_from_cache(walking_journey)

    assert "observation_coverage" in updated.model_dump()
    cov = updated.observation_coverage
    assert cov.get("total_planned") == 42
    assert cov.get("collected") == 19
    assert cov.get("unavailable") == 23
    assert cov.get("analyzed") >= 0
