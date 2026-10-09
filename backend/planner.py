"""Multimodal journey planner connecting transit datasets, imagery, and Gemma vision analysis.

Supports two location modes:
- Mode A: Fixed demo locations (A: MG Road, B: Cubbon Park, C: Majestic) with prepared Street View imagery
- Mode B: General arbitrary locations with GTFS-matched routing and user-uploaded pedestrian imagery
"""

import math
import os
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.config import settings
from backend.gemma import (
    analyze_pedestrian_image_multimodal,
    create_unavailable_analysis,
)
from backend.gtfs_service import gtfs_index
from backend.image_quality import assess_image_quality
from backend.locations import FIXED_LOCATIONS, DemoLocation, get_location
from backend.manifest_service import (
    LEGACY_OBS_MAP,
    REVERSE_LEGACY_MAP,
    ROUTE_METADATA,
    manifest_service,
)
from backend.schemas import (
    AccessibilityCriterionFinding,
    ConfidenceRating,
    FeatureStatus,
    GemmaVisualAnalysis,
    ObservationCoverageSummary,
)
from backend.transit_data import (
    ALL_JOURNEY_OPTIONS,
    JourneyOption,
    RouteSegment,
    TransitMode,
    get_all_journeys,
    get_journeys_for_direction,
)

# Runtime cache mapping observation ID / segment ID to Gemma analysis
ANALYSIS_CACHE: Dict[str, GemmaVisualAnalysis] = {}

# Prepared image registry for Mode A demo locations
PREPARED_IMAGES_MAP = {
    "OBS_1": {
        "filename": "data/street_view/a_to_b/0001.png",
        "legacy_name": "OBS_1_mg_road.jpg",
        "name": "MG Road Metro Entrance A / Church Street",
        "location": "MG Road (Point A)",
        "lat": 12.975420,
        "lon": 77.606510,
    },
    "OBS_2": {
        "filename": "data/street_view/a_to_b/0011.png",
        "legacy_name": "OBS_2_kasturba_road.jpg",
        "name": "Kasturba Road / Cubbon Park Walkway",
        "location": "Kasturba Road connector (A <-> B)",
        "lat": 12.978900,
        "lon": 77.600900,
    },
    "OBS_3": {
        "filename": "data/street_view/b_to_c/0001.png",
        "legacy_name": "OBS_3_cubbon_park.jpg",
        "name": "Cubbon Park Metro Entrance A Plaza",
        "location": "Cubbon Park (Point B)",
        "lat": 12.980850,
        "lon": 77.598350,
    },
    "OBS_4": {
        "filename": "data/street_view/b_to_c/0005.png",
        "legacy_name": "OBS_4_sheshadri_subway.jpg",
        "name": "Sheshadri Road / Maharani College Subway",
        "location": "Sheshadri Road connector (B <-> C)",
        "lat": 12.978450,
        "lon": 77.584150,
    },
    "OBS_5": {
        "filename": "data/street_view/b_to_c/0008.png",
        "legacy_name": "OBS_5_majestic_fob.jpg",
        "name": "Majestic KBS Bus Terminal & Metro Skywalk",
        "location": "Majestic Interchange (Point C)",
        "lat": 12.975710,
        "lon": 77.572880,
    },
}

# Observation to corridor and segment associations
OBSERVATION_SEGMENT_MAP: Dict[str, Dict[str, List[str]]] = {
    "OBS_1": {
        "corridors": ["A->B", "C->A"],
        "segments": ["AB_M_1", "AB_B_1", "AB_W_1", "CA_W_3", "CA_M_3", "CA_B_3", "CA_MX_3"],
    },
    "OBS_2": {
        "corridors": ["A->B", "B->C"],
        "segments": ["AB_W_2", "AB_B_1", "BC_W_1"],
    },
    "OBS_3": {
        "corridors": ["A->B", "B->C"],
        "segments": ["AB_M_3", "AB_W_3", "BC_M_1", "BC_W_1", "CA_MX_3"],
    },
    "OBS_4": {
        "corridors": ["B->C"],
        "segments": ["BC_W_2", "BC_B_1"],
    },
    "OBS_5": {
        "corridors": ["B->C", "C->A"],
        "segments": ["BC_M_3", "BC_B_3", "BC_W_3", "CA_M_1", "CA_B_1", "CA_W_1"],
    },
}


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate great-circle distance between two coordinates in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return int(R * c)


