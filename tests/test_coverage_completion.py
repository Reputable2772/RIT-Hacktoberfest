"""Targeted tests to achieve 100% test coverage across all backend modules."""

import io
import json
import os
from unittest.mock import MagicMock, patch
import cv2
import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from google.genai.errors import APIError
from pydantic_core import ValidationError

from backend.main import app
from backend.config import settings
from backend.schemas import (
    AccessibilityCriterionFinding,
    ConfidenceRating,
    FeatureStatus,
    GemmaVisualAnalysis,
    ImageQualityResult,
    ModelObservations,
    VisibleBarrier,
)
from backend.accessibility_findings import (
    REPRESENTATIVE_OBSERVATIONS,
    get_all_observations,
)
from backend.transit_data import (
    get_journeys_for_direction,
)
from backend.image_quality import decode_image
from backend.locations import get_location, FIXED_LOCATIONS
from backend.gtfs_service import GTFSIndex, gtfs_index
from backend.gemma import (
    clean_json_response,
    get_genai_client,
    analyze_image_with_model,
    analyze_pedestrian_image_multimodal,
    _parse_gemma_criteria_response,
    create_unavailable_analysis,
)
from backend.planner import (
    get_image_path,
    evaluate_criteria_score,
    recalculate_journey_from_cache,
    run_gemma_analysis_on_prepared_image,
    _create_mock_verified_analysis,
    rank_journey_options,
    plan_custom_journey,
    ANALYSIS_CACHE,
    PREPARED_IMAGES_MAP,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_sharp_image_bytes() -> bytes:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = 255
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def make_blurry_image_bytes() -> bytes:
    base = np.linspace(100, 150, 100, dtype=np.uint8)
    img = np.tile(base, (100, 1))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    blurry = cv2.GaussianBlur(img, (25, 25), 0)
    _, buf = cv2.imencode(".jpg", blurry)
    return buf.tobytes()


# ==========================================
# 1. accessibility_findings.py Coverage (380)
# ==========================================
def test_get_all_observations():
    obs = get_all_observations()
    assert len(obs) == len(REPRESENTATIVE_OBSERVATIONS)
    assert all(o.id in REPRESENTATIVE_OBSERVATIONS for o in obs)


# ==========================================
# 2. transit_data.py Coverage (978-979)
# ==========================================
def test_get_journeys_for_direction():
    ab = get_journeys_for_direction("a", "b")
    assert len(ab) > 0
    assert ab[0].journey_key == "A->B"

    empty = get_journeys_for_direction("UNKNOWN", "DEST")
    assert empty == []


# ==========================================
# 3. image_quality.py Coverage (29-30)
# ==========================================
def test_decode_image_exception_handler():
    with patch("cv2.imdecode", side_effect=RuntimeError("imdecode failed")):
        result = decode_image(b"fake_image_bytes")
        assert result is None


# ==========================================
# 4. locations.py Coverage (74-77)
# ==========================================
def test_get_location_valid_and_invalid():
    loc_a = get_location("A")
    assert loc_a.key == "A"
    assert loc_a.name == FIXED_LOCATIONS["A"].name

    loc_b_space = get_location("  b  ")
    assert loc_b_space.key == "B"

    with pytest.raises(KeyError, match="Unknown demo location 'Z'"):
        get_location("Z")


# ==========================================
# 5. gtfs_service.py Coverage (79-80, 102-103, 109-110, 114-115, 123, 142-157)
# ==========================================
def test_gtfs_bmrcl_and_bmtc_exceptions():
    idx = GTFSIndex()
    with patch("os.path.exists", return_value=True), patch("zipfile.ZipFile", side_effect=Exception("Corrupt zip")):
        idx.load_if_needed()
        assert idx._loaded is True
        assert len(idx._bmrcl_stops) == 0
        assert len(idx._bmtc_stops) == 0


def test_gtfs_stops_counts_and_empty_lists():
    idx = GTFSIndex()
    idx._loaded = True
    idx._bmtc_stops = []
    idx._bmrcl_stops = []

    assert idx.bmtc_stops_count == 0
    assert idx.bmrcl_stops_count == 0
    assert idx.find_nearest_bmtc_stops(12.97, 77.59) == []
    assert idx.find_nearest_bmrcl_stations(12.97, 77.59) == []


def test_gtfs_find_nearest_bmrcl_stations():
    stations = gtfs_index.find_nearest_bmrcl_stations(12.975, 77.606, limit=2)
    assert len(stations) > 0
    assert stations[0].agency == "BMRCL"
    assert stations[0].distance_meters is not None
    assert gtfs_index.bmrcl_stops_count > 0
    assert gtfs_index.bmtc_stops_count > 0


# ==========================================
# 6. main.py Coverage (84-88, 133, 182-208, 216-220, 255, 262, 267, 298-302)
# ==========================================
def test_get_image_not_found(client):
    resp = client.get("/api/images/nonexistent_image_123.jpg")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Image file not found on disk"


def test_get_image_found(client, tmp_path):
    # Test valid image serving with both PNG and JPEG extensions
    sample_png = tmp_path / "test_sample.png"
    sample_png.write_bytes(b"\x89PNG\r\n\x1a\nfake_png")
    with patch("backend.main.get_image_path", return_value=str(sample_png)):
        resp = client.get("/api/images/test_sample.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    sample_jpg = tmp_path / "test_sample.jpg"
    sample_jpg.write_bytes(b"\xff\xd8\xfffake_jpg")
    with patch("backend.main.get_image_path", return_value=str(sample_jpg)):
        resp = client.get("/api/images/test_sample.jpg")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"


def test_analyze_file_size_exceeded(client):
    with patch.object(settings, "MAX_UPLOAD_MB", 0.0001):  # ~100 bytes
        resp = client.post(
            "/api/analyze",
            files={"image": ("big.jpg", b"x" * 2000, "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "exceeds maximum limit" in resp.json()["detail"]


def test_get_observations_list(client):
    # Test with cached analysis, ready for analysis, and uncollected states
    dummy = create_unavailable_analysis("OBS_1", status="completed")
    ANALYSIS_CACHE["OBS_1"] = dummy

    def mock_get_path(filename):
        if "0011" in filename:
            return None
        return "/fake/path/" + filename

    try:
        with patch("backend.main.get_image_path", side_effect=mock_get_path):
            with patch("os.path.exists", side_effect=lambda p: True if p and "fake" in p else False):
                resp = client.get("/api/observations")
                assert resp.status_code == 200
                items = resp.json()
                statuses = {item["id"]: item["status"] for item in items}
                assert statuses.get("OBS_1") == "analysis_completed"
                assert statuses.get("OBS_2") == "image_uncollected"
                assert "ready_for_analysis" in statuses.values()
    finally:
        ANALYSIS_CACHE.pop("OBS_1", None)


def test_analyze_prepared_observation_error_handling(client):
    # 400 on ValueError
    resp = client.post("/api/analyze-observation/NON_EXISTENT_OBS")
    assert resp.status_code == 400
    assert "Unknown prepared observation ID" in resp.json()["detail"]

    # 500 on unexpected Exception
    with patch("backend.main.run_gemma_analysis_on_prepared_image", side_effect=RuntimeError("Unexpected error")):
        resp500 = client.post("/api/analyze-observation/OBS_1")
        assert resp500.status_code == 500
        assert "Unexpected error" in resp500.json()["detail"]


def test_upload_and_analyze_validation_errors(client):
    # Unsupported content type
    resp1 = client.post(
        "/api/upload-and-analyze?segment_id=SEG_1",
        files={"image": ("doc.pdf", b"pdfcontent", "application/pdf")},
    )
    assert resp1.status_code == 400
    assert "Unsupported format" in resp1.json()["detail"]

    # Empty bytes
    resp2 = client.post(
        "/api/upload-and-analyze?segment_id=SEG_1",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp2.status_code == 400
    assert "Uploaded image is empty" in resp2.json()["detail"]

    # Blurry image
    blurry_bytes = make_blurry_image_bytes()
    resp3 = client.post(
        "/api/upload-and-analyze?segment_id=SEG_1",
        files={"image": ("blurry.jpg", blurry_bytes, "image/jpeg")},
    )
    assert resp3.status_code == 400
    assert "failed quality check" in resp3.json()["detail"].lower()


def test_serve_ui_existing_and_fallback(client):
    # Fallback when index.html does not exist
    with patch("os.path.exists", side_effect=lambda p: False if "index.html" in p else True):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Saakshi Planner" in resp.text
        assert "UI loading..." in resp.text

    # When index.html exists
    resp_normal = client.get("/")
    assert resp_normal.status_code == 200
    assert "<!DOCTYPE html>" in resp_normal.text or "<html" in resp_normal.text


# ==========================================
# 7. planner.py Coverage (141, 177-179, 195, 202-204, 232, 253, 312, 317-324, 332-339, 352-353, 368-402, 473, 476, 560-565, 576-581)
# ==========================================
def test_get_image_path_none():
    assert get_image_path("non_existent_image_foo_bar_xyz.jpg") is None


def test_evaluate_criteria_score_absent_features_and_moderate():
    finding = GemmaVisualAnalysis(
        image_id="TEST",
        status="completed",
        inference_source="test",
        model_used="test",
        evidence_status="BARRIER",
        sidewalk=AccessibilityCriterionFinding(
            criterion="sidewalk", label="Sidewalk", status=FeatureStatus.ABSENT,
            confidence=ConfidenceRating.HIGH, explanation="No sidewalk",
        ),
        curb_ramps=AccessibilityCriterionFinding(
            criterion="curb_ramps", label="Curb Ramps", status=FeatureStatus.PRESENT,
            confidence=ConfidenceRating.HIGH, explanation="Ramped",
        ),
        tactile_paving=AccessibilityCriterionFinding(
            criterion="tactile_paving", label="Tactile Paving", status=FeatureStatus.ABSENT,
            confidence=ConfidenceRating.HIGH, explanation="None",
        ),
        pedestrian_crossings=AccessibilityCriterionFinding(
            criterion="pedestrian_crossings", label="Crossings", status=FeatureStatus.ABSENT,
            confidence=ConfidenceRating.HIGH, explanation="Uncontrolled",
        ),
        obstructions=AccessibilityCriterionFinding(
            criterion="obstructions", label="Obstructions", status=FeatureStatus.ABSENT,
            confidence=ConfidenceRating.HIGH, explanation="Clear",
        ),
        surface_damage=AccessibilityCriterionFinding(
            criterion="surface_damage", label="Surface", status=FeatureStatus.ABSENT,
            confidence=ConfidenceRating.HIGH, explanation="Intact",
        ),
        calculated_accessibility_score=50.0,
        summary="Test",
        limitations=[],
    )
    score, concerns, verdict = evaluate_criteria_score(finding)
    # Score: base 50 - 25 (sw) + 15 (cr) + 0 (tp absent) - 10 (pc absent) + 15 (ob absent) + 10 (sd absent) = 55.0
    assert score == 55.0
    assert verdict == "Moderate Accessibility"
    assert any("No continuous sidewalk" in c for c in concerns)
    assert any("Uncontrolled crossing" in c for c in concerns)


def test_recalculate_journey_from_segment_cache():
    from backend.transit_data import get_journeys_for_direction
    journey = get_journeys_for_direction("A", "B")[0]
    seg_id = journey.segments[0].id
    analysis = create_unavailable_analysis(image_id="MOCK_IMG", segment_id=seg_id, status="completed")
    ANALYSIS_CACHE[seg_id] = analysis
    try:
        updated = recalculate_journey_from_cache(journey)
        assert updated is not None
    finally:
        ANALYSIS_CACHE.pop(seg_id, None)


def test_run_gemma_analysis_uncollected_image():
    ANALYSIS_CACHE.pop("OBS_1", None)
    with patch("backend.planner.get_image_path", return_value=None):
        res = run_gemma_analysis_on_prepared_image("OBS_1")
        assert res.status == "image_unavailable"
        assert "not yet been collected" in res.limitations[0]
    ANALYSIS_CACHE.pop("OBS_1", None)


def test_run_gemma_analysis_quality_failed():
    ANALYSIS_CACHE.pop("OBS_1", None)
    q_res = ImageQualityResult(
        passed=False,
        laplacian_variance=5.0,
        mean_brightness=50.0,
        issues=["Severely blurry"],
    )
    with patch("backend.planner.assess_image_quality", return_value=(False, q_res, None)):
        res = run_gemma_analysis_on_prepared_image("OBS_1")
        assert res.status == "quality_failed"
        assert "Severely blurry" in res.limitations[0]
    ANALYSIS_CACHE.pop("OBS_1", None)


def test_run_gemma_offline_demo_fallback_and_profiles():
    # Test all profiles in _create_mock_verified_analysis
    for obs_id in ["OBS_1", "OBS_2", "OBS_3", "OBS_4", "OBS_5", "UNKNOWN_OBS_99"]:
        meta = PREPARED_IMAGES_MAP.get(
            obs_id, {"location": "UNKNOWN_LOC", "name": "Unknown Observation"}
        )
        mock_ana = _create_mock_verified_analysis(obs_id, meta)
        assert mock_ana.inference_source == "offline_demo"

    # Test fallback branch when inference returns error and ALLOW_OFFLINE_DEMO_FALLBACK is True
    ANALYSIS_CACHE.pop("OBS_1", None)
    with patch.object(settings, "ALLOW_OFFLINE_DEMO_FALLBACK", True):
        with patch("backend.planner.analyze_pedestrian_image_multimodal", return_value=(None, "Model offline")):
            res = run_gemma_analysis_on_prepared_image("OBS_1")
            assert res.inference_source == "offline_demo"
    ANALYSIS_CACHE.pop("OBS_1", None)


def test_rank_journey_options_criteria():
    from backend.transit_data import get_journeys_for_direction
    opts = get_journeys_for_direction("A", "B")
    by_transfers = rank_journey_options(opts, criterion="fewest_transfers")
    assert len(by_transfers) == len(opts)
    by_unknown = rank_journey_options(opts, criterion="unrecognized_criterion")
    assert len(by_unknown) == len(opts)


def test_plan_custom_journey_fallback_stops():
    with patch("backend.gtfs_service.gtfs_index.find_nearest_bmtc_stops", return_value=[]):
        plans = plan_custom_journey(
            origin_name="Custom Origin",
            origin_lat=12.93,
            origin_lon=77.53,
            dest_name="Custom Dest",
            dest_lat=12.94,
            dest_lon=77.54,
        )
        assert len(plans) == 2
        bus_opt = next(p for p in plans if p.primary_mode == "bus")
        assert any("Estimated" in seg.from_name for seg in bus_opt.segments)
        assert any("Estimated" in seg.to_name for seg in bus_opt.segments)


# ==========================================
# 8. gemma.py Coverage (113-117, 125-129, 139-185, 247-283, 293-338, 350-370)
# ==========================================
def test_clean_json_response():
    plain = '{"status": "ok"}'
    assert clean_json_response(plain) == plain

    fenced_json = '```json\n{"status": "ok"}\n```'
    assert clean_json_response(fenced_json) == plain

    fenced_raw = '```\n{"status": "ok"}\n```'
    assert clean_json_response(fenced_raw) == plain


def test_get_genai_client_init_exception():
    with patch.object(settings, "GEMINI_API_KEY", "dummy_configured_key"):
        with patch("backend.gemma.genai.Client", side_effect=Exception("Initialization failed")):
            client = get_genai_client()
            assert client is None


def test_analyze_image_with_model_all_paths():
    img_bytes = make_sharp_image_bytes()

    # 0. Client is None branch
    with patch("backend.gemma.get_genai_client", return_value=None):
        obs_none, err_none = analyze_image_with_model(img_bytes, client=None)
        assert obs_none is None
        assert "Google API key not configured" in err_none

    # 1. Successful response
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "location": "MG Road",
        "primary_ground_surface": "concrete_pavers",
        "visible_barriers": [
            {
                "type": "curb",
                "description": "unramped curb",
                "location": "curb ramp area",
                "visibility": "clear",
            }
        ],
        "step_free_access": True,
        "tactile_paving": True,
        "curb_ramps_present": True,
        "sidewalk_present": True,
        "sidewalk_width_adequate": True,
        "surface_condition": "good",
        "estimated_crossing_distance_m": 8.0,
        "pedestrian_signals": True,
        "lighting_quality": "good",
        "observed_transit_infrastructure": ["metro_station_entrance"],
        "overall_pedestrian_score": 85.0,
        "summary": "High pedestrian accessibility",
        "limitations": [],
    })
    mock_client.models.generate_content.return_value = mock_resp
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert err is None
    assert obs is not None
    assert len(obs.visible_barriers) == 1
    assert obs.visible_barriers[0].type == "curb"

    # 2. Empty response text
    mock_resp.text = ""
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert obs is None
    assert "empty response" in err

    # 3. APIError
    mock_client.models.generate_content.side_effect = APIError(500, {"error": "API quota"})
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert obs is None
    assert "Model API error" in err

    # 4. JSONDecodeError
    mock_client.models.generate_content.side_effect = None
    mock_resp.text = "invalid json {"
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert obs is None
    assert "invalid JSON" in err

    # 5. ValidationError
    mock_resp.text = json.dumps({"visible_barriers": [{"type": "broken_path"}]})  # missing required fields
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert obs is None
    assert "validation error" in err

    # 6. Generic Exception
    mock_client.models.generate_content.side_effect = RuntimeError("Unknown failure")
    obs, err = analyze_image_with_model(img_bytes, client=mock_client)
    assert obs is None
    assert "Model inference error" in err


def test_analyze_pedestrian_image_multimodal_local_endpoint():
    img_bytes = make_sharp_image_bytes()
    criteria_data = {
        "sidewalk": {"status": "present", "confidence": "high", "explanation": "Wide"},
        "curb_ramps": {"status": "present", "confidence": "high", "explanation": "Ramped"},
        "tactile_paving": {"status": "present", "confidence": "high", "explanation": "Tactile"},
        "pedestrian_crossings": {"status": "present", "confidence": "high", "explanation": "Marked"},
        "obstructions": {"status": "absent", "confidence": "high", "explanation": "Clear"},
        "surface_damage": {"status": "absent", "confidence": "high", "explanation": "Smooth"},
        "calculated_accessibility_score": 92.0,
        "summary": "Excellent sidewalk",
        "limitations": [],
    }

    # 1. Local endpoint success
    mock_local_resp = MagicMock()
    mock_local_resp.status_code = 200
    mock_local_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(criteria_data)}}]
    }

    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", "http://localhost:8080"):
        with patch("httpx.Client.post", return_value=mock_local_resp):
            ana, err = analyze_pedestrian_image_multimodal(img_bytes, image_id="LOCAL_OK")
            assert err is None
            assert ana.inference_source == "live_local_gemma"
            assert ana.evidence_status == "NO_BARRIER_OBSERVED"

    # 2. Local endpoint exception falls through
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", "http://localhost:8080"):
        with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
            with patch("backend.gemma.get_genai_client", return_value=None):
                ana, err = analyze_pedestrian_image_multimodal(img_bytes, image_id="LOCAL_FAIL")
                assert ana is None
                assert "No live Gemma runtime or valid API key available" in err


