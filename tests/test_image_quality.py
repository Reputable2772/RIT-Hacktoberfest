"""Unit tests for OpenCV image-quality checks."""

import cv2
import numpy as np
import pytest
from backend.image_quality import assess_image_quality, decode_image


def create_encoded_image(array: np.ndarray, ext: str = ".jpg") -> bytes:
    """Encode numpy image array into bytes."""
    success, buffer = cv2.imencode(ext, array)
    assert success, "Image encoding failed in test setup"
    return buffer.tobytes()


def test_decode_image_valid():
    """Valid image bytes decode to a numpy ndarray."""
    img_data = np.zeros((100, 100, 3), dtype=np.uint8)
    encoded = create_encoded_image(img_data)
    decoded = decode_image(encoded)
    assert decoded is not None
    assert decoded.shape == (100, 100, 3)


def test_decode_image_invalid_bytes():
    """Corrupted bytes return None."""
    decoded = decode_image(b"this is not an image")
    assert decoded is None


def test_decode_empty_bytes():
    """Empty bytes return None."""
    assert decode_image(b"") is None


def test_sharp_balanced_image_passes():
    """Sharp, well-exposed image passes quality gate."""
    # High contrast checkerboard pattern
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(0, 200, 20):
        for j in range(0, 200, 20):
            if (i // 20 + j // 20) % 2 == 0:
                img[i : i + 20, j : j + 20] = 200
            else:
                img[i : i + 20, j : j + 20] = 50

    encoded = create_encoded_image(img)
    passed, result, decoded = assess_image_quality(encoded)

    assert passed is True
    assert result.passed is True
    assert result.laplacian_variance > 100.0
    assert 35.0 <= result.mean_brightness <= 220.0
    assert len(result.issues) == 0
    assert decoded is not None


def test_blurry_image_fails():
    """Heavy blur triggers blur failure in quality gate."""
    # Start with subtle gradient and apply heavy Gaussian blur
    base = np.linspace(100, 150, 200, dtype=np.uint8)
    img = np.tile(base, (200, 1))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    blurry = cv2.GaussianBlur(img, (25, 25), 0)

    encoded = create_encoded_image(blurry)
    passed, result, decoded = assess_image_quality(encoded, blur_threshold=100.0)

    assert passed is False
    assert result.passed is False
    assert result.laplacian_variance < 100.0
    assert any("blurry" in issue.lower() for issue in result.issues)


def test_underexposed_image_fails():
    """Severely dark image triggers underexposure issue."""
    dark_img = np.full((100, 100, 3), 15, dtype=np.uint8)
    encoded = create_encoded_image(dark_img)

    passed, result, _ = assess_image_quality(encoded, dark_threshold=35.0)

    assert passed is False
    assert result.passed is False
    assert result.mean_brightness < 35.0
    assert any("underexposed" in issue.lower() for issue in result.issues)


def test_overexposed_image_fails():
    """Severely bright image triggers overexposure issue."""
    bright_img = np.full((100, 100, 3), 245, dtype=np.uint8)
    encoded = create_encoded_image(bright_img)

    passed, result, _ = assess_image_quality(encoded, bright_threshold=220.0)

    assert passed is False
    assert result.passed is False
    assert result.mean_brightness > 220.0
    assert any("overexposed" in issue.lower() for issue in result.issues)


def test_unparseable_image_fails_gate():
    """Random unparseable data returns failed ImageQualityResult."""
    passed, result, decoded = assess_image_quality(b"\x00\x01\x02\x03BADIMAGE")

    assert passed is False
    assert result.passed is False
    assert decoded is None
    assert any("could not be decoded" in issue.lower() for issue in result.issues)
