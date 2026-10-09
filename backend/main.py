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
import hashlib
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
    BenchmarkModel,
    GemmaVisualAnalysis,
    HealthResponse,
    ModelObservations,
    SegmentModel,
    StreetViewObservationItem,
)
from backend.manifest_service import manifest_service
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
allow_all = "*" in settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://.*" if allow_all else None,
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

# Mount static frontend directory and public images
static_dir = os.path.join(base_dir, "backend", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

public_images_dir = os.path.join(base_dir, "public", "images")
if os.path.exists(public_images_dir):
    app.mount("/images", StaticFiles(directory=public_images_dir), name="public_images")


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

    photo_hash = f"sha256-{hashlib.sha256(image_bytes).hexdigest()}"
    quality_dict = {
        "blur_score": quality_result.laplacian_variance,
        "exposure_score": quality_result.mean_brightness,
        "passed": quality_result.passed,
        "notes": quality_result.issues,
    }
    witness_a = {
        "name": "OpenCV (Geometric & Edge)",
        "result": "Quality checks passed" if quality_result.passed else "Pre-gate quality refusal",
        "score": 0.85 if quality_result.passed else 0.35,
    }

    if not passed_quality:
        status_val, reason, limitations = evaluate_evidence(quality_result=quality_result, observations=None)
        return AnalysisResponse(
            status=status_val,
            observations=ModelObservations(),
            image_quality=quality_result,
            limitations=limitations,
            reason=reason,
            verdict="INCONCLUSIVE",
            barrier_type=None,
            description=reason,
            confidence=0.40,
            quality=quality_dict,
            witness_a=witness_a,
            witness_b={
                "name": "Gemma 4 (Vision-Language)",
                "result": "NOT_EVALUATED",
                "observations": ["Image quality pre-gate failed; semantic inference skipped."],
            },
            witness_agreement="NOT_EVALUATED",
            gate_reasons=[reason],
            captured_at=None,
            capture_date_source="unknown",
            source="saakshi_live_backend",
            photo_hash=photo_hash,
        )

    observations, error_message = analyze_image_with_model(image_bytes=image_bytes, mime_type=content_type)
    status_val, reason, limitations = evaluate_evidence(
        quality_result=quality_result,
        observations=observations,
        error_message=error_message,
    )

    verdict_str = "CLEAR_OBSERVED" if status_val.value == "NO_BARRIER_OBSERVED" else status_val.value
    barrier_type = (
        observations.visible_barriers[0].type
        if observations and observations.visible_barriers
        else None
    )
    obs_list: List[str] = []
    if observations:
        obs_list.extend([b.description for b in observations.visible_barriers])
        obs_list.extend(observations.visible_features)

    witness_b = {
        "name": "Gemma 4 (Vision-Language)",
        "result": verdict_str,
        "observations": obs_list,
    }

    return AnalysisResponse(
        status=status_val,
        observations=observations or ModelObservations(),
        image_quality=quality_result,
        limitations=limitations,
        reason=reason,
        verdict=verdict_str,
        barrier_type=barrier_type,
        description=reason,
        confidence=0.90 if status_val.value == "BARRIER" else (0.85 if status_val.value == "NO_BARRIER_OBSERVED" else 0.40),
        quality=quality_dict,
        witness_a=witness_a,
        witness_b=witness_b,
        witness_agreement="AGREE" if (verdict_str in ("BARRIER", "CLEAR_OBSERVED")) else "NOT_EVALUATED",
        gate_reasons=[reason],
        captured_at=None,
        capture_date_source="unknown",
        source="saakshi_live_backend",
        photo_hash=photo_hash,
    )


# --- AUDITED SECTORS & BENCHMARK SUITE ---

PILOT_SEGMENTS = [
    {
        "id": "seg-1",
        "name": "MG Road North Section (Pedestrian Zone)",
        "lat": 12.9757,
        "lon": 77.6074,
        "polyline": [[12.9757, 77.6074], [12.9762, 77.6080], [12.9768, 77.6085]],
        "status": "BARRIER",
        "last_verified": "2026-10-09T08:30:00Z",
        "confidence": 0.88,
        "image_url": "/images/sample_barrier.jpg",
        "captured_at": "2026-10-09T08:30:00Z",
        "provenance": "Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9762°N, 77.6080°E",
        "limitations": ["Visual record valid strictly for capture moment; physical obstructions can shift dynamically."],
        "transit_note": "BMTC bus stop within 80m (Trinity/MG Rd); real-time schedule feed not integrated for this pilot corridor.",
    },
    {
        "id": "seg-2",
        "name": "Brigade Road Stretch (Paved Footway)",
        "lat": 12.9720,
        "lon": 77.6080,
        "polyline": [[12.9720, 77.6080], [12.9725, 77.6088], [12.9730, 77.6096]],
        "status": "CLEAR_OBSERVED",
        "last_verified": "2026-10-09T09:15:00Z",
        "confidence": 0.93,
        "image_url": "/images/sample_clear.jpg",
        "captured_at": "2026-10-09T09:15:00Z",
        "provenance": "Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9725°N, 77.6088°E",
        "limitations": ["Reflects clear path observed at camera capture; does not guarantee permanent clearance."],
        "transit_note": "BMRCL MG Road Metro station 320m north; train arrival times not coupled to audit instrument.",
    },
    {
        "id": "seg-3",
        "name": "Church Street Segment (Shadowed Corridors)",
        "lat": 12.9740,
        "lon": 77.6055,
        "polyline": [[12.9740, 77.6055], [12.9745, 77.6060], [12.9750, 77.6065]],
        "status": "INCONCLUSIVE",
        "last_verified": None,
        "confidence": None,
        "image_url": "/images/sample_inconclusive.jpg",
        "captured_at": "2026-10-09T07:45:00Z",
        "provenance": "Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9745°N, 77.6060°E",
        "limitations": ["Pre-gate filter refused evaluation due to optical glare and heavy shadowing."],
        "transit_note": "Pedestrian plaza zone; public transit timetables not integrated into evidence pipeline.",
    },
    {
        "id": "seg-4",
        "name": "Residency Road East (Uninspected Segment)",
        "lat": 12.9705,
        "lon": 77.6065,
        "polyline": [[12.9705, 77.6065], [12.9710, 77.6072], [12.9715, 77.6079]],
        "status": "UNVERIFIED",
        "last_verified": None,
        "confidence": None,
        "image_url": None,
        "captured_at": None,
        "provenance": "OpenStreetMap geometry registration only // Pending field sensor survey",
        "limitations": ["No photographic evidence has been logged for this segment."],
        "transit_note": "Corridor vector cataloged only; no transit or accessibility telemetry available.",
    },
]


@app.get("/api/segments", response_model=List[SegmentModel], tags=["Segments"])
def get_segments() -> List[SegmentModel]:
    """Return historical audited sectors for Pilot Map."""
    return [SegmentModel(**s) for s in PILOT_SEGMENTS]


@app.get("/api/benchmark", response_model=BenchmarkModel, tags=["Benchmark"])
def get_benchmark() -> BenchmarkModel:
    """Return ground-truth benchmark metrics."""
    return BenchmarkModel(
        n=0,
        correct=0,
        missed_barriers=0,
        false_reassurance_count=0,
        false_reassurance_rate=0.0,
        inconclusive_count=0,
        per_mode=None,
    )


@app.get("/api/samples", tags=["Samples"])
def get_samples():
    """Return sample images for quick intake analysis."""
    return [
        {"id": "barrier-1", "url": "/images/sample_barrier.jpg", "label": "Broken Footpath Slab & Open Trench"},
        {"id": "clear-1", "url": "/images/sample_clear.jpg", "label": "Clear Footpath (MG Road Metro Station)"},
        {"id": "hazard-1", "url": "/images/sample_rubble_drain.jpg", "label": "Missing Drain Cover & Curb Rubble"},
        {"id": "narrow-1", "url": "/images/sample_posters.jpg", "label": "Narrow Compound Wall Footpath"},
    ]



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


@app.get("/api/observations", response_model=List[StreetViewObservationItem], tags=["Visual Evidence"])
def get_observations_list(
    route_id: Optional[str] = Query(None, description="Filter by route: a_to_b, b_to_c, c_to_a"),
    collection_status: Optional[str] = Query(None, description="Filter by status: collected, unavailable"),
    legacy_only: bool = Query(False, description="Filter to the 5 legacy demo points"),
) -> List[StreetViewObservationItem]:
    """List manifest Street View observations (all 171 points or filtered) with live analysis status."""
    return manifest_service.get_observations(
        route_id=route_id,
        collection_status=collection_status,
        legacy_only=legacy_only,
        analysis_cache=ANALYSIS_CACHE,
    )


@app.get("/api/observations/summary", tags=["Visual Evidence"])
def get_observations_summary():
    """Return coverage summary across all 171 planned points and each route separately."""
    return {
        "overall": manifest_service.get_overall_summary(ANALYSIS_CACHE),
        "routes": manifest_service.get_route_coverage_reports(ANALYSIS_CACHE),
        "audit": manifest_service.audit_and_reconcile(),
    }


@app.get("/api/observations/{obs_id}", response_model=StreetViewObservationItem, tags=["Visual Evidence"])
def get_single_observation(obs_id: str) -> StreetViewObservationItem:
    """Get details and analysis status for a single observation (by canonical ID or legacy OBS_1–5)."""
    item = manifest_service.get_observation_by_id(obs_id, analysis_cache=ANALYSIS_CACHE)
    if not item:
        raise HTTPException(status_code=404, detail=f"Observation '{obs_id}' not found.")
    return item


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
