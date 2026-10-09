"""Deterministic evidence gate for accessibility assessment.

Applies strict, defensible, deterministic rules to convert model observations
and image quality results into a final status:
- BARRIER
- NO_BARRIER_OBSERVED
- INCONCLUSIVE

Principles:
1. No arbitrary numerical confidence thresholds.
2. The backend owns the verdict; the model provides raw observations.
3. Single-image assessment only; never claim a route is 'accessible' or 'safe'.
4. Uncertainty relevant to the barrier assessment forces abstention (INCONCLUSIVE).
"""

from typing import List, Optional, Tuple
from backend.schemas import (
    AssessmentStatus,
    BarrierVisibility,
    ImageQualityResult,
    ModelObservations,
)

STANDARD_LIMITATIONS = [
    "Assessment is based strictly on a single 2D street-view image.",
    "Result does not guarantee that the route, path, or entrance is safe or fully accessible.",
    "Physical cross-slopes, exact path widths, and continuous path clearance outside the camera frame cannot be measured.",
    "Transient obstacles (e.g. parked vehicles, temporary works) may change over time.",
]

BARRIER_AMBIGUITY_KEYWORDS = {
    "barrier",
    "obstruction",
    "curb",
    "step",
    "stairs",
    "ramp",
    "surface",
    "pavement",
    "path",
    "sidewalk",
    "walkway",
    "pedestrian",
    "drop-off",
    "blocked",
}


def evaluate_evidence(
    quality_result: ImageQualityResult,
    observations: Optional[ModelObservations] = None,
    error_message: Optional[str] = None,
) -> Tuple[AssessmentStatus, str, List[str]]:
    """Determine the final status based on deterministic evidence rules.

    Returns:
        Tuple of (status, reason, merged_limitations)
    """
    merged_limitations = list(STANDARD_LIMITATIONS)
    if observations and observations.limitations:
        for lim in observations.limitations:
            if lim not in merged_limitations:
                merged_limitations.append(lim)

    # Rule 1: Failed image quality check
    if not quality_result.passed:
        issue_summary = "; ".join(quality_result.issues) if quality_result.issues else "Image failed quality gate"
        return (
            AssessmentStatus.INCONCLUSIVE,
            f"Image quality is insufficient to support an accessibility assessment: {issue_summary}.",
            merged_limitations,
        )

    # Rule 2: Model error, timeout, or schema failure
    if error_message or observations is None:
        err_detail = error_message or "Model response was unavailable or invalid"
        return (
            AssessmentStatus.INCONCLUSIVE,
            f"Automated visual analysis failed: {err_detail}. No reliable verdict can be rendered.",
            merged_limitations,
        )

    # Rule 3: Check for material ambiguity relevant to barrier assessment
    # Check if any reported barrier is uncertain
    has_clear_barrier = any(
        b.visibility.lower() == BarrierVisibility.CLEAR.value
        for b in observations.visible_barriers
    )
    has_only_uncertain_barriers = (
        len(observations.visible_barriers) > 0
        and not has_clear_barrier
    )

    # Check if uncertain observations mention potential barriers/path elements
    relevant_uncertainties = [
        unc
        for unc in observations.uncertain_observations
        if any(kw in unc.lower() for kw in BARRIER_AMBIGUITY_KEYWORDS)
    ]

    if has_only_uncertain_barriers:
        return (
            AssessmentStatus.INCONCLUSIVE,
            "Potential barriers were noted, but visibility is uncertain or obstructed. The assessment is inconclusive.",
            merged_limitations,
        )

    # Rule 4: Clear visible barrier reported in usable image
    if has_clear_barrier:
        barriers_desc = ", ".join(
            f"{b.type} ({b.location})" for b in observations.visible_barriers if b.visibility.lower() == BarrierVisibility.CLEAR.value
        )
        return (
            AssessmentStatus.BARRIER,
            f"Clear physical accessibility barrier(s) detected in the pedestrian area: {barriers_desc}.",
            merged_limitations,
        )

    # Rule 5: If there are no clear barriers, but relevant uncertainties exist regarding path condition
    if relevant_uncertainties:
        uncertainty_desc = "; ".join(relevant_uncertainties)
        return (
            AssessmentStatus.INCONCLUSIVE,
            f"Visual evidence is ambiguous regarding potential path barriers: {uncertainty_desc}.",
            merged_limitations,
        )

    # Rule 6: No barrier reported in usable image
    features_desc = ""
    if observations.visible_features:
        features_desc = f" Observed visible accessibility features: {', '.join(observations.visible_features)}."

    return (
        AssessmentStatus.NO_BARRIER_OBSERVED,
        f"No pedestrian barriers were observed in the supplied image.{features_desc} Note that assessment is strictly limited to the visible camera perspective.",
        merged_limitations,
    )
