"""Unit tests for the deterministic evidence gate."""

import pytest
from backend.evidence_gate import evaluate_evidence
from backend.schemas import (
    AssessmentStatus,
    ImageQualityResult,
    ModelObservations,
    VisibleBarrier,
)


@pytest.fixture
def passing_quality() -> ImageQualityResult:
    return ImageQualityResult(
        passed=True,
        laplacian_variance=250.0,
        mean_brightness=120.0,
        issues=[],
    )


@pytest.fixture
def failing_quality() -> ImageQualityResult:
    return ImageQualityResult(
        passed=False,
        laplacian_variance=25.0,
        mean_brightness=120.0,
        issues=["Image is too blurry."],
    )


def test_failed_image_quality_returns_inconclusive(failing_quality):
    """Failed image quality check must yield INCONCLUSIVE without considering model output."""
    obs = ModelObservations(
        visible_barriers=[
            VisibleBarrier(
                type="stairs",
                description="Steps without ramp",
                location="entrance",
                visibility="clear",
            )
        ]
    )
    status, reason, limitations = evaluate_evidence(failing_quality, observations=obs)

    assert status == AssessmentStatus.INCONCLUSIVE
    assert "quality is insufficient" in reason.lower()
    assert len(limitations) > 0


def test_model_error_returns_inconclusive(passing_quality):
    """API error or timeout must yield INCONCLUSIVE."""
    status, reason, limitations = evaluate_evidence(
        passing_quality,
        observations=None,
        error_message="Connection timed out after 10s",
    )

    assert status == AssessmentStatus.INCONCLUSIVE
    assert "automated visual analysis failed" in reason.lower()
    assert "timed out" in reason.lower()


def test_none_observations_returns_inconclusive(passing_quality):
    """Missing observations yields INCONCLUSIVE."""
    status, reason, _ = evaluate_evidence(passing_quality, observations=None)
    assert status == AssessmentStatus.INCONCLUSIVE


def test_clear_barrier_returns_barrier(passing_quality):
    """Clearly visible barrier produces BARRIER verdict."""
    obs = ModelObservations(
        visible_barriers=[
            VisibleBarrier(
                type="obstruction",
                description="Vehicle parked across sidewalk",
                location="center sidewalk",
                visibility="clear",
            )
        ],
        visible_features=[],
        uncertain_observations=[],
    )
    status, reason, limitations = evaluate_evidence(passing_quality, observations=obs)

    assert status == AssessmentStatus.BARRIER
    assert "barrier" in reason.lower()
    assert "obstruction" in reason.lower()
    assert len(limitations) > 0


def test_no_barriers_returns_no_barrier_observed(passing_quality):
    """Usable image with no reported barrier returns NO_BARRIER_OBSERVED."""
    obs = ModelObservations(
        visible_barriers=[],
        visible_features=["curb_ramp", "wide_sidewalk"],
        uncertain_observations=[],
    )
    status, reason, limitations = evaluate_evidence(passing_quality, observations=obs)

    assert status == AssessmentStatus.NO_BARRIER_OBSERVED
    assert "no pedestrian barriers were observed" in reason.lower()
    assert "curb_ramp" in reason.lower()
    assert len(limitations) > 0


def test_uncertain_barrier_returns_inconclusive(passing_quality):
    """Barrier marked with uncertain visibility forces INCONCLUSIVE."""
    obs = ModelObservations(
        visible_barriers=[
            VisibleBarrier(
                type="broken_pavement",
                description="Possible crack or uneven surface",
                location="far ahead",
                visibility="uncertain",
            )
        ],
        visible_features=[],
        uncertain_observations=[],
    )
    status, reason, _ = evaluate_evidence(passing_quality, observations=obs)

    assert status == AssessmentStatus.INCONCLUSIVE
    assert "uncertain" in reason.lower()


def test_relevant_ambiguity_returns_inconclusive(passing_quality):
    """Ambiguity about pedestrian path elements forces INCONCLUSIVE."""
    obs = ModelObservations(
        visible_barriers=[],
        visible_features=[],
        uncertain_observations=[
            "Heavy shadows obscure whether the curb edge has a level drop-off or ramp."
        ],
    )
    status, reason, _ = evaluate_evidence(passing_quality, observations=obs)

    assert status == AssessmentStatus.INCONCLUSIVE
    assert "ambiguous" in reason.lower()


def test_irrelevant_ambiguity_does_not_force_inconclusive(passing_quality):
    """Ambiguity unrelated to pedestrian barriers does not force abstention."""
    obs = ModelObservations(
        visible_barriers=[],
        visible_features=["tactile_paving"],
        uncertain_observations=[
            "Building signage text is unreadable due to distance."
        ],
    )
    status, reason, _ = evaluate_evidence(passing_quality, observations=obs)

    assert status == AssessmentStatus.NO_BARRIER_OBSERVED


def test_limitations_always_present_and_custom_appended(passing_quality):
    """Standard limitations plus model limitations are merged."""
    obs = ModelObservations(
        visible_barriers=[],
        visible_features=[],
        uncertain_observations=[],
        limitations=["Nighttime street lighting limits depth perception."],
    )
    _, _, limitations = evaluate_evidence(passing_quality, observations=obs)

    assert any("strictly on a single 2D" in lim for lim in limitations)
    assert any("Nighttime street lighting" in lim for lim in limitations)
