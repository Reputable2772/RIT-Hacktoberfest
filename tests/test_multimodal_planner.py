"""Integration tests for Multimodal Planner, Mode A & Mode B routing, and Gemma Vision."""

import io
from unittest.mock import MagicMock, patch
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.planner import PREPARED_IMAGES_MAP, get_image_path
from backend.schemas import (
    AccessibilityCriterionFinding,
    ConfidenceRating,
    FeatureStatus,
    GemmaVisualAnalysis,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_sharp_test_image() -> bytes:
    """Create a sharp image buffer."""
    img = np.zeros((150, 150, 3), dtype=np.uint8)
    for i in range(0, 150, 15):
        for j in range(0, 150, 15):
            if (i // 15 + j // 15) % 2 == 0:
                img[i : i + 15, j : j + 15] = 220
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def test_get_demo_locations(client):
    """GET /api/locations returns the canonical 3 fixed points: A, B, and C."""
    res = client.get("/api/locations")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    keys = [loc["key"] for loc in data]
    assert keys == ["A", "B", "C"]
    assert any("MG Road" in loc["name"] for loc in data)
    assert any("Cubbon Park" in loc["name"] for loc in data)
    assert any("Majestic" in loc["name"] for loc in data)


def test_get_journeys_and_rankings(client):
    """GET /api/journeys returns A->B, B->C, C->A with selectable rankings."""
    res = client.get("/api/journeys?sort=fastest")
    assert res.status_code == 200
    data = res.json()

    assert "A->B" in data
    assert "B->C" in data
    assert "C->A" in data

    # Verify sorting by fastest
    ab_routes = data["A->B"]
    assert len(ab_routes) >= 2
    durations = [r["total_duration_minutes"] for r in ab_routes]
    assert durations == sorted(durations)

    # Test sorting by least walking
    res_walk = client.get("/api/journeys?sort=least_walking")
    assert res_walk.status_code == 200
    walk_routes = res_walk.json()["A->B"]
    walk_dists = [r["total_walking_distance_meters"] for r in walk_routes]
    assert walk_dists == sorted(walk_dists)


def test_prepared_streetview_files_exist_on_disk():
    """Verify that all 5 prepared Street View images actually exist on disk."""
    for obs_id, meta in PREPARED_IMAGES_MAP.items():
        path = get_image_path(meta["filename"])
        assert path is not None, f"Prepared file {meta['filename']} missing from disk"
        assert len(open(path, "rb").read()) > 10000


def test_analyze_prepared_observation(client):
    """POST /api/analyze-observation/{id} loads actual bytes and returns structured 6 criteria."""
    res = client.post("/api/analyze-observation/OBS_1")
    assert res.status_code == 200
    data = res.json()

    assert data["image_id"] == "OBS_1"
    assert "sidewalk" in data
    assert "curb_ramps" in data
    assert "tactile_paving" in data
    assert "pedestrian_crossings" in data
    assert "obstructions" in data
    assert "surface_damage" in data
    assert data["sidewalk"]["status"] in ("present", "absent", "unknown")
    assert 0.0 <= data["calculated_accessibility_score"] <= 100.0


def test_custom_journey_planning_without_image(client):
    """Mode B: Plan route for arbitrary coordinates without requiring image upfront."""
    req_payload = {
        "origin_name": "Koramangala 5th Block",
        "origin_lat": 12.9352,
        "origin_lon": 77.6245,
        "dest_name": "MG Road",
        "dest_lat": 12.9755,
        "dest_lon": 77.6068,
        "sort": "fastest",
    }
    res = client.post("/api/custom-journey", json=req_payload)
    assert res.status_code == 200
    routes = res.json()
    assert len(routes) >= 2

    # Verify visual evidence is labeled as not supplied
    walking_route = next(r for r in routes if r["primary_mode"] == "walking")
    assert "not_supplied" in walking_route["data_provenance"]["visual_evidence"]
    assert "Unassessed" in walking_route["accessibility_verdict"]


def test_upload_and_analyze_custom_image(client):
    """Mode B: User uploads image for a walking segment and receives Gemma analysis."""
    test_img_bytes = make_sharp_test_image()

    res = client.post(
        "/api/upload-and-analyze?segment_id=CUSTOM_SEG_1",
        files={"image": ("my_street_photo.jpg", test_img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["segment_id"] == "CUSTOM_SEG_1"
    assert "sidewalk" in data
    assert "curb_ramps" in data
    assert "surface_damage" in data
    assert 0.0 <= data["calculated_accessibility_score"] <= 100.0

