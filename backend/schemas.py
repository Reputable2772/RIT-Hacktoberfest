"""Pydantic schemas for request/response models and model observations."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AssessmentStatus(str, Enum):
    BARRIER = "BARRIER"
    NO_BARRIER_OBSERVED = "NO_BARRIER_OBSERVED"
    INCONCLUSIVE = "INCONCLUSIVE"


class BarrierVisibility(str, Enum):
    CLEAR = "clear"
    PARTIAL = "partial"
    UNCERTAIN = "uncertain"


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


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "saakshi"
    version: str = "1.0.0"
    configured_model: str