def get_image_path(filename: str) -> Optional[str]:
    """Resolve absolute path to an observation image safely within allowed data directories."""
    if not filename:
        return None

    resolved = manifest_service.resolve_image_path(filename)
    if resolved:
        return resolved

    # Fallback for legacy filenames
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        return None

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    normalized_name = os.path.normpath(filename).lstrip(os.path.sep)
    if ".." in normalized_name.split(os.path.sep):
        return None

    for meta in PREPARED_IMAGES_MAP.values():
        if filename in (meta.get("legacy_name"), meta.get("filename")):
            p = os.path.realpath(os.path.join(base_dir, meta["filename"]))
            if os.path.isfile(p):
                return p

    return None


def evaluate_criteria_score(analysis: GemmaVisualAnalysis) -> Tuple[float, List[str], str]:
    """Calculate segment accessibility score (0-100), concerns list, and verdict string.

    Rules:
    - Base score is 50.0 (neutral baseline for unknown/unassessed).
    - If status is 'image_unavailable', 'runtime_unavailable', or 'unassessed':
      returns (50.0, ["Visual accessibility unassessed."], "Unassessed")
    - Confirmed positive features add points:
      - sidewalk present: +15
      - curb_ramps present: +15
      - tactile_paving present: +10
      - pedestrian_crossings present: +10
      - obstructions absent: +15
      - surface_damage absent: +10
    - Confirmed physical barriers subtract points:
      - obstructions present: -30 (path blocked)
      - surface_damage present: -25 (severe trip/wheelchair hazard)
      - sidewalk absent: -25 (forced to walk on active roadway)
      - curb_ramps absent: -20 (step barrier)
    - Unknown features DO NOT add or subtract points (prevents unverified features counting as proof).
    """
    if analysis.status in ("image_unavailable", "runtime_unavailable", "unassessed"):
        return 50.0, ["Visual evidence not available or unassessed for this segment."], "Unassessed"

    known_criteria = 0
    score = 50.0
    concerns = []

    # 1. Sidewalk
    if analysis.sidewalk.status == FeatureStatus.PRESENT:
        score += 15.0
        known_criteria += 1
    elif analysis.sidewalk.status == FeatureStatus.ABSENT:
        score -= 25.0
        concerns.append("No continuous sidewalk; pedestrian must walk in roadway.")
        known_criteria += 1

    # 2. Curb Ramps
    if analysis.curb_ramps.status == FeatureStatus.PRESENT:
        score += 15.0
        known_criteria += 1
    elif analysis.curb_ramps.status == FeatureStatus.ABSENT:
        score -= 20.0
        concerns.append("Missing dropped curb ramps at pedestrian crossing.")
        known_criteria += 1

    # 3. Tactile Paving
    if analysis.tactile_paving.status == FeatureStatus.PRESENT:
        score += 10.0
        known_criteria += 1
    elif analysis.tactile_paving.status == FeatureStatus.ABSENT:
        known_criteria += 1

    # 4. Pedestrian Crossings
    if analysis.pedestrian_crossings.status == FeatureStatus.PRESENT:
        score += 10.0
        known_criteria += 1
    elif analysis.pedestrian_crossings.status == FeatureStatus.ABSENT:
        score -= 10.0
        concerns.append("Uncontrolled crossing without zebra markings or signal.")
        known_criteria += 1

    # 5. Obstructions
    if analysis.obstructions.status == FeatureStatus.PRESENT:
        score -= 30.0
        concerns.append("Physical obstructions or vehicle encroachment blocking footpath.")
        known_criteria += 1
    elif analysis.obstructions.status == FeatureStatus.ABSENT:
        score += 15.0
        known_criteria += 1

    # 6. Surface Damage
    if analysis.surface_damage.status == FeatureStatus.PRESENT:
        score -= 25.0
        concerns.append("Visible surface damage (cracks, potholes, broken pavers, or tree roots).")
        known_criteria += 1
    elif analysis.surface_damage.status == FeatureStatus.ABSENT:
        score += 10.0
        known_criteria += 1

    if known_criteria == 0:
        return 50.0, ["Visual evidence inconclusive: all criteria unknown."], "Unassessed (Inconclusive)"

    clamped_score = max(5.0, min(98.0, round(score, 1)))

    if clamped_score >= 80.0:
        verdict = "Highly Accessible"
    elif clamped_score >= 50.0:
        verdict = "Moderate Accessibility"
    else:
        verdict = "Significant Physical Barriers"

    return clamped_score, concerns, verdict


