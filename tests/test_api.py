"""API and integration tests for FastAPI endpoints."""

from unittest.mock import MagicMock, patch
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import ModelObservations, VisibleBarrier


@pytest.fixture
def client():
    return TestClient(app)


def make_sharp_image_bytes() -> bytes:
    """Create a sharp, high-contrast image buffer."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(0, 200, 20):
        for j in range(0, 200, 20):
            if (i // 20 + j // 20) % 2 == 0:
                img[i : i + 20, j : j + 20] = 220
            else:
                img[i : i + 20, j : j + 20] = 40
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def make_blurry_image_bytes() -> bytes:
    """Create a heavily blurred image buffer."""
    base = np.linspace(100, 150, 200, dtype=np.uint8)
    img = np.tile(base, (200, 1))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    blurry = cv2.GaussianBlur(img, (25, 25), 0)
    _, buf = cv2.imencode(".jpg", blurry)
    return buf.tobytes()


def test_health_endpoint(client):
    """GET /health returns 200 and configured model without external calls."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "saakshi"
    assert "configured_model" in data


def test_analyze_unsupported_file_type(client):
    """POST /api/analyze with non-image file returns 400."""
    response = client.post(
        "/api/analyze",
        files={"image": ("test.txt", b"plain text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"].lower()


def test_analyze_empty_file(client):
    """POST /api/analyze with empty file returns 400."""
    response = client.post(
        "/api/analyze",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_analyze_poor_quality_skips_model(client):
    """Poor quality image returns INCONCLUSIVE and does NOT call model."""
    blurry_bytes = make_blurry_image_bytes()

    with patch("backend.main.analyze_image_with_model") as mock_model:
        response = client.post(
            "/api/analyze",
            files={"image": ("blurry.jpg", blurry_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "INCONCLUSIVE"
        assert data["image_quality"]["passed"] is False
        assert any("blurry" in issue.lower() for issue in data["image_quality"]["issues"])
        # Crucial check: model inference must NOT be called for poor quality images
        mock_model.assert_not_called()


def test_analyze_clear_barrier(client):
    """Usable image with clear visible barrier returns BARRIER."""
    sharp_bytes = make_sharp_image_bytes()
    mock_obs = ModelObservations(
        visible_barriers=[
            VisibleBarrier(
                type="stairs",
                description="Flight of 5 steps without adjacent ramp",
                location="curb entry",
                visibility="clear",
            )
        ],
        visible_features=[],
        uncertain_observations=[],
    )

    with patch("backend.main.analyze_image_with_model", return_value=(mock_obs, None)):
        response = client.post(
            "/api/analyze",
            files={"image": ("sharp.jpg", sharp_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "BARRIER"
        assert len(data["observations"]["visible_barriers"]) == 1
        assert data["observations"]["visible_barriers"][0]["type"] == "stairs"
        assert "stairs" in data["reason"].lower()


def test_analyze_no_barrier_observed(client):
    """Usable image with no barriers returns NO_BARRIER_OBSERVED."""
    sharp_bytes = make_sharp_image_bytes()
    mock_obs = ModelObservations(
        visible_barriers=[],
        visible_features=["curb_ramp", "tactile_paving"],
        uncertain_observations=[],
    )

    with patch("backend.main.analyze_image_with_model", return_value=(mock_obs, None)):
        response = client.post(
            "/api/analyze",
            files={"image": ("sharp.jpg", sharp_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "NO_BARRIER_OBSERVED"
        assert "no pedestrian barriers were observed" in data["reason"].lower()
        assert "curb_ramp" in data["observations"]["visible_features"]


def test_analyze_model_api_error_returns_inconclusive(client):
    """Model API error or timeout yields INCONCLUSIVE safely without 500 error."""
    sharp_bytes = make_sharp_image_bytes()

    with patch(
        "backend.main.analyze_image_with_model",
        return_value=(None, "Model API connection timed out"),
    ):
        response = client.post(
            "/api/analyze",
            files={"image": ("sharp.jpg", sharp_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "INCONCLUSIVE"
        assert "failed" in data["reason"].lower()
        assert "timed out" in data["reason"].lower()


def test_analyze_malformed_model_output(client):
    """Malformed model output yields INCONCLUSIVE safely."""
    sharp_bytes = make_sharp_image_bytes()

    with patch(
        "backend.main.analyze_image_with_model",
        return_value=(None, "Model returned invalid JSON: Expecting value"),
    ):
        response = client.post(
            "/api/analyze",
            files={"image": ("sharp.jpg", sharp_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "INCONCLUSIVE"
        assert "invalid json" in data["reason"].lower()


def test_analyze_ambiguous_evidence(client):
    """Ambiguous path evidence yields INCONCLUSIVE."""
    sharp_bytes = make_sharp_image_bytes()
    mock_obs = ModelObservations(
        visible_barriers=[],
        visible_features=[],
        uncertain_observations=["Overhanging branches or obstruction may block sidewalk"],
    )

    with patch("backend.main.analyze_image_with_model", return_value=(mock_obs, None)):
        response = client.post(
            "/api/analyze",
            files={"image": ("sharp.jpg", sharp_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "INCONCLUSIVE"
        assert "ambiguous" in data["reason"].lower()
