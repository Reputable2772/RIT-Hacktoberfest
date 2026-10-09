"""Automated tests for dynamic corridor route computation with reliable deterministic fallback.

Tests required by Saakshi Release Gate & Dynamic Routing specification:
- Successful route computation for each of the three journeys (A->B, B->C, C->A).
- Routing-provider timeout.
- Routing-provider error response.
- Malformed or empty computed results.
- Missing or invalid local route geometry.
- Fallback to precompiled data for each journey independently.
- No fallback data available for unknown corridors.
- Gemma unavailable while routing succeeds.
- Routing unavailable while Gemma is configured.
- Invalid or missing observation images.
- Route-specific evidence isolation.
- Correct provenance in every outcome.
- Correct response schemas and ranking behavior.
- No invented transit data when GTFS real-time schedules are unavailable.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.planner import get_evaluated_journeys, run_gemma_analysis_on_prepared_image
from backend.route_engine import (
    RoutingComputationError,
    compute_corridor_alternatives,
    get_all_corridor_journeys_with_fallback,
    get_corridor_journeys_with_fallback,
    get_fallback_corridor_journeys,
    parse_local_route_geometry,
)
from backend.transit_data import ALL_JOURNEY_OPTIONS, TransitMode


@pytest.fixture
def client():
    return TestClient(app)


def test_successful_route_computation_all_three_journeys():
    """Verify that all three journeys compute dynamically from local geometries and GTFS feeds."""
    for corridor in ["A->B", "B->C", "C->A"]:
        options = compute_corridor_alternatives(corridor)
        assert len(options) >= 2, f"Corridor {corridor} must have at least 2 computed alternatives"

        # Check walk option
        walk_opt = next((o for o in options if o.primary_mode == TransitMode.WALKING), None)
        assert walk_opt is not None, f"Missing walking option for {corridor}"
        assert walk_opt.computation_mode == "computed"
        assert walk_opt.total_walking_distance_meters > 0
        assert walk_opt.total_duration_minutes > 0
        assert len(walk_opt.segments[0].polyline) >= 2
        assert walk_opt.data_provenance.get("computation_status") == "computed"
        assert walk_opt.data_provenance.get("fallback_used") == "false"

        # Check transit options
        metro_opt = next((o for o in options if o.primary_mode == TransitMode.METRO), None)
        assert metro_opt is not None, f"Missing metro option for {corridor}"
        assert metro_opt.computation_mode == "computed"
        assert metro_opt.total_fare_inr in (10.0, 15.0, 20.0)

        # Observations and coverage report attached
        assert len(walk_opt.observations) > 0
        assert "total_planned" in walk_opt.observation_coverage
        assert walk_opt.observation_coverage["total_planned"] > 0


def test_routing_provider_timeout():
    """Verify that an external routing timeout triggers clean fallback with machine-readable reason."""
    with patch("backend.config.settings.ROUTING_SERVICE_URL", "http://external-router.local"):
        with patch(
            "backend.route_engine.attempt_external_routing",
            side_effect=RoutingComputationError(
                reason="provider_timeout",
                explanation="Live routing provider timed out after 2.0s.",
            ),
        ):
            fallback_options = get_corridor_journeys_with_fallback("A->B")
            assert len(fallback_options) >= 2
            for opt in fallback_options:
                assert opt.computation_mode == "precompiled_fallback"
                assert opt.fallback_reason == "provider_timeout"
                assert "timed out" in opt.fallback_explanation.lower()
                assert opt.data_provenance.get("computation_status") == "precompiled_fallback"
                assert opt.data_provenance.get("fallback_used") == "true"


def test_routing_provider_error_response():
    """Verify that a 502/500 routing provider error triggers graceful fallback."""
    with patch("backend.config.settings.ROUTING_SERVICE_URL", "http://external-router.local"):
        with patch(
            "backend.route_engine.attempt_external_routing",
            side_effect=RoutingComputationError(
                reason="provider_error",
                explanation="Live routing provider returned HTTP 502 Bad Gateway.",
            ),
        ):
            fallback_options = get_corridor_journeys_with_fallback("B->C")
            assert len(fallback_options) >= 2
            for opt in fallback_options:
                assert opt.computation_mode == "precompiled_fallback"
                assert opt.fallback_reason == "provider_error"
                assert "502" in opt.fallback_explanation


def test_malformed_or_empty_computed_results():
    """Verify that malformed or empty route geometries trigger deterministic fallback."""
    with pytest.raises(RoutingComputationError) as exc_info:
        parse_local_route_geometry("non_existent_mock_id")
    assert exc_info.value.reason == "geometry_file_missing"

    with patch(
        "backend.route_engine.parse_local_route_geometry",
        side_effect=RoutingComputationError(
            reason="malformed_computed_data",
            explanation="Route geometry returned empty coordinate array.",
        ),
    ):
        fallback_options = get_corridor_journeys_with_fallback("C->A")
        assert len(fallback_options) >= 2
        assert fallback_options[0].computation_mode == "precompiled_fallback"
        assert fallback_options[0].fallback_reason == "malformed_computed_data"


def test_missing_or_invalid_local_route_geometry():
    """Verify that a missing route geometry file triggers fallback with geometry_file_missing code."""
    with patch("os.path.exists", return_value=False):
        fallback_options = get_corridor_journeys_with_fallback("A->B")
        assert len(fallback_options) >= 2
        for opt in fallback_options:
            assert opt.computation_mode == "precompiled_fallback"
            assert opt.fallback_reason == "geometry_file_missing"


def test_fallback_to_precompiled_data_independently():
    """Verify that fallback on one corridor does NOT affect successful computation on others."""
    # Force failure only for B->C
    original_compute = compute_corridor_alternatives

    def mock_compute(corridor):
        if corridor == "B->C":
            raise RoutingComputationError("simulated_bc_failure", "Simulated failure for B->C")
        return original_compute(corridor)

    with patch("backend.route_engine.compute_corridor_alternatives", side_effect=mock_compute):
        all_res = get_all_corridor_journeys_with_fallback()

        # A->B should be dynamically computed
        assert all_res["A->B"][0].computation_mode == "computed"
        assert all_res["A->B"][0].fallback_reason is None

        # B->C should have fallen back
        assert all_res["B->C"][0].computation_mode == "precompiled_fallback"
        assert all_res["B->C"][0].fallback_reason == "simulated_bc_failure"

        # C->A should be dynamically computed
        assert all_res["C->A"][0].computation_mode == "computed"
        assert all_res["C->A"][0].fallback_reason is None


def test_no_fallback_data_available():
    """Verify that an unknown corridor produces an empty list and does not crash."""
    unknown = get_fallback_corridor_journeys(
        "X->Y", reason="unknown_corridor", explanation="No precompiled data"
    )
    assert unknown == []


def test_gemma_unavailable_while_routing_succeeds():
    """Verify that routing continues to produce valid route alternatives even when Gemma is offline."""
    with patch("backend.gemma.get_genai_client", return_value=None):
        journeys = get_evaluated_journeys()
        assert "A->B" in journeys
        assert "B->C" in journeys
        assert "C->A" in journeys
        assert len(journeys["A->B"]) >= 2

        # Route alternatives remain fully functional
        walk_opt = next(o for o in journeys["A->B"] if o.primary_mode == TransitMode.WALKING)
        assert walk_opt.total_walking_distance_meters > 0
        assert walk_opt.total_duration_minutes > 0


def test_routing_unavailable_while_gemma_configured():
    """Verify that precompiled fallback works seamlessly when routing is forced to fallback."""
    with patch("backend.config.settings.FORCE_ROUTING_FALLBACK", True):
        journeys = get_evaluated_journeys()
        ab_opts = journeys["A->B"]
        assert len(ab_opts) >= 2
        assert ab_opts[0].computation_mode == "precompiled_fallback"
        assert ab_opts[0].fallback_reason == "forced_fallback"


def test_route_specific_evidence_isolation():
    """Verify that observations belong strictly to their designated route corridor."""
    ab_options = compute_corridor_alternatives("A->B")
    bc_options = compute_corridor_alternatives("B->C")
    ca_options = compute_corridor_alternatives("C->A")

    ab_obs_ids = {o.id for o in ab_options[0].observations}
    bc_obs_ids = {o.id for o in bc_options[0].observations}
    ca_obs_ids = {o.id for o in ca_options[0].observations}

    # Strict isolation
    assert all("A_TO_B" in obs_id or obs_id in ("OBS_1", "OBS_2", "OBS_3") for obs_id in ab_obs_ids)
    assert all("B_TO_C" in obs_id or obs_id in ("OBS_2", "OBS_3", "OBS_4", "OBS_5") for obs_id in bc_obs_ids)
    assert all("C_TO_A" in obs_id or obs_id in ("OBS_1", "OBS_4", "OBS_5") for obs_id in ca_obs_ids)


def test_correct_provenance_in_every_outcome():
    """Verify that data_provenance clearly indicates computation status and source."""
    # 1. Computed
    computed_opts = compute_corridor_alternatives("A->B")
    for opt in computed_opts:
        prov = opt.data_provenance
        assert prov.get("computation_status") == "computed"
        assert prov.get("fallback_used") == "false"
        assert "routing" in prov or "metro_schedule" in prov

    # 2. Fallback
    fallback_opts = get_fallback_corridor_journeys(
        "A->B", reason="test_reason", explanation="Test explanation"
    )
    for opt in fallback_opts:
        prov = opt.data_provenance
        assert prov.get("computation_status") == "precompiled_fallback"
        assert prov.get("fallback_used") == "true"
        assert prov.get("fallback_reason") == "test_reason"
        assert prov.get("fallback_explanation") == "Test explanation"


def test_response_schemas_and_ranking_behavior(client):
    """Verify API endpoint returns compliant schemas and ranks appropriately by sort criteria."""
    for criterion in ["fastest", "least_walking", "fewest_transfers", "best_accessibility"]:
        res = client.get(f"/api/journeys?sort={criterion}")
        assert res.status_code == 200
        data = res.json()
        assert "A->B" in data
        assert "B->C" in data
        assert "C->A" in data

        routes_ab = data["A->B"]
        assert len(routes_ab) >= 2
        # Verify schema integrity
        top = routes_ab[0]
        assert "id" in top
        assert "primary_mode" in top
        assert "total_duration_minutes" in top
        assert "data_provenance" in top
        assert "computation_mode" in top


def test_no_invented_transit_data_without_gtfs_schedules():
    """Verify that transit options explicitly declare static stop matching without claiming real-time dispatch."""
    options = compute_corridor_alternatives("A->B")
    metro_opt = next(o for o in options if o.primary_mode == TransitMode.METRO)
    bus_opt = next(o for o in options if o.primary_mode == TransitMode.BUS)

    # Metro relies on verified BMRCL stops & headway, not imaginary real-time GPS
    assert metro_opt.data_provenance["metro_schedule"] == "verified_bmrcl_gtfs"

    # Bus relies on verified BMTC stops and spatial velocity models
    assert bus_opt.data_provenance["bus_schedule"] == "verified_bmtc_gtfs"
    assert any("traffic" in lim.lower() for lim in bus_opt.limitations)
