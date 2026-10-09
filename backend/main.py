"""Main FastAPI application for Saakshi Multimodal Accessibility Planner.

Endpoints:
- GET  /health                      : Simple health status and configured model
- POST /api/analyze                 : Single street-view image upload quality & barrier assessment
- GET  /api/locations               : Mode A: Fixed demo locations (MG Road, Cubbon Park, Majestic)
- GET  /api/journeys                : Mode A: Journey alternatives for A->B, B->C, C->A
- GET  /api/observations            : Mode A: Prepared Street View evidence points
- POST /api/analyze-observation/{id}: Trigger real Gemma multimodal inference on prepared image
- POST /api/custom-journey          : Mode B: Plan multimodal route for arbitrary locations
- POST /api/upload-and-analyze      : Mode B: Upload custom pedestrian photo and run Gemma analysis
- GET  /                            : Single-page multimodal interactive web interface
"""

import os
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import settings
from backend.evidence_gate import evaluate_evidence
from backend.gemma import (
    analyze_image_with_model,
    analyze_pedestrian_image_multimodal,
    create_unavailable_analysis,
)
from backend.image_quality import assess_image_quality
from backend.locations import FIXED_LOCATIONS, DemoLocation, get_all_locations
from backend.planner import (
    ANALYSIS_CACHE,
    PREPARED_IMAGES_MAP,
    get_evaluated_journeys,
    get_image_path,
    plan_custom_journey,
    rank_journey_options,
    run_gemma_analysis_on_prepared_image,
)
from backend.schemas import (
    AnalysisResponse,
    GemmaVisualAnalysis,
    HealthResponse,
    ModelObservations,
)
from backend.transit_data import (
    ALL_JOURNEY_OPTIONS,
    JourneyOption,
    get_all_journeys,
    get_journeys_for_direction,
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
    description="Multimodal Bengaluru Pedestrian Accessibility and Transit Planner",
    version="2.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Image endpoint resolving from both data/observations and data/street_view
@app.get("/api/images/{file_path:path}", tags=["Images"])
def get_image(file_path: str):
    full_path = get_image_path(file_path)
    if not full_path or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    media_type = "image/png" if full_path.endswith(".png") else "image/jpeg"
    return FileResponse(full_path, media_type=media_type)

# Mount static frontend directory
static_dir = os.path.join(base_dir, "backend", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# --- CORE HEALTH & SINGLE-IMAGE ANALYSIS (Task 1 contract preserved) ---

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Return application health without calling external model APIs."""
    return HealthResponse(
        status="ok",
        app="saakshi",
        version="2.0.0",
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
    """Analyze a single image upload using OpenCV quality checks and Gemma."""
    content_type = image.content_type or ""
    if content_type.lower() not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Supported formats: {', '.join(sorted(SUPPORTED_MIME_TYPES))}",
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    image_bytes = await image.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image file is empty.")

    if len(image_bytes) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Image size exceeds maximum limit of {settings.MAX_UPLOAD_MB} MB.")

    passed_quality, quality_result, _ = assess_image_quality(image_bytes)

    if not passed_quality:
        status_val, reason, limitations = evaluate_evidence(quality_result=quality_result, observations=None)
        return AnalysisResponse(
            status=status_val,
            observations=ModelObservations(),
            image_quality=quality_result,
            limitations=limitations,
            reason=reason,
        )

    observations, error_message = analyze_image_with_model(image_bytes=image_bytes, mime_type=content_type)
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


# --- MULTIMODAL ROUTING & GEMMA INTEGRATION (Task 2) ---

@app.get("/api/locations", response_model=List[DemoLocation], tags=["Planner"])
def get_locations() -> List[DemoLocation]:
    """Mode A: Return canonical demo locations (A: MG Road, B: Cubbon Park, C: Majestic)."""
    return get_all_locations()


@app.get("/api/journeys", response_model=Dict[str, List[JourneyOption]], tags=["Planner"])
def get_journeys(
    sort: str = Query("fastest", description="Ranking criterion: fastest, least_walking, fewest_transfers, best_accessibility"),
) -> Dict[str, List[JourneyOption]]:
    """Mode A: Return evaluated journeys for A->B, B->C, and C->A with selectable dynamic ranking."""
    return get_evaluated_journeys(sort_criterion=sort)


@app.get("/api/observations", tags=["Visual Evidence"])
def get_observations_list():
    """Mode A: List prepared Street View observation points with current Gemma analysis status."""
    items = []
    for obs_id, meta in PREPARED_IMAGES_MAP.items():
        img_path = get_image_path(meta["filename"])
        file_exists = img_path is not None and os.path.exists(img_path)
        analyzed = obs_id in ANALYSIS_CACHE
        analysis_data = ANALYSIS_CACHE.get(obs_id)

        if analyzed:
            status_str = "analysis_completed"
        elif file_exists:
            status_str = "ready_for_analysis"
        else:
            status_str = "image_uncollected"

        items.append({
            "id": obs_id,
            "name": meta["name"],
            "location": meta["location"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "image_filename": meta["filename"],
            "image_url": f"/api/images/{meta['filename']}",
            "image_available": file_exists,
            "status": status_str,
            "analysis": analysis_data,
        })
    return items


@app.post("/api/analyze-observation/{obs_id}", response_model=GemmaVisualAnalysis, tags=["Visual Evidence"])
def analyze_prepared_observation(obs_id: str) -> GemmaVisualAnalysis:
    """Mode A: Run Gemma multimodal inference on prepared image or return honest unavailable status."""
    try:
        return run_gemma_analysis_on_prepared_image(obs_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error analyzing observation {obs_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class CustomJourneyRequest(BaseModel):
    origin_name: str
    origin_lat: float
    origin_lon: float
    dest_name: str
    dest_lat: float
    dest_lon: float
    sort: Optional[str] = "fastest"


@app.post("/api/custom-journey", response_model=List[JourneyOption], tags=["Planner"])
def custom_journey_planning(req: CustomJourneyRequest) -> List[JourneyOption]:
    """Mode B: Plan transit and walking options for arbitrary locations without automatic Street View."""
    options = plan_custom_journey(
        origin_name=req.origin_name,
        origin_lat=req.origin_lat,
        origin_lon=req.origin_lon,
        dest_name=req.dest_name,
        dest_lat=req.dest_lat,
        dest_lon=req.dest_lon,
    )
    return rank_journey_options(options, criterion=req.sort or "fastest")


@app.post("/api/upload-and-analyze", response_model=GemmaVisualAnalysis, tags=["Visual Evidence"])
async def upload_and_analyze_segment(
    segment_id: str = Query(..., description="Segment or walking connector ID"),
    image: UploadFile = File(..., description="User-supplied pedestrian photograph (JPEG, PNG, WebP)"),
) -> GemmaVisualAnalysis:
    """Mode B: Upload user-supplied pedestrian photograph and run real Gemma multimodal inference."""
    content_type = image.content_type or ""
    if content_type.lower() not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{content_type}'. Supported: {', '.join(sorted(SUPPORTED_MIME_TYPES))}",
        )

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is empty.")

    # OpenCV quality check
    passed, q_res, _ = assess_image_quality(image_bytes)
    if not passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image failed quality check: {'; '.join(q_res.issues)}",
        )

    # Execute Gemma multimodal analysis
    analysis, error_msg = analyze_pedestrian_image_multimodal(
        image_bytes=image_bytes,
        mime_type=content_type,
        image_id=f"USER_UPLOAD_{segment_id}",
        segment_id=segment_id,
    )

    if error_msg or analysis is None:
        analysis = create_unavailable_analysis(
            image_id=f"USER_UPLOAD_{segment_id}",
            segment_id=segment_id,
            reason=error_msg or "Inference runtime unavailable",
            status="runtime_unavailable",
        )

    # Cache result
    ANALYSIS_CACHE[segment_id] = analysis
    return analysis


# --- WEB INTERFACE (HTML + Leaflet + CSS) ---

@app.get("/", response_class=HTMLResponse, tags=["UI"])
def serve_ui():
    """Serve the interactive single-page application."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Saakshi Planner</h1><p>UI loading...</p>")