def test_analyze_pedestrian_image_multimodal_genai_all_paths():
    img_bytes = make_sharp_image_bytes()
    criteria_barrier_data = {
        "sidewalk": {"status": "present", "confidence": "high", "explanation": "Wide"},
        "curb_ramps": {"status": "absent", "confidence": "high", "explanation": "Step barrier"},
        "tactile_paving": {"status": "absent", "confidence": "high", "explanation": "None"},
        "pedestrian_crossings": {"status": "unknown", "confidence": "low", "explanation": "Unknown"},
        "obstructions": {"status": "present", "confidence": "high", "explanation": "Parked cars"},
        "surface_damage": {"status": "absent", "confidence": "high", "explanation": "Smooth"},
        "calculated_accessibility_score": 45.0,
        "summary": "Obstructions present",
        "limitations": [],
    }

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(criteria_barrier_data)
    mock_client.models.generate_content.return_value = mock_resp

    # 1. Success with BARRIER status
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
        assert err is None
        assert ana.evidence_status == "BARRIER"
        assert ana.inference_source == "live_gemma_api"

    # 2. Empty response text
    mock_resp.text = ""
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
        assert ana is None
        assert "empty response" in err

    # 3. APIError
    mock_client.models.generate_content.side_effect = APIError(500, {"error": "API error"})
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
        assert ana is None
        assert "Model API error" in err

    # 4. JSONDecodeError
    mock_client.models.generate_content.side_effect = None
    mock_resp.text = "invalid json ["
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
        assert ana is None
        assert "invalid JSON" in err

    # 5. ValidationError
    mock_resp.text = json.dumps(criteria_barrier_data)
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        with patch("backend.gemma._parse_gemma_criteria_response", side_effect=ValidationError.from_exception_data("Validation failed", [])):
            ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
            assert ana is None
            assert "validation error" in err

    # 6. Generic Exception
    mock_client.models.generate_content.side_effect = RuntimeError("SDK crashed")
    with patch.object(settings, "GEMMA_LOCAL_ENDPOINT", ""):
        ana, err = analyze_pedestrian_image_multimodal(img_bytes, client=mock_client)
        assert ana is None
        assert "Model inference error" in err


def test_parse_gemma_criteria_response_inconclusive():
    data = {
        "sidewalk": {"status": "unknown"},
        "curb_ramps": {"status": "unknown"},
        "tactile_paving": {"status": "unknown"},
        "pedestrian_crossings": {"status": "unknown"},
        "obstructions": {"status": "unknown"},
        "surface_damage": {"status": "unknown"},
        "calculated_accessibility_score": 50.0,
        "summary": "Inconclusive assessment",
        "limitations": [],
    }
    parsed = _parse_gemma_criteria_response(
        data=data,
        image_id="TEST_INC",
        location_id="LOC_INC",
        segment_id="SEG_INC",
        model_used="model_test",
        inference_source="test_source",
    )
    assert parsed.evidence_status == "INCONCLUSIVE"


def test_get_image_path_security_checks():
    from backend.planner import get_image_path

    # Empty filename
    assert get_image_path("") is None
    assert get_image_path(None) is None

    # Invalid extension
    assert get_image_path("test.env") is None
    assert get_image_path("script.py") is None
    assert get_image_path("image.txt") is None

    # Path traversal attempts
    assert get_image_path("../secrets.png") is None
    assert get_image_path("data/../../etc/passwd.png") is None
    assert get_image_path("/etc/passwd.png") is None