def recalculate_journey_from_cache(journey: JourneyOption) -> JourneyOption:
    """Dynamically recalculate a journey's accessibility score and concerns from ANALYSIS_CACHE."""
    j_copy = journey.model_copy(deep=True)
    corridor = j_copy.journey_key
    route_id = {"A->B": "a_to_b", "B->C": "b_to_c", "C->A": "c_to_a"}.get(corridor)

    if route_id:
        coverage_reports = manifest_service.get_route_coverage_reports(ANALYSIS_CACHE)
        rep = coverage_reports.get(route_id)
        if rep:
            j_copy.observation_coverage = {
                "total_planned": rep.total_planned,
                "collected": rep.collected_count,
                "unavailable": rep.unavailable_count,
                "analyzed": rep.analyzed_count,
            }

    relevant_analyses: List[GemmaVisualAnalysis] = []
    seen_images: Set[str] = set()

    if route_id:
        for obs in manifest_service.get_observations(route_id=route_id, analysis_cache=ANALYSIS_CACHE):
            if obs.id in ANALYSIS_CACHE:
                analysis = ANALYSIS_CACHE[obs.id]
                img_key = obs.image_filename or obs.id
                if img_key not in seen_images:
                    seen_images.add(img_key)
                    relevant_analyses.append(analysis)

    for obs_id, mapping in OBSERVATION_SEGMENT_MAP.items():
        if corridor in mapping["corridors"] and obs_id in ANALYSIS_CACHE:
            canonical_id = LEGACY_OBS_MAP.get(obs_id, obs_id)
            if canonical_id not in seen_images and obs_id not in seen_images:
                seen_images.add(obs_id)
                relevant_analyses.append(ANALYSIS_CACHE[obs_id])

    for seg in j_copy.segments:
        if seg.id in ANALYSIS_CACHE:
            relevant_analyses.append(ANALYSIS_CACHE[seg.id])

    if not relevant_analyses:
        return j_copy

    segment_scores = []
    accumulated_concerns = list(j_copy.accessibility_concerns)

    for analysis in relevant_analyses:
        score, concerns, verdict = evaluate_criteria_score(analysis)
        segment_scores.append(score)
        for c in concerns:
            if c not in accumulated_concerns and not c.startswith("Visual evidence not available"):
                accumulated_concerns.append(c)

    if segment_scores:
        min_score = min(segment_scores)
        avg_score = sum(segment_scores) / len(segment_scores)
        composite_score = round(min_score * 0.7 + avg_score * 0.3, 1)
        j_copy.accessibility_score = composite_score
        j_copy.accessibility_concerns = accumulated_concerns

        if composite_score >= 80.0:
            j_copy.accessibility_verdict = "Highly Accessible"
        elif composite_score >= 50.0:
            j_copy.accessibility_verdict = "Moderate Accessibility"
        else:
            j_copy.accessibility_verdict = "Significant Physical Barriers"

    return j_copy


def get_evaluated_journeys(sort_criterion: str = "fastest") -> Dict[str, List[JourneyOption]]:
    """Return all journeys across A->B, B->C, and C->A with dynamic scores and rankings."""
    raw_journeys = get_all_journeys()
    evaluated: Dict[str, List[JourneyOption]] = {}

    for key, options in raw_journeys.items():
        recalculated_options = [recalculate_journey_from_cache(opt) for opt in options]
        evaluated[key] = rank_journey_options(recalculated_options, criterion=sort_criterion)

    return evaluated


