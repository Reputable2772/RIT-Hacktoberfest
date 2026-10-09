"""Image quality checks using OpenCV.

Note:
These metrics (Laplacian variance for sharpness, mean grayscale intensity for exposure)
are heuristic indicators of image readability, NOT calibrated accessibility metrics.
They serve as a defensive quality gate before sending images to downstream inference.
"""

from typing import Optional, Tuple
import cv2
import numpy as np
from backend.config import settings
from backend.schemas import ImageQualityResult


def decode_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decode raw image bytes into an OpenCV BGR image array.
    
    Returns None if decoding fails or the image is empty.
    """
    if not image_bytes:
        return None
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            return None
        return img
    except Exception:
        return None


def assess_image_quality(
    image_bytes: bytes,
    blur_threshold: Optional[float] = None,
    dark_threshold: Optional[float] = None,
    bright_threshold: Optional[float] = None,
) -> Tuple[bool, ImageQualityResult, Optional[np.ndarray]]:
    """Assess whether an image is usable for accessibility barrier analysis.

    Checks:
    1. Successful decoding via OpenCV.
    2. Blur via Laplacian variance heuristic.
    3. Exposure via mean intensity heuristic (underexposure / overexposure).

    Returns:
        Tuple of (passed: bool, quality_result: ImageQualityResult, decoded_image: Optional[np.ndarray])
    """
    blur_th = blur_threshold if blur_threshold is not None else settings.BLUR_THRESHOLD
    dark_th = dark_threshold if dark_threshold is not None else settings.DARK_BRIGHTNESS_THRESHOLD
    bright_th = bright_threshold if bright_threshold is not None else settings.BRIGHT_BRIGHTNESS_THRESHOLD

    issues = []

    img = decode_image(image_bytes)
    if img is None:
        issues.append("Image could not be decoded. Unsupported format or corrupted file.")
        return False, ImageQualityResult(
            passed=False,
            laplacian_variance=0.0,
            mean_brightness=0.0,
            issues=issues,
        ), None

    # Convert to grayscale for metric evaluations
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Blur check via Laplacian variance
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if lap_var < blur_th:
        issues.append(
            f"Image is too blurry for reliable assessment (Laplacian variance: {lap_var:.1f} < {blur_th:.1f})."
        )

    # 2. Exposure check via mean brightness
    mean_bright = float(np.mean(gray))
    if mean_bright < dark_th:
        issues.append(
            f"Image is severely underexposed (mean brightness: {mean_bright:.1f} < {dark_th:.1f})."
        )
    elif mean_bright > bright_th:
        issues.append(
            f"Image is severely overexposed (mean brightness: {mean_bright:.1f} > {bright_th:.1f})."
        )

    passed = len(issues) == 0

    return passed, ImageQualityResult(
        passed=passed,
        laplacian_variance=round(lap_var, 2),
        mean_brightness=round(mean_bright, 2),
        issues=issues,
    ), img
