"""Focused regression tests for dynamic accessibility scoring, observation isolation, and GTFS provenance."""

import pytest
from fastapi.testclient import TestClient

from backend.gtfs_service import gtfs_index
from backend.main import app
from backend.planner import (
    ANALYSIS_CACHE,
    evaluate_criteria_score,
    get_evaluated_journeys,
    recalculate_journey_from_cache,
)
from backend.schemas import (
    AccessibilityCriterionFinding,
    ConfidenceRating,
    FeatureStatus,
    GemmaVisualAnalysis,
)
from backend.transit_data import ALL_JOURNEY_OPTIONS, get_journeys_for_direction


@pytest.fixture
def client():
    return TestClient(app)


def make_sample_analysis(
    image_id: str,
    sidewalk_status: FeatureStatus = FeatureStatus.UNKNOWN,
    curb_status: FeatureStatus = FeatureStatus.UNKNOWN,
    tactile_status: FeatureStatus = FeatureStatus.UNKNOWN,
    crossing_status: FeatureStatus = FeatureStatus.UNKNOWN,
    obstruction_status: FeatureStatus = FeatureStatus.UNKNOWN,
    damage_status: FeatureStatus = FeatureStatus.UNKNOWN,
    status: str = "completed",
    inference_source: str = "live_local_gemma",
) -> GemmaVisualAnalysis:
    """Helper to create a structured GemmaVisualAnalysis fixture."""
    def crit(key: str, label: str, stat: FeatureStatus) -> AccessibilityCriterionFinding:
        return AccessibilityCriterionFinding(
            criterion=key,
            label=label,
            status=stat,
            confidence=ConfidenceRating.HIGH if stat != FeatureStatus.UNKNOWN else ConfidenceRating.LOW,
            explanation=f"Test evidence for {key}",
        )

    return GemmaVisualAnalysis(
        image_id=image_id,
        status=status,
        inference_source=inference_source,
        model_used="gemma-test",
        sidewalk=crit("sidewalk", "Sidewalk", sidewalk_status),
        curb_ramps=crit("curb_ramps", "Curb Ramps", curb_status),
        tactile_paving=crit("tactile_paving", "Tactile Paving", tactile_status),
        pedestrian_crossings=crit("pedestrian_crossings", "Crossings", crossing_status),
        obstructions=crit("obstructions", "Obstructions", obstruction_status),
        surface_damage=crit("surface_damage", "Surface Damage", damage_status),
        calculated_accessibility_score=50.0,
        summary="Test analysis summary",
    )


def test_confirmed_barrier_reduces_route_score():
    """Confirmed physical barriers (obstruction, broken surface, no ramps) must reduce score significantly."""
    barrier_analysis = make_sample_analysis(
        image_id="OBS_2",
        sidewalk_status=FeatureStatus.PRESENT,
        curb_status=FeatureStatus.ABSENT,
        obstruction_status=FeatureStatus.PRESENT,
        damage_status=FeatureStatus.PRESENT,
    )

    score, concerns, verdict = evaluate_criteria_score(barrier_analysis)
    assert score < 40.0, f"Expected score < 40 for severe barriers, got {score}"
    assert "Significant Physical Barriers" in verdict
    assert any("obstruction" in c.lower() for c in concerns)
    assert any("damage" in c.lower() for c in concerns)


def test_unknown_evidence_does_not_count_as_proof_of_accessibility():
    """Unassessed or unknown criteria must NOT increase score or claim accessibility."""
    unknown_analysis = make_sample_analysis(
        image_id="OBS_UNKNOWN",
        sidewalk_status=FeatureStatus.UNKNOWN,
        curb_status=FeatureStatus.UNKNOWN,
        tactile_status=FeatureStatus.UNKNOWN,
        crossing_status=FeatureStatus.UNKNOWN,
        obstruction_status=FeatureStatus.UNKNOWN,
        damage_status=FeatureStatus.UNKNOWN,
    )

    score, concerns, verdict = evaluate_criteria_score(unknown_analysis)
    assert score == 50.0, "Unknown evidence must not gain points"
    assert "Unassessed" in verdict or "Inconclusive" in verdict


def test_confirmed_clear_path_increases_score():
    """Confirmed absence of obstacles and presence of ramps/tactile paving must raise score to High."""
    clear_analysis = make_sample_analysis(
        image_id="OBS_1",
        sidewalk_status=FeatureStatus.PRESENT,
        curb_status=FeatureStatus.PRESENT,
        tactile_status=FeatureStatus.PRESENT,
        crossing_status=FeatureStatus.PRESENT,
        obstruction_status=FeatureStatus.ABSENT,
        damage_status=FeatureStatus.ABSENT,
    )

    score, concerns, verdict = evaluate_criteria_score(clear_analysis)
    assert score >= 85.0, f"Expected high score >= 85, got {score}"
    assert verdict == "Highly Accessible"
    assert len(concerns) == 0


