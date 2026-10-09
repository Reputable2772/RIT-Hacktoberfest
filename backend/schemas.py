"""Pydantic schemas for request/response models and model observations."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AssessmentStatus(str, Enum):
    BARRIER = "BARRIER"
    NO_BARRIER_OBSERVED = "NO_BARRIER_OBSERVED"
    INCONCLUSIVE = "INCONCLUSIVE"


class BarrierVisibility(str, Enum):
    CLEAR = "clear"
    PARTIAL = "partial"
    UNCERTAIN = "uncertain"


class FeatureStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class ConfidenceRating(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VisibleBarrier(BaseModel):
    type: str = Field(
        ...,
        description="Type of barrier (e.g., obstruction, curb, stairs, broken_pavement, debris, narrow_path)",
    )
    description: str = Field(..., description="Brief factual description of the visible barrier")
    location: str = Field(..., description="Location in image (e.g., left sidewalk, path center, ahead)")
    visibility: str = Field(
        default="clear",
        description="Visibility confidence: 'clear', 'partial', or 'uncertain'",
    )


class ModelObservations(BaseModel):
    visible_barriers: List[VisibleBarrier] = Field(
        default_factory=list,
        description="List of detected physical barriers obstructing pedestrian travel",
    )
    visible_features: List[str] = Field(
        default_factory=list,
        description="List of visible accessibility features (e.g. curb ramp, tactile paving, flat sidewalk)",
    )
    uncertain_observations: List[str] = Field(
        default_factory=list,
        description="Observations that could not be confirmed due to distance, occlusion, or lighting",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Model-identified visual limitations specific to this image",
    )


class ImageQualityResult(BaseModel):
    passed: bool = Field(..., description="True if image meets minimum quality criteria for analysis")
    laplacian_variance: float = Field(..., description="Heuristic blur metric (higher is sharper)")
    mean_brightness: float = Field(..., description="Heuristic brightness metric (0-255)")
    issues: List[str] = Field(default_factory=list, description="List of detected quality issues")


class AnalysisResponse(BaseModel):
    status: AssessmentStatus = Field(
        ...,
        description="Final deterministic status: BARRIER, NO_BARRIER_OBSERVED, or INCONCLUSIVE",
    )
    observations: ModelObservations = Field(
        ...,
        description="Structured observations extracted from visual evidence",
    )
    image_quality: ImageQualityResult = Field(
        ...,
        description="OpenCV image readability, blur, and exposure results",
    )
    limitations: List[str] = Field(
        ...,
        description="Explicit caveats and physical limitations of this single-image assessment",
    )
    reason: str = Field(
        ...,
        description="Explanation of the deterministic evidence gate verdict",
    )
    # UI and Dual-Witness compatibility fields
    verdict: Optional[str] = None
    barrier_type: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    quality: Optional[Dict] = None
    witness_a: Optional[Dict] = None
    witness_b: Optional[Dict] = None
    witness_agreement: Optional[str] = None
    gate_reasons: Optional[List[str]] = None
    captured_at: Optional[str] = None
    capture_date_source: Optional[str] = None
    source: Optional[str] = None
    photo_hash: Optional[str] = None


class SegmentModel(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    polyline: List[List[float]]
    status: str
    last_verified: Optional[str] = None
    confidence: Optional[float] = None
    image_url: Optional[str] = None
    captured_at: Optional[str] = None
    provenance: Optional[str] = None
    limitations: Optional[List[str]] = None
    transit_note: Optional[str] = None


class BenchmarkPerModeModel(BaseModel):
    correct: int = 0
    missed_barriers: int = 0
    inconclusive_count: int = 0
    false_reassurance_count: int = 0
    false_reassurance_rate: float = 0.0


class BenchmarkPerModesModel(BaseModel):
    classical: BenchmarkPerModeModel
    gemma: BenchmarkPerModeModel
    combined: BenchmarkPerModeModel


class BenchmarkModel(BaseModel):
    n: int = 0
    correct: int = 0
    missed_barriers: int = 0
    false_reassurance_count: int = 0
    false_reassurance_rate: float = 0.0
    inconclusive_count: int = 0
    per_mode: Optional[BenchmarkPerModesModel] = None



class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "saakshi"
    version: str = "1.0.0"
    configured_model: str


# --- MULTIMODAL GEMMA STRUCTURED PEDESTRIAN ACCESSIBILITY CRITERIA ---

class AccessibilityCriterionFinding(BaseModel):
    criterion: str = Field(..., description="Key identifier (sidewalk, curb_ramps, etc.)")
    label: str = Field(..., description="Human-readable title")
    status: FeatureStatus = Field(..., description="present, absent, or unknown")
    confidence: ConfidenceRating = Field(..., description="high, medium, or low")
    explanation: str = Field(..., description="Factual visual evidence from image")


class GemmaVisualAnalysis(BaseModel):
    image_id: str = Field(..., description="Unique image identifier")
    location_id: Optional[str] = None
    segment_id: Optional[str] = None
    status: str = Field("completed", description="Analysis status: completed, image_unavailable, runtime_unavailable, unassessed")
    inference_source: str = Field("unavailable", description="live_local_gemma, live_gemma_api, offline_demo, or unavailable")
    model_used: str = Field(..., description="Identifier of the multimodal model executed")
    evidence_status: Optional[str] = Field(None, description="High-level verdict: BARRIER, NO_BARRIER_OBSERVED, or INCONCLUSIVE")
    sidewalk: AccessibilityCriterionFinding
    curb_ramps: AccessibilityCriterionFinding
    tactile_paving: AccessibilityCriterionFinding
    pedestrian_crossings: AccessibilityCriterionFinding
    obstructions: AccessibilityCriterionFinding
    surface_damage: AccessibilityCriterionFinding
    calculated_accessibility_score: float = Field(..., description="Composite 0-100 score")
    summary: str = Field(..., description="Overall pedestrian verdict")
    limitations: List[str] = Field(default_factory=list)


# --- STREET VIEW MANIFEST OBSERVATION SCHEMAS ---

class ObservationCoverageSummary(BaseModel):
    total_planned: int = 0
    collected: int = 0
    unavailable: int = 0
    analyzed: int = 0


class StreetViewObservationItem(BaseModel):
    id: str
    route_id: str
    direction: str
    sequence_number: int
    image_sequence_number: Optional[int] = None
    name: str
    location: str
    lat: float
    lon: float
    heading: float
    distance_along_route_m: float
    nearest_feature: str
    imagery_date: Optional[str] = None
    image_filename: Optional[str] = None
    image_url: Optional[str] = None
    image_available: bool = False
    collection_status: str  # "collected" or "unavailable"
    unavailable_reason: Optional[str] = None
    status: str  # "analysis_completed", "ready_for_analysis", "uncollected_gap"
    analysis: Optional[GemmaVisualAnalysis] = None
    is_usable_evidence: bool = True
    usability_issue: Optional[str] = None


class RouteCoverageReport(BaseModel):
    route_id: str
    direction: str
    name: str
    distance_meters: float
    target_spacing_meters: float
    total_planned: int
    collected_count: int
    unavailable_count: int
    analyzed_count: int = 0
    usable_evidence_count: int
    image_directory: str

