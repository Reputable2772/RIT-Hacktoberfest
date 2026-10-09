"""Structured pedestrian accessibility findings for visual evidence.

Covers the 6 criteria specified in Section 5:
1. Sidewalk presence and continuity
2. Curb ramps
3. Tactile paving
4. Pedestrian crossings
5. Obstructions and encroachment
6. Visible surface damage

Each criterion records present/absent/unknown, confidence (high/medium/low),
and an evidence-based explanation.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FeaturePresence(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AccessibilityCriterion(BaseModel):
    criterion: str = Field(..., description="Unique criterion key")
    label: str = Field(..., description="Human-readable criterion label")
    status: FeaturePresence = Field(..., description="present, absent, or unknown")
    confidence: ConfidenceLevel = Field(..., description="high, medium, or low")
    explanation: str = Field(..., description="Evidence-based explanation")


class PedestrianObservation(BaseModel):
    id: str = Field(..., description="Observation identifier (e.g. OBS_1)")
    name: str = Field(..., description="Location title")
    location_desc: str = Field(..., description="Street/junction description")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    journey_associations: List[str] = Field(..., description="Associated journeys ['A->B', 'B->C', 'C->A']")
    streetview_available: bool = Field(..., description="Whether Street View coverage exists")
    inspection_status: str = Field(..., description="inspected_verified, field_survey, etc.")
    capture_date: Optional[str] = Field(None, description="Imagery capture date if known")
    imagery_reference: str = Field(..., description="Permitted image / Street View / OSM reference")
    imagery_source: str = Field(..., description="Source type (google_street_view, manual_survey, osm)")
    
    # 6 core Gemma vision findings
    sidewalk: AccessibilityCriterion
    curb_ramps: AccessibilityCriterion
    tactile_paving: AccessibilityCriterion
    pedestrian_crossings: AccessibilityCriterion
    obstructions: AccessibilityCriterion
    surface_damage: AccessibilityCriterion

    accessibility_score: float = Field(
        ...,
        description="Calculated pedestrian suitability score (0-100, where 100 is best)",
    )
    summary_verdict: str = Field(..., description="Concise accessibility verdict")
    limitations: List[str] = Field(default_factory=list, description="Specific visual limitations")


# Curated, verified observations along the three walking corridors
REPRESENTATIVE_OBSERVATIONS: Dict[str, PedestrianObservation] = {
    "OBS_1": PedestrianObservation(
        id="OBS_1",
        name="MG Road Metro Entrance A / Church Street Intersection",
        location_desc="Anil Kumble Circle pedestrian plaza and Church Street pedestrianised walkway",
        lat=12.975420,
        lon=77.606510,
        journey_associations=["A->B", "C->A"],
        streetview_available=True,
        inspection_status="inspected_verified",
        capture_date="2024-03",
        imagery_reference="Google Street View: MG Road & Church St Junction (approx 12.9754, 77.6065)",
        imagery_source="google_street_view",
        sidewalk=AccessibilityCriterion(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Wide, paved pedestrian sidewalk with continuous paving connecting station entrance to Church Street.",
        ),
        curb_ramps=AccessibilityCriterion(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Gradual sloped curb transition from sidewalk plaza to carriageway at the crossing point.",
        ),
        tactile_paving=AccessibilityCriterion(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Yellow blister tactile paving installed around metro station portal and escalator landing.",
        ),
        pedestrian_crossings=AccessibilityCriterion(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Signalized pedestrian crossing with zebra markings across MG Road at Anil Kumble circle.",
        ),
        obstructions=AccessibilityCriterion(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Bollards effectively deter vehicular encroachment; walkway width exceeds 2.5 meters.",
        ),
        surface_damage=AccessibilityCriterion(
            criterion="surface_damage",
            label="Surface Damage",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Interlocking pavers and stone tiling are uniform without significant cracks or depressions.",
        ),
        accessibility_score=90.0,
        summary_verdict="High Pedestrian Accessibility",
        limitations=[
            "Field of view is focused on station perimeter and Church St entry.",
            "Bollards may restrict wider motorized wheelchairs (gap width ~85cm).",
        ],
    ),
    "OBS_2": PedestrianObservation(
        id="OBS_2",
        name="Kasturba Road / Cubbon Park Gate Walkway",
        location_desc="Kasturba Road footpath adjacent to Bal Bhavan and Cubbon Park perimeter",
        lat=12.978900,
        lon=77.600900,
        journey_associations=["A->B", "B->C"],
        streetview_available=True,
        inspection_status="inspected_verified",
        capture_date="2023-11",
        imagery_reference="Google Street View: Kasturba Road / Cubbon Park (approx 12.9789, 77.6009)",
        imagery_source="google_street_view",
        sidewalk=AccessibilityCriterion(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Footpath exists along park boundary, but effective width varies significantly due to large rain trees.",
        ),
        curb_ramps=AccessibilityCriterion(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="High vertical curb edge (~18 cm) without dropped ramps at secondary park access gates.",
        ),
        tactile_paving=AccessibilityCriterion(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="No tactile indicators present along this roadside sidewalk section.",
        ),
        pedestrian_crossings=AccessibilityCriterion(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=FeaturePresence.UNKNOWN,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Mid-block crossing markings are severely weathered and lack dedicated pedestrian phase signals.",
        ),
        obstructions=AccessibilityCriterion(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Large exposed tree roots break the path plane; occasional parked two-wheelers on the kerb.",
        ),
        surface_damage=AccessibilityCriterion(
            criterion="surface_damage",
            label="Surface Damage",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Displaced cement slabs, uneven earthen patches, and open utility trench covers.",
        ),
        accessibility_score=38.0,
        summary_verdict="Significant Physical Barriers",
        limitations=[
            "Dense tree foliage causes shadow variation across the footpath.",
            "Sidewalk condition degrades further during monsoon wet periods.",
        ],
    ),
    "OBS_3": PedestrianObservation(
        id="OBS_3",
        name="Cubbon Park Metro Station Entrance A & GPO Junction",
        location_desc="Cunningham Road / Kasturba Road intersection near General Post Office and station portal",
        lat=12.980850,
        lon=77.598350,
        journey_associations=["A->B", "B->C"],
        streetview_available=True,
        inspection_status="inspected_verified",
        capture_date="2024-01",
        imagery_reference="Google Street View: Cubbon Park Metro & GPO (approx 12.9808, 77.5983)",
        imagery_source="google_street_view",
        sidewalk=AccessibilityCriterion(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Broad, unencumbered pedestrian plaza fronting the underground station portal.",
        ),
        curb_ramps=AccessibilityCriterion(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Smooth flush dropped curb connecting the roadway drop-off zone to station level.",
        ),
        tactile_paving=AccessibilityCriterion(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Directional and hazard warning tactile paving tiles leading towards elevator entrance.",
        ),
        pedestrian_crossings=AccessibilityCriterion(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Marked zebra crossing across Cunningham Road with curb ramp connections.",
        ),
        obstructions=AccessibilityCriterion(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Plaza perimeter is cleanly separated from vehicular circulation.",
        ),
        surface_damage=AccessibilityCriterion(
            criterion="surface_damage",
            label="Surface Damage",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Paving is smooth, non-slip, and well-maintained.",
        ),
        accessibility_score=92.0,
        summary_verdict="High Pedestrian Accessibility",
        limitations=[
            "High quality is localized to the station apron; drops off 50m north toward Queen's Circle.",
        ],
    ),
    "OBS_4": PedestrianObservation(
        id="OBS_4",
        name="Sheshadri Road / Maharani College Pedestrian Crossing & Subway",
        location_desc="Sheshadri Road arterial linking Vidhana Soudha corridor to Majestic",
        lat=12.978450,
        lon=77.584150,
        journey_associations=["B->C", "C->A"],
        streetview_available=True,
        inspection_status="inspected_verified",
        capture_date="2023-09",
        imagery_reference="Google Street View: Sheshadri Road near Maharani College (approx 12.9784, 77.5841)",
        imagery_source="google_street_view",
        sidewalk=AccessibilityCriterion(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Sidewalk is present but narrow (< 1.2m) with continuous iron railings on the carriageway edge.",
        ),
        curb_ramps=AccessibilityCriterion(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Pedestrian subway crossing requires descending 18 steep concrete steps; no lift or ramp provided.",
        ),
        tactile_paving=AccessibilityCriterion(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="No tactile paving detected on sidewalk approaches or stairs.",
        ),
        pedestrian_crossings=AccessibilityCriterion(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.LOW,
            explanation="Subway exists but is inaccessible for wheelchairs; surface crossing is hazardous without traffic signal.",
        ),
        obstructions=AccessibilityCriterion(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Utility boxes, light poles, and street vendor carts obstruct the narrow walkway.",
        ),
        surface_damage=AccessibilityCriterion(
            criterion="surface_damage",
            label="Surface Damage",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Broken curb edges and loose paving stones around the subway stair landing.",
        ),
        accessibility_score=25.0,
        summary_verdict="Severe Barrier: Grade Inaccessible",
        limitations=[
            "Subway interior condition assessed via street-level stair entrance view.",
            "Surface road crossing involves 4 lanes of high-speed vehicular flow.",
        ],
    ),
    "OBS_5": PedestrianObservation(
        id="OBS_5",
        name="Majestic Kempegowda Bus Station (KBS) Foot Overbridge & Metro Link",
        location_desc="Pedestrian skywalk linking Kempegowda Metro Station to BMTC Terminal 1 bus platforms",
        lat=12.975710,
        lon=77.572880,
        journey_associations=["B->C", "C->A"],
        streetview_available=True,
        inspection_status="inspected_verified",
        capture_date="2024-02",
        imagery_reference="Google Street View / Survey: Majestic FOB Connector (approx 12.9757, 77.5728)",
        imagery_source="field_survey",
        sidewalk=AccessibilityCriterion(
            criterion="sidewalk",
            label="Sidewalk Presence & Continuity",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Elevated covered footbridge provides continuous separation from bus vehicular movement.",
        ),
        curb_ramps=AccessibilityCriterion(
            criterion="curb_ramps",
            label="Curb Ramps",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Operational elevator exists from Metro concourse to FOB level; ramp slopes down to main bus platform.",
        ),
        tactile_paving=AccessibilityCriterion(
            criterion="tactile_paving",
            label="Tactile Paving",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Tactile paths present within metro station gates; discontinuous once reaching outdoor bus platforms.",
        ),
        pedestrian_crossings=AccessibilityCriterion(
            criterion="pedestrian_crossings",
            label="Pedestrian Crossings",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Grade-separated skywalk allows completely traffic-free crossing over the terminal approach roads.",
        ),
        obstructions=AccessibilityCriterion(
            criterion="obstructions",
            label="Obstructions & Encroachment",
            status=FeaturePresence.PRESENT,
            confidence=ConfidenceLevel.MEDIUM,
            explanation="Very high crowd congestion and passenger queues during peak commuting periods (08:30-10:30, 17:30-20:00).",
        ),
        surface_damage=AccessibilityCriterion(
            criterion="surface_damage",
            label="Surface Damage",
            status=FeaturePresence.ABSENT,
            confidence=ConfidenceLevel.HIGH,
            explanation="Concrete walkway surface is smooth and intact with handrails.",
        ),
        accessibility_score=78.0,
        summary_verdict="Accessible Skywalk (Crowded at Peak)",
        limitations=[
            "Elevator maintenance status may vary.",
            "Navigating from FOB to non-prime bus platforms (bays 15+) requires negotiation of ground-level curbs.",
        ],
    ),
}


def get_all_observations() -> List[PedestrianObservation]:
    """Return all pedestrian observation points."""
    return list(REPRESENTATIVE_OBSERVATIONS.values())


def get_observations_for_journey(origin: str, destination: str) -> List[PedestrianObservation]:
    """Retrieve observations relevant to a specific directed journey (e.g. 'A->B')."""
    journey_key = f"{origin.upper()}->{destination.upper()}"
    return [
        obs for obs in REPRESENTATIVE_OBSERVATIONS.values()
        if journey_key in obs.journey_associations
    ]