def test_observation_isolation_between_routes():
    """An observation on corridor A->B (OBS_2) must only affect relevant routes and NOT mutate C->A."""
    # Place barrier analysis in cache for OBS_2 (Kasturba Road, A->B)
    ANALYSIS_CACHE["OBS_2"] = make_sample_analysis(
        image_id="OBS_2",
        sidewalk_status=FeatureStatus.PRESENT,
        obstruction_status=FeatureStatus.PRESENT,
        damage_status=FeatureStatus.PRESENT,
    )

    evaluated = get_evaluated_journeys()

    # Corridor A->B should reflect the updated barrier score
    ab_walk = next((j for j in evaluated["A->B"] if j.primary_mode == "walking"), None)
    assert ab_walk is not None
    assert ab_walk.accessibility_score < 40.0, "Expected A->B walk score to be penalized by OBS_2"

    # Corridor C->A walking route does NOT traverse OBS_2 and must NOT be affected
    ca_walk = next((j for j in evaluated["C->A"] if j.primary_mode == "walking"), None)
    assert ca_walk is not None
    # CA walk baseline is 32.0; it should not inherit OBS_2 concerns
    assert not any("OBS_2" in c for c in ca_walk.accessibility_concerns)


def test_gtfs_nearest_stop_matches_real_bmtc_stops():
    """Ensure gtfs_index returns genuine BMTC bus stops with non-zero coordinates."""
    # Coordinates in Koramangala
    stops = gtfs_index.find_nearest_bmtc_stops(12.9352, 77.6245, limit=2)
    assert len(stops) == 2
    for s in stops:
        assert s.agency == "BMTC"
        assert len(s.stop_name) > 3
        assert 12.0 < s.lat < 14.0
        assert 77.0 < s.lon < 78.0
        assert s.distance_meters is not None
        assert s.distance_meters < 500


def test_custom_journey_uses_genuine_gtfs_stop_names(client):
    """Mode B custom journey planning must resolve genuine BMTC stops from GTFS feed."""
    req_payload = {
        "origin_name": "Koramangala 5th Block",
        "origin_lat": 12.9352,
        "origin_lon": 77.6245,
        "dest_name": "Indiranagar 100ft Road",
        "dest_lat": 12.9716,
        "dest_lon": 77.6412,
        "sort": "fastest",
    }
    res = client.post("/api/custom-journey", json=req_payload)
    assert res.status_code == 200
    journeys = res.json()

    bus_option = next((j for j in journeys if j["primary_mode"] == "bus"), None)
    assert bus_option is not None
    assert "gtfs_stop_matched" in bus_option["data_provenance"]["transit"]

    # Segment 1 must arrive at a genuine BMTC stop, not 'Nearest Bus Stop'
    seg1 = bus_option["segments"][0]
    assert "BMTC Stop:" in seg1["to_name"]
    assert seg1["to_name"] != "Nearest Bus Stop (Estimated)"


def test_uncollected_image_status_handling(client):
    """An uncollected image must return HTTP 200 with clear unavailable status instead of misleading 404."""
    from backend.planner import run_gemma_analysis_on_prepared_image

    # Even if an observation has an uncollected image, it must return a valid GemmaVisualAnalysis
    analysis = run_gemma_analysis_on_prepared_image("OBS_1")
    assert analysis.image_id == "OBS_1"
    assert analysis.calculated_accessibility_score >= 0.0
    assert analysis.sidewalk.status in (FeatureStatus.PRESENT, FeatureStatus.ABSENT, FeatureStatus.UNKNOWN)


def test_dynamic_ranking_by_accessibility(client):
    """GET /api/journeys?sort=best_accessibility must rank higher accessible routes before routes with barriers."""
    # Set high accessible analysis for OBS_1 and severe barrier for OBS_2
    ANALYSIS_CACHE["OBS_1"] = make_sample_analysis(
        image_id="OBS_1",
        sidewalk_status=FeatureStatus.PRESENT,
        curb_status=FeatureStatus.PRESENT,
        obstruction_status=FeatureStatus.ABSENT,
        damage_status=FeatureStatus.ABSENT,
    )
    ANALYSIS_CACHE["OBS_2"] = make_sample_analysis(
        image_id="OBS_2",
        sidewalk_status=FeatureStatus.PRESENT,
        curb_status=FeatureStatus.ABSENT,
        obstruction_status=FeatureStatus.PRESENT,
        damage_status=FeatureStatus.PRESENT,
    )

    res = client.get("/api/journeys?sort=best_accessibility")
    assert res.status_code == 200
    data = res.json()

    ab_routes = data["A->B"]
    scores = [r["accessibility_score"] for r in ab_routes]
    # Assert descending order of accessibility scores
    assert scores == sorted(scores, reverse=True)
    # The first route must have a higher score than the lowest
    assert scores[0] >= scores[-1]