def run_gemma_analysis_on_prepared_image(obs_id: str) -> GemmaVisualAnalysis:
    """Load prepared image bytes from disk and execute real Gemma multimodal inference.

    Supports both canonical manifest observation IDs (e.g. OBS_A_TO_B_0001) and legacy IDs (OBS_1–5).
    For unavailable gap points, returns an explicit honest unassessed/unavailable status
    without fabricating model outputs.
    """
    if obs_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[obs_id]

    obs_item = manifest_service.get_observation_by_id(obs_id, analysis_cache=ANALYSIS_CACHE)
    legacy_meta = PREPARED_IMAGES_MAP.get(obs_id)

    if not obs_item and not legacy_meta:
        raise ValueError(f"Unknown prepared observation ID: {obs_id}")

    # Case 1: Point is an uncollected gap (collection_status == 'unavailable')
    if obs_item and (obs_item.collection_status == "unavailable" or not obs_item.image_available):
        reason_text = obs_item.unavailable_reason or f"Observation {obs_id} was not collected in Street View."
        analysis = create_unavailable_analysis(
            image_id=obs_id,
            location_id=obs_item.location,
            reason=reason_text,
            status="image_unavailable",
        )
        ANALYSIS_CACHE[obs_id] = analysis
        return analysis

    # Case 2: Collected image on disk
    filename_to_resolve = (
        legacy_meta["filename"] if legacy_meta
        else (obs_item.image_filename if obs_item and obs_item.image_filename else "")
    )
    img_path = get_image_path(filename_to_resolve)
    if not img_path or not os.path.exists(img_path):
        location_desc = legacy_meta["location"] if legacy_meta else (obs_item.location if obs_item else "")
        analysis = create_unavailable_analysis(
            image_id=obs_id,
            location_id=location_desc,
            reason=f"Prepared ground-level Street View image '{filename_to_resolve}' has not yet been collected on disk.",
            status="image_unavailable",
        )
        ANALYSIS_CACHE[obs_id] = analysis
        return analysis

    with open(img_path, "rb") as f:
        image_bytes = f.read()

    # OpenCV quality check
    passed, q_res, _ = assess_image_quality(image_bytes)
    location_desc = legacy_meta["location"] if legacy_meta else (obs_item.location if obs_item else "")
    if not passed:
        analysis = create_unavailable_analysis(
            image_id=obs_id,
            location_id=location_desc,
            reason=f"Image failed quality check: {'; '.join(q_res.issues)}",
            status="quality_failed",
        )
        ANALYSIS_CACHE[obs_id] = analysis
        return analysis

    # Execute genuine Gemma multimodal inference
    mime_type = "image/png" if img_path.endswith(".png") else "image/jpeg"
    analysis, error_msg = analyze_pedestrian_image_multimodal(
        image_bytes=image_bytes,
        mime_type=mime_type,
        image_id=obs_id,
        location_id=location_desc,
    )

    if error_msg or analysis is None:
        if settings.ALLOW_OFFLINE_DEMO_FALLBACK and (obs_id in PREPARED_IMAGES_MAP or obs_id in LEGACY_OBS_MAP):
            analysis = _create_mock_verified_analysis(obs_id, legacy_meta or {"location": location_desc})
            analysis.inference_source = "offline_demo"
        else:
            analysis = create_unavailable_analysis(
                image_id=obs_id,
                location_id=location_desc,
                reason=f"Live model inference unavailable: {error_msg}",
                status="runtime_unavailable",
            )

    ANALYSIS_CACHE[obs_id] = analysis
    return analysis


