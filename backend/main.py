"""Main FastAPI application for Saakshi Backend.

Endpoints:
- GET  /health      : Simple health status and configured model
- POST /api/analyze : Multi-part street-view image upload and accessibility barrier assessment
"""

import logging
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.evidence_gate import evaluate_evidence
from backend.gemma import analyze_image_with_model
from backend.image_quality import assess_image_quality
from backend.schemas import (
    AnalysisResponse,
    HealthResponse,
    ModelObservations,
)

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

app = FastAPI(
    title="Saakshi API",
    description="Evidence-based pedestrian accessibility image checker",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Return application health without calling external model APIs."""
    return HealthResponse(
        status="ok",
        app="saakshi",
        version="1.0.0",
        configured_model=settings.GEMINI_MODEL,
    )


@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def analyze_image(
    image: UploadFile = File(..., description="Street-view image file (JPEG, PNG, WebP, max 10MB)"),
) -> AnalysisResponse:
    """Analyze a single street-view image for pedestrian accessibility barriers.

    Workflow:
    1. Validate upload content type and size.
    2. Run OpenCV image-quality check (decoding, blur, underexposure, overexposure).
    3. If quality fails, return INCONCLUSIVE without calling the model.
    4. If quality passes, query the configured vision model and validate structured output.
    5. Pass observations and quality metrics through the deterministic evidence gate.
    """
    # 1. Validate MIME type
    content_type = image.content_type or ""
    if content_type.lower() not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_MIME_TYPES))}"
            ),
        )

    # 2. Read bytes with size validation
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    image_bytes = await image.read()

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds maximum limit of {settings.MAX_UPLOAD_MB} MB.",
        )

    # 3. OpenCV Image Quality Gate
    passed_quality, quality_result, _ = assess_image_quality(image_bytes)

    if not passed_quality:
        # Reject before making any model call
        status_val, reason, limitations = evaluate_evidence(
            quality_result=quality_result,
            observations=None,
        )
        return AnalysisResponse(
            status=status_val,
            observations=ModelObservations(),
            image_quality=quality_result,
            limitations=limitations,
            reason=reason,
        )

    # 4. Vision Model Inference
    observations, error_message = analyze_image_with_model(
        image_bytes=image_bytes,
        mime_type=content_type,
    )

    # 5. Deterministic Evidence Gate
    status_val, reason, limitations = evaluate_evidence(
        quality_result=quality_result,
        observations=observations,
        error_message=error_message,
    )

    return AnalysisResponse(
        status=status_val,
        observations=observations or ModelObservations(),
        image_quality=quality_result,
        limitations=limitations,
        reason=reason,
    )