def _create_mock_verified_analysis(obs_id: str, meta: Dict) -> GemmaVisualAnalysis:
    """Create offline demo verified structured findings when explicitly enabled."""
    profiles = {
        "OBS_1": (
            FeatureStatus.PRESENT, FeatureStatus.PRESENT, FeatureStatus.PRESENT,
            FeatureStatus.PRESENT, FeatureStatus.ABSENT, FeatureStatus.ABSENT,
            92.0, "High Pedestrian Accessibility. Level wide walkway with tactile path and signalized crossing.",
        ),
        "OBS_2": (
            FeatureStatus.PRESENT, FeatureStatus.ABSENT, FeatureStatus.ABSENT,
            FeatureStatus.UNKNOWN, FeatureStatus.PRESENT, FeatureStatus.PRESENT,
            38.0, "Significant Physical Barriers. Heavy tree-root buckling, displaced paving stones, and 18cm unramped curb.",
        ),
        "OBS_3": (
            FeatureStatus.PRESENT, FeatureStatus.PRESENT, FeatureStatus.PRESENT,
            FeatureStatus.PRESENT, FeatureStatus.ABSENT, FeatureStatus.ABSENT,
            94.0, "High Pedestrian Accessibility. Flush dropped curb, tactile paving, and unobstructed station apron.",
        ),
        "OBS_4": (
            FeatureStatus.PRESENT, FeatureStatus.ABSENT, FeatureStatus.ABSENT,
            FeatureStatus.PRESENT, FeatureStatus.PRESENT, FeatureStatus.PRESENT,
            24.0, "Severe Physical Barrier. 18 steep concrete steps without ramp/lift; narrow sidewalk obstructed by vendor carts.",
        ),
        "OBS_5": (
            FeatureStatus.PRESENT, FeatureStatus.PRESENT, FeatureStatus.PRESENT,
            FeatureStatus.PRESENT, FeatureStatus.PRESENT, FeatureStatus.ABSENT,
            80.0, "Good Accessibility via Skywalk. Elevator access connects bus terminal to metro; heavy passenger congestion at peak.",
        ),
    }

    sw, cr, tp, pc, ob, sd, score, summary = profiles.get(
        obs_id,
        (FeatureStatus.UNKNOWN, FeatureStatus.UNKNOWN, FeatureStatus.UNKNOWN,
         FeatureStatus.UNKNOWN, FeatureStatus.UNKNOWN, FeatureStatus.UNKNOWN, 50.0, "Unassessed")
    )

    return GemmaVisualAnalysis(
        image_id=obs_id,
        location_id=meta["location"],
        status="completed",
        inference_source="offline_demo",
        model_used=settings.GEMINI_MODEL,
        evidence_status="BARRIER" if (ob == FeatureStatus.PRESENT or sd == FeatureStatus.PRESENT) else "NO_BARRIER_OBSERVED",
        sidewalk=AccessibilityCriterionFinding(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=sw,
            confidence=ConfidenceRating.HIGH,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        curb_ramps=AccessibilityCriterionFinding(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=cr,
            confidence=ConfidenceRating.HIGH,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        tactile_paving=AccessibilityCriterionFinding(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=tp,
            confidence=ConfidenceRating.HIGH,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        pedestrian_crossings=AccessibilityCriterionFinding(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=pc,
            confidence=ConfidenceRating.MEDIUM,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        obstructions=AccessibilityCriterionFinding(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=ob,
            confidence=ConfidenceRating.HIGH,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        surface_damage=AccessibilityCriterionFinding(
            criterion="surface_damage",
            label="Surface Damage",
            status=sd,
            confidence=ConfidenceRating.HIGH,
            explanation=f"Evaluated from {meta['name']} visual evidence.",
        ),
        calculated_accessibility_score=score,
        summary=summary,
        limitations=["Ground-truthed visual reference evaluated offline without live API key."],
    )


def rank_journey_options(
    options: List[JourneyOption],
    criterion: str = "fastest",
) -> List[JourneyOption]:
    """Rank journey options by user-selected criterion:

    - 'fastest': Lowest total duration (minutes)
    - 'least_walking': Lowest walking distance (meters)
    - 'fewest_transfers': Lowest number of transfers
    - 'best_accessibility': Highest calculated accessibility score (0-100)
    """
    if criterion == "fastest":
        return sorted(options, key=lambda j: j.total_duration_minutes)
    elif criterion == "least_walking":
        return sorted(options, key=lambda j: j.total_walking_distance_meters)
    elif criterion == "fewest_transfers":
        return sorted(options, key=lambda j: (j.total_transfers, j.total_duration_minutes))
    elif criterion == "best_accessibility":
        return sorted(options, key=lambda j: -j.accessibility_score)
    return options


def plan_custom_journey(
    origin_name: str,
    origin_lat: float,
    origin_lon: float,
    dest_name: str,
    dest_lat: float,
    dest_lon: float,
) -> List[JourneyOption]:
    """Mode B: Compute multimodal route alternatives grounded in actual GTFS stops."""
    dist_meters = haversine_distance_meters(origin_lat, origin_lon, dest_lat, dest_lon)
    walk_minutes = max(3, int(dist_meters / 75.0))  # ~4.5 km/h walking speed

    options = []

    # 1. Walking Alternative
    options.append(
        JourneyOption(
            id="CUSTOM_WALK",
            journey_key="CUSTOM",
            origin_key="CUSTOM_ORIGIN",
            destination_key="CUSTOM_DEST",
            origin_name=origin_name,
            destination_name=dest_name,
            primary_mode=TransitMode.WALKING,
            title=f"Direct Walking Route to {dest_name}",
            summary=f"Direct pedestrian journey ({dist_meters}m, approx {walk_minutes} min).",
            total_duration_minutes=walk_minutes,
            total_walking_distance_meters=dist_meters,
            total_transfers=0,
            estimated_wait_time_minutes=0,
            total_fare_inr=0.0,
            accessibility_score=50.0,
            accessibility_verdict="Unassessed (Upload Image to Analyze)",
            accessibility_concerns=[
                "No visual evidence supplied yet for this custom route segment.",
            ],
            data_provenance={
                "routing": "estimated_walking_speed",
                "visual_evidence": "not_supplied",
            },
            recommendation_reasons=[
                "Direct continuous walking path.",
            ],
            limitations=[
                "Visual accessibility analysis is unavailable until suitable pedestrian environment photographs are supplied.",
            ],
            observations=[],
            segments=[
                RouteSegment(
                    id="CUSTOM_SEG_WALK_1",
                    mode=TransitMode.WALKING,
                    from_name=origin_name,
                    to_name=dest_name,
                    from_lat=origin_lat,
                    from_lon=origin_lon,
                    to_lat=dest_lat,
                    to_lon=dest_lon,
                    distance_meters=dist_meters,
                    duration_minutes=walk_minutes,
                    agency="Pedestrian",
                    data_source="estimated_walking_speed",
                    wheelchair_accessible=True,
                    polyline=[[origin_lat, origin_lon], [dest_lat, dest_lon]],
                )
            ],
        )
    )

    # 2. Transit / Bus Alternative Matched to Genuine GTFS Stops
    orig_stops = gtfs_index.find_nearest_bmtc_stops(origin_lat, origin_lon, limit=1)
    dest_stops = gtfs_index.find_nearest_bmtc_stops(dest_lat, dest_lon, limit=1)

    if orig_stops:
        orig_stop = orig_stops[0]
        orig_stop_name = f"BMTC Stop: {orig_stop.stop_name}"
        orig_stop_lat = orig_stop.lat
        orig_stop_lon = orig_stop.lon
        ingress_dist = orig_stop.distance_meters or 200
        ingress_min = max(2, int(ingress_dist / 75.0))
        orig_stop_id = orig_stop.stop_id
    else:
        orig_stop_name = "Nearest Bus Stop (Estimated)"
        orig_stop_lat = origin_lat + 0.002
        orig_stop_lon = origin_lon + 0.002
        ingress_dist = 200
        ingress_min = 3
        orig_stop_id = "EST_ORIGIN"

    if dest_stops:
        dest_stop = dest_stops[0]
        dest_stop_name = f"BMTC Stop: {dest_stop.stop_name}"
        dest_stop_lat = dest_stop.lat
        dest_stop_lon = dest_stop.lon
        egress_dist = dest_stop.distance_meters or 200
        egress_min = max(2, int(egress_dist / 75.0))
        dest_stop_id = dest_stop.stop_id
    else:
        dest_stop_name = "Destination Bus Stop (Estimated)"
        dest_stop_lat = dest_lat - 0.002
        dest_stop_lon = dest_lon - 0.002
        egress_dist = 200
        egress_min = 3
        dest_stop_id = "EST_DEST"

    bus_ride_dist = haversine_distance_meters(orig_stop_lat, orig_stop_lon, dest_stop_lat, dest_stop_lon)
    bus_ride_min = max(5, int(bus_ride_dist / 250.0))  # ~15 km/h urban bus speed

    options.append(
        JourneyOption(
            id="CUSTOM_BUS",
            journey_key="CUSTOM",
            origin_key="CUSTOM_ORIGIN",
            destination_key="CUSTOM_DEST",
            origin_name=origin_name,
            destination_name=dest_name,
            primary_mode=TransitMode.BUS,
            title="BMTC Bus Service via GTFS Matched Stops",
            summary=f"Bus route connecting {orig_stop_name} and {dest_stop_name}.",
            total_duration_minutes=bus_ride_min + ingress_min + egress_min + 6,
            total_walking_distance_meters=ingress_dist + egress_dist,
            total_transfers=0,
            estimated_wait_time_minutes=6,
            total_fare_inr=15.0,
            accessibility_score=50.0,
            accessibility_verdict="Unassessed (Upload Image to Analyze)",
            accessibility_concerns=[
                "Standard bus entrance steps present elevation barrier.",
            ],
            data_provenance={
                "origin_bus_stop": f"gtfs_matched_bmtc_stop:{orig_stop_id}",
                "destination_bus_stop": f"gtfs_matched_bmtc_stop:{dest_stop_id}",
                "transit": "gtfs_stop_matched_spatial_estimate",
                "walking_segments": "estimated_walking_speed",
                "visual_evidence": "not_supplied",
            },
            recommendation_reasons=[
                f"Connects via genuine BMTC stops: {orig_stop_name} and {dest_stop_name}.",
                "Reduces pedestrian exposure compared to direct walking.",
            ],
            limitations=[
                "Upload a photograph of the bus stop boarding area to evaluate curb ramps and tactile paving.",
            ],
            observations=[],
            segments=[
                RouteSegment(
                    id="CUSTOM_SEG_BUS_1",
                    mode=TransitMode.WALKING,
                    from_name=origin_name,
                    to_name=orig_stop_name,
                    from_lat=origin_lat,
                    from_lon=origin_lon,
                    to_lat=orig_stop_lat,
                    to_lon=orig_stop_lon,
                    distance_meters=ingress_dist,
                    duration_minutes=ingress_min,
                    agency="Pedestrian",
                    data_source="estimated_walking_speed",
                    wheelchair_accessible=True,
                    polyline=[[origin_lat, origin_lon], [orig_stop_lat, orig_stop_lon]],
                ),
                RouteSegment(
                    id="CUSTOM_SEG_BUS_2",
                    mode=TransitMode.BUS,
                    from_name=orig_stop_name,
                    to_name=dest_stop_name,
                    from_lat=orig_stop_lat,
                    from_lon=orig_stop_lon,
                    to_lat=dest_stop_lat,
                    to_lon=dest_stop_lon,
                    distance_meters=bus_ride_dist,
                    duration_minutes=bus_ride_min,
                    transit_line="BMTC Bus Service",
                    agency="BMTC",
                    fare_inr=15.0,
                    headway_minutes=8,
                    data_source="gtfs_stop_matched_spatial_estimate",
                    wheelchair_accessible=False,
                    polyline=[
                        [orig_stop_lat, orig_stop_lon],
                        [(orig_stop_lat + dest_stop_lat) / 2.0, (orig_stop_lon + dest_stop_lon) / 2.0],
                        [dest_stop_lat, dest_stop_lon],
                    ],
                ),
                RouteSegment(
                    id="CUSTOM_SEG_BUS_3",
                    mode=TransitMode.WALKING,
                    from_name=dest_stop_name,
                    to_name=dest_name,
                    from_lat=dest_stop_lat,
                    from_lon=dest_stop_lon,
                    to_lat=dest_lat,
                    to_lon=dest_lon,
                    distance_meters=egress_dist,
                    duration_minutes=egress_min,
                    agency="Pedestrian",
                    data_source="estimated_walking_speed",
                    wheelchair_accessible=True,
                    polyline=[[dest_stop_lat, dest_stop_lon], [dest_lat, dest_lon]],
                ),
            ],
        )
    )

    return options
