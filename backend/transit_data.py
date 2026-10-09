"""Bengaluru transit data integration for BMRCL (Metro) and BMTC (Bus).

Implements transit services connecting the three fixed demo locations (A: MG Road, B: Cubbon Park, C: Majestic).
Data provenance distinguishes:
- 'verified_bmrcl_gtfs': Pre-compiled demo fixtures based on verified BMRCL GTFS stops and published Purple Line timetable headways
- 'verified_bmtc_gtfs': Pre-compiled demo fixtures based on verified BMTC GTFS stops and published bus route intervals
- 'estimated_walking_speed': Computed at standard pedestrian speed (~1.25 m/s)
- 'gtfs_stop_matched_spatial_estimate': Dynamic nearest-stop matching against GTFS stops.txt with urban travel speed models
- 'manually_verified_demo': Ground-truthed during field survey for demo corridors
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.locations import FIXED_LOCATIONS, DemoLocation, get_location
from backend.accessibility_findings import (
    PedestrianObservation,
    get_observations_for_journey,
)


class TransitMode(str, Enum):
    METRO = "metro"
    BUS = "bus"
    WALKING = "walking"
    MIXED = "mixed"


class RouteSegment(BaseModel):
    id: str = Field(..., description="Segment ID")
    mode: TransitMode = Field(..., description="Transport mode")
    from_name: str = Field(..., description="Departure point")
    to_name: str = Field(..., description="Arrival point")
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float
    distance_meters: int = Field(..., description="Distance in meters")
    duration_minutes: int = Field(..., description="Duration in minutes")
    transit_line: Optional[str] = Field(None, description="Transit line (e.g. Purple Line, Route 335E)")
    agency: Optional[str] = Field(None, description="Operating agency (BMRCL, BMTC, or Pedestrian)")
    num_intermediate_stops: int = 0
    intermediate_stops: List[str] = Field(default_factory=list)
    fare_inr: Optional[float] = None
    headway_minutes: Optional[int] = None
    data_source: str = Field(..., description="Data provenance tag")
    wheelchair_accessible: bool = True
    pedestrian_concerns: List[str] = Field(default_factory=list)
    polyline: List[List[float]] = Field(
        default_factory=list,
        description="List of [lat, lon] coordinates along segment trajectory",
    )


class JourneyOption(BaseModel):
    id: str = Field(..., description="Unique journey option ID")
    journey_key: str = Field(..., description="Directed journey ('A->B', 'B->C', 'C->A')")
    origin_key: str
    destination_key: str
    origin_name: str
    destination_name: str
    primary_mode: TransitMode
    title: str = Field(..., description="Route headline")
    summary: str = Field(..., description="High-level description")
    total_duration_minutes: int
    total_walking_distance_meters: int
    total_transfers: int
    estimated_wait_time_minutes: int
    total_fare_inr: float
    segments: List[RouteSegment]
    observations: List[PedestrianObservation]
    accessibility_score: float = Field(..., description="Score out of 100")
    accessibility_verdict: str = Field(..., description="Barrier rating")
    accessibility_concerns: List[str] = Field(default_factory=list)
    data_provenance: Dict[str, str] = Field(default_factory=dict)
    recommendation_reasons: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


# --- ROUTE CATALOG FOR DIRECTED JOURNEYS ---

def _build_journey_options() -> Dict[str, List[JourneyOption]]:
    """Build all verified transit alternatives for A->B, B->C, and C->A."""
    loc_a = FIXED_LOCATIONS["A"]
    loc_b = FIXED_LOCATIONS["B"]
    loc_c = FIXED_LOCATIONS["C"]

    obs_a_b = get_observations_for_journey("A", "B")
    obs_b_c = get_observations_for_journey("B", "C")
    obs_c_a = get_observations_for_journey("C", "A")

    return {
        "A->B": [
            # 1. Metro Option (Recommended for accessibility & speed)
            JourneyOption(
                id="J_AB_METRO",
                journey_key="A->B",
                origin_key="A",
                destination_key="B",
                origin_name=loc_a.name,
                destination_name=loc_b.name,
                primary_mode=TransitMode.METRO,
                title="BMRCL Purple Line Metro (Direct)",
                summary="Elevator-accessible metro connection between MG Road and Cubbon Park. 1 stop.",
                total_duration_minutes=9,
                total_walking_distance_meters=210,
                total_transfers=0,
                estimated_wait_time_minutes=3,
                total_fare_inr=10.0,
                accessibility_score=94.0,
                accessibility_verdict="Highly Accessible",
                accessibility_concerns=[],
                recommendation_reasons=[
                    "Fastest transit option (9 min total door-to-door).",
                    "Elevator access verified at both MG Road and Cubbon Park stations.",
                    "Minimizes pedestrian exposure to Kasturba Road curb damage.",
                ],
                data_provenance={
                    "metro_schedule": "verified_bmrcl_gtfs",
                    "walking_segments": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "Platform gaps exist between train and platform (~7cm horizontal, 3cm vertical).",
                ],
                observations=obs_a_b,
                segments=[
                    RouteSegment(
                        id="AB_M_1",
                        mode=TransitMode.WALKING,
                        from_name="MG Road Station Entrance A",
                        to_name="MG Road Platform 1",
                        from_lat=loc_a.lat,
                        from_lon=loc_a.lon,
                        to_lat=12.975429,
                        to_lon=77.607260,
                        distance_meters=110,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_a.lat, loc_a.lon], [12.975429, 77.607260]],
                    ),
                    RouteSegment(
                        id="AB_M_2",
                        mode=TransitMode.METRO,
                        from_name="Mahatma Gandhi Road (MAGR)",
                        to_name="Cubbon Park (CBPK)",
                        from_lat=12.975429,
                        from_lon=77.607260,
                        to_lat=12.980979,
                        to_lon=77.597570,
                        distance_meters=1150,
                        duration_minutes=3,
                        transit_line="Purple Line (Challaghatta direction)",
                        agency="BMRCL",
                        num_intermediate_stops=0,
                        intermediate_stops=[],
                        fare_inr=10.0,
                        headway_minutes=5,
                        data_source="verified_bmrcl_gtfs",
                        wheelchair_accessible=True,
                        polyline=[
                            [12.975429, 77.607260],
                            [12.976000, 77.604000],
                            [12.978500, 77.600000],
                            [12.980979, 77.597570],
                        ],
                    ),
                    RouteSegment(
                        id="AB_M_3",
                        mode=TransitMode.WALKING,
                        from_name="Cubbon Park Platform",
                        to_name="Cubbon Park Station Entrance A",
                        from_lat=12.980979,
                        from_lon=77.597570,
                        to_lat=loc_b.lat,
                        to_lon=loc_b.lon,
                        distance_meters=100,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.980979, 77.597570], [loc_b.lat, loc_b.lon]],
                    ),
                ],
            ),
            # 2. Walking-Only
            JourneyOption(
                id="J_AB_WALK",
                journey_key="A->B",
                origin_key="A",
                destination_key="B",
                origin_name=loc_a.name,
                destination_name=loc_b.name,
                primary_mode=TransitMode.WALKING,
                title="Direct Street Walk via Church St & Kasturba Rd",
                summary="Pedestrian walk along Church Street, Queen's Road and Kasturba Road.",
                total_duration_minutes=17,
                total_walking_distance_meters=1250,
                total_transfers=0,
                estimated_wait_time_minutes=0,
                total_fare_inr=0.0,
                accessibility_score=58.0,
                accessibility_verdict="Moderate Barriers",
                accessibility_concerns=[
                    "Kasturba Road perimeter sidewalk has protruding tree roots (OBS_2).",
                    "Missing dropped curb ramp at park gate drop-off (OBS_2).",
                ],
                recommendation_reasons=[
                    "Zero transit wait time.",
                    "Pleasant route through pedestrianized Church Street segment.",
                ],
                data_provenance={
                    "route": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "Exposed to heat, traffic fumes, and seasonal monsoon puddling.",
                ],
                observations=obs_a_b,
                segments=[
                    RouteSegment(
                        id="AB_W_1",
                        mode=TransitMode.WALKING,
                        from_name=loc_a.name,
                        to_name=loc_b.name,
                        from_lat=loc_a.lat,
                        from_lon=loc_a.lon,
                        to_lat=loc_b.lat,
                        to_lon=loc_b.lon,
                        distance_meters=1250,
                        duration_minutes=17,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=False,
                        pedestrian_concerns=[
                            "Unpaved earthen edge and root displacements near Bal Bhavan gate.",
                        ],
                        polyline=[
                            [12.975526, 77.606790],
                            [12.975420, 77.606510],
                            [12.975800, 77.603000],
                            [12.977200, 77.601500],
                            [12.978900, 77.600900],
                            [12.980958, 77.597570],
                        ],
                    )
                ],
            ),
            # 3. BMTC Bus
            JourneyOption(
                id="J_AB_BUS",
                journey_key="A->B",
                origin_key="A",
                destination_key="B",
                origin_name=loc_a.name,
                destination_name=loc_b.name,
                primary_mode=TransitMode.BUS,
                title="BMTC Bus (Route 335E / 138)",
                summary="Bus from Anil Kumble Circle to GPO / Police Corner, then short walk.",
                total_duration_minutes=18,
                total_walking_distance_meters=260,
                total_transfers=0,
                estimated_wait_time_minutes=6,
                total_fare_inr=15.0,
                accessibility_score=68.0,
                accessibility_verdict="Partial Accessibility",
                accessibility_concerns=[
                    "Bus high-floor boarding steps (35 cm vertical rise).",
                    "Boarding curb crowding at Anil Kumble circle.",
                ],
                recommendation_reasons=[
                    "Frequent service on MG Road trunk route.",
                ],
                data_provenance={
                    "bus_schedule": "verified_bmtc_gtfs",
                    "walking_segments": "estimated_walking_speed",
                },
                limitations=[
                    "Subject to road traffic congestion at Queen's Circle.",
                ],
                observations=obs_a_b,
                segments=[
                    RouteSegment(
                        id="AB_B_1",
                        mode=TransitMode.WALKING,
                        from_name="MG Road Station",
                        to_name="Anil Kumble Circle Bus Stop",
                        from_lat=loc_a.lat,
                        from_lon=loc_a.lon,
                        to_lat=12.975400,
                        to_lon=77.605800,
                        distance_meters=110,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_a.lat, loc_a.lon], [12.975400, 77.605800]],
                    ),
                    RouteSegment(
                        id="AB_B_2",
                        mode=TransitMode.BUS,
                        from_name="Anil Kumble Circle",
                        to_name="Police Corner / GPO",
                        from_lat=12.975400,
                        from_lon=77.605800,
                        to_lat=12.980680,
                        to_lon=77.598350,
                        distance_meters=1350,
                        duration_minutes=8,
                        transit_line="Route 335E / 138",
                        agency="BMTC",
                        num_intermediate_stops=1,
                        intermediate_stops=["BRV Parade Ground"],
                        fare_inr=15.0,
                        headway_minutes=7,
                        data_source="verified_bmtc_gtfs",
                        wheelchair_accessible=False,
                        polyline=[
                            [12.975400, 77.605800],
                            [12.976500, 77.603000],
                            [12.978200, 77.600500],
                            [12.980680, 77.598350],
                        ],
                    ),
                    RouteSegment(
                        id="AB_B_3",
                        mode=TransitMode.WALKING,
                        from_name="Police Corner Bus Stop",
                        to_name="Cubbon Park Metro",
                        from_lat=12.980680,
                        from_lon=77.598350,
                        to_lat=loc_b.lat,
                        to_lon=loc_b.lon,
                        distance_meters=150,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.980680, 77.598350], [loc_b.lat, loc_b.lon]],
                    ),
                ],
            ),
        ],

        "B->C": [
            # 1. Metro Option (BMRCL Purple Line)
            JourneyOption(
                id="J_BC_METRO",
                journey_key="B->C",
                origin_key="B",
                destination_key="C",
                origin_name=loc_b.name,
                destination_name=loc_c.name,
                primary_mode=TransitMode.METRO,
                title="BMRCL Purple Line Metro (Direct)",
                summary="Fast direct connection via Vidhana Soudha & Central College to Majestic. 3 stops.",
                total_duration_minutes=13,
                total_walking_distance_meters=270,
                total_transfers=0,
                estimated_wait_time_minutes=3,
                total_fare_inr=15.0,
                accessibility_score=93.0,
                accessibility_verdict="Highly Accessible",
                accessibility_concerns=[],
                recommendation_reasons=[
                    "Drastically faster than road options (13 min vs 35+ min).",
                    "Completely bypasses severe pedestrian hazards on Sheshadri Road (OBS_4).",
                    "Elevators operational at both Cubbon Park and Majestic terminals.",
                ],
                data_provenance={
                    "metro_schedule": "verified_bmrcl_gtfs",
                    "walking_segments": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "High passenger crowd density at Majestic interchange during peak hours.",
                ],
                observations=obs_b_c,
                segments=[
                    RouteSegment(
                        id="BC_M_1",
                        mode=TransitMode.WALKING,
                        from_name="Cubbon Park Entrance A",
                        to_name="Cubbon Park Platform 2",
                        from_lat=loc_b.lat,
                        from_lon=loc_b.lon,
                        to_lat=12.980895,
                        to_lon=77.597565,
                        distance_meters=90,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_b.lat, loc_b.lon], [12.980895, 77.597565]],
                    ),
                    RouteSegment(
                        id="BC_M_2",
                        mode=TransitMode.METRO,
                        from_name="Cubbon Park (CBPK)",
                        to_name="Nadaprabhu Kempegowda Station, Majestic (KGWA)",
                        from_lat=12.980895,
                        from_lon=77.597565,
                        to_lat=12.975670,
                        to_lon=77.572810,
                        distance_meters=2750,
                        duration_minutes=6,
                        transit_line="Purple Line (Challaghatta direction)",
                        agency="BMRCL",
                        num_intermediate_stops=2,
                        intermediate_stops=[
                            "Dr. B.R. Ambedkar Vidhana Soudha (VDSU)",
                            "Sir M. Visveshwaraya Central College (SVCU)",
                        ],
                        fare_inr=15.0,
                        headway_minutes=5,
                        data_source="verified_bmrcl_gtfs",
                        wheelchair_accessible=True,
                        polyline=[
                            [12.980895, 77.597565],
                            [12.979800, 77.590500],
                            [12.977500, 77.581500],
                            [12.975670, 77.572810],
                        ],
                    ),
                    RouteSegment(
                        id="BC_M_3",
                        mode=TransitMode.WALKING,
                        from_name="Majestic Metro Platform",
                        to_name="Majestic Station FOB Connector",
                        from_lat=12.975670,
                        from_lon=77.572810,
                        to_lat=loc_c.lat,
                        to_lon=loc_c.lon,
                        distance_meters=180,
                        duration_minutes=3,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.975670, 77.572810], [loc_c.lat, loc_c.lon]],
                    ),
                ],
            ),
            # 2. BMTC Bus
            JourneyOption(
                id="J_BC_BUS",
                journey_key="B->C",
                origin_key="B",
                destination_key="C",
                origin_name=loc_b.name,
                destination_name=loc_c.name,
                primary_mode=TransitMode.BUS,
                title="BMTC Bus (Route 290E / 305D / G-4)",
                summary="Bus from GPO via K.R. Circle & Sheshadri Road to Kempegowda Bus Station.",
                total_duration_minutes=26,
                total_walking_distance_meters=280,
                total_transfers=0,
                estimated_wait_time_minutes=5,
                total_fare_inr=15.0,
                accessibility_score=64.0,
                accessibility_verdict="Partial Accessibility",
                accessibility_concerns=[
                    "Bus boarding steps.",
                    "Congestion on KBS bus platform concourse.",
                ],
                recommendation_reasons=[
                    "Direct drop-off at central bus terminal bays.",
                ],
                data_provenance={
                    "bus_schedule": "verified_bmtc_gtfs",
                    "walking_segments": "estimated_walking_speed",
                },
                limitations=[
                    "Severe traffic bottleneck around K.R. Circle junction during evening peak.",
                ],
                observations=obs_b_c,
                segments=[
                    RouteSegment(
                        id="BC_B_1",
                        mode=TransitMode.WALKING,
                        from_name="Cubbon Park Metro",
                        to_name="GPO Bus Stop",
                        from_lat=loc_b.lat,
                        from_lon=loc_b.lon,
                        to_lat=12.980680,
                        to_lon=77.598310,
                        distance_meters=110,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_b.lat, loc_b.lon], [12.980680, 77.598310]],
                    ),
                    RouteSegment(
                        id="BC_B_2",
                        mode=TransitMode.BUS,
                        from_name="GPO",
                        to_name="Kempegowda Bus Station",
                        from_lat=12.980680,
                        from_lon=77.598310,
                        to_lat=12.977510,
                        to_lon=77.571410,
                        distance_meters=3100,
                        duration_minutes=18,
                        transit_line="Route G-4 / 290E",
                        agency="BMTC",
                        num_intermediate_stops=4,
                        intermediate_stops=["Vidhana Soudha", "K.R. Circle", "Maharani College", "City Civil Court"],
                        fare_inr=15.0,
                        headway_minutes=6,
                        data_source="verified_bmtc_gtfs",
                        wheelchair_accessible=False,
                        polyline=[
                            [12.980680, 77.598310],
                            [12.979500, 77.591000],
                            [12.978000, 77.585000],
                            [12.977510, 77.571410],
                        ],
                    ),
                    RouteSegment(
                        id="BC_B_3",
                        mode=TransitMode.WALKING,
                        from_name="Kempegowda Bus Stop",
                        to_name="Majestic Station Entrance",
                        from_lat=12.977510,
                        from_lon=77.571410,
                        to_lat=loc_c.lat,
                        to_lon=loc_c.lon,
                        distance_meters=170,
                        duration_minutes=3,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.977510, 77.571410], [loc_c.lat, loc_c.lon]],
                    ),
                ],
            ),
            # 3. Walking-Only (NOT RECOMMENDED DUE TO SEVERE BARRIERS)
            JourneyOption(
                id="J_BC_WALK",
                journey_key="B->C",
                origin_key="B",
                destination_key="C",
                origin_name=loc_b.name,
                destination_name=loc_c.name,
                primary_mode=TransitMode.WALKING,
                title="Walking Route via Sheshadri Road",
                summary="Pedestrian walk via Ambedkar Veedhi and Sheshadri Road to Majestic.",
                total_duration_minutes=41,
                total_walking_distance_meters=2900,
                total_transfers=0,
                estimated_wait_time_minutes=0,
                total_fare_inr=0.0,
                accessibility_score=31.0,
                accessibility_verdict="Severe Barriers Present",
                accessibility_concerns=[
                    "Critical barrier: Maharani College subway requires 18 steep stairs without lift (OBS_4).",
                    "Narrow sidewalk (<1.2m) obstructed by street vendors and utilities (OBS_4).",
                    "Extremely hostile pedestrian crossing over 4-lane arterial road.",
                ],
                recommendation_reasons=[
                    "Exercise/leisure option only; strongly discouraged for individuals with mobility impairments.",
                ],
                data_provenance={
                    "route": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "Pedestrian routing along Sheshadri Road is unsafe after dark due to poor lighting.",
                ],
                observations=obs_b_c,
                segments=[
                    RouteSegment(
                        id="BC_W_1",
                        mode=TransitMode.WALKING,
                        from_name=loc_b.name,
                        to_name=loc_c.name,
                        from_lat=loc_b.lat,
                        from_lon=loc_b.lon,
                        to_lat=loc_c.lat,
                        to_lon=loc_c.lon,
                        distance_meters=2900,
                        duration_minutes=41,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=False,
                        pedestrian_concerns=[
                            "Steep stairs at pedestrian subway; broken pavement; high traffic collision risk.",
                        ],
                        polyline=[
                            [12.980958, 77.597570],
                            [12.979800, 77.590500],
                            [12.978450, 77.584150],
                            [12.976500, 77.577000],
                            [12.975708, 77.572876],
                        ],
                    )
                ],
            ),
        ],

        "C->A": [
            # 1. Metro Option (Recommended)
            JourneyOption(
                id="J_CA_METRO",
                journey_key="C->A",
                origin_key="C",
                destination_key="A",
                origin_name=loc_c.name,
                destination_name=loc_a.name,
                primary_mode=TransitMode.METRO,
                title="BMRCL Purple Line Metro (Direct)",
                summary="High-capacity direct subway connection from Majestic to MG Road. 4 stops.",
                total_duration_minutes=15,
                total_walking_distance_meters=260,
                total_transfers=0,
                estimated_wait_time_minutes=3,
                total_fare_inr=18.0,
                accessibility_score=92.0,
                accessibility_verdict="Highly Accessible",
                accessibility_concerns=[],
                recommendation_reasons=[
                    "Direct corridor connection in only 9 minutes train ride time.",
                    "Full tactile pathing from entrance to platform at both terminals.",
                    "Avoids all congested surface crossings across central business district.",
                ],
                data_provenance={
                    "metro_schedule": "verified_bmrcl_gtfs",
                    "walking_segments": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "High passenger footfall at Majestic concourse can require patience in queues.",
                ],
                observations=obs_c_a,
                segments=[
                    RouteSegment(
                        id="CA_M_1",
                        mode=TransitMode.WALKING,
                        from_name="Majestic Station Concourse",
                        to_name="Majestic Purple Line Platform 1",
                        from_lat=loc_c.lat,
                        from_lon=loc_c.lon,
                        to_lat=12.975751,
                        to_lon=77.573090,
                        distance_meters=140,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_c.lat, loc_c.lon], [12.975751, 77.573090]],
                    ),
                    RouteSegment(
                        id="CA_M_2",
                        mode=TransitMode.METRO,
                        from_name="Nadaprabhu Kempegowda Station, Majestic (KGWA)",
                        to_name="Mahatma Gandhi Road (MAGR)",
                        from_lat=12.975751,
                        from_lon=77.573090,
                        to_lat=12.975628,
                        to_lon=77.606300,
                        distance_meters=3800,
                        duration_minutes=9,
                        transit_line="Purple Line (Whitefield direction)",
                        agency="BMRCL",
                        num_intermediate_stops=3,
                        intermediate_stops=[
                            "Sir M. Visveshwaraya Central College (SVCU)",
                            "Dr. B.R. Ambedkar Vidhana Soudha (VDSU)",
                            "Cubbon Park (CBPK)",
                        ],
                        fare_inr=18.0,
                        headway_minutes=5,
                        data_source="verified_bmrcl_gtfs",
                        wheelchair_accessible=True,
                        polyline=[
                            [12.975751, 77.573090],
                            [12.977500, 77.581500],
                            [12.979800, 77.590500],
                            [12.980958, 77.597570],
                            [12.975628, 77.606300],
                        ],
                    ),
                    RouteSegment(
                        id="CA_M_3",
                        mode=TransitMode.WALKING,
                        from_name="MG Road Platform 2",
                        to_name="MG Road Station Entrance A",
                        from_lat=12.975628,
                        from_lon=77.606300,
                        to_lat=loc_a.lat,
                        to_lon=loc_a.lon,
                        distance_meters=120,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.975628, 77.606300], [loc_a.lat, loc_a.lon]],
                    ),
                ],
            ),
            # 2. BMTC Bus Option
            JourneyOption(
                id="J_CA_BUS",
                journey_key="C->A",
                origin_key="C",
                destination_key="A",
                origin_name=loc_c.name,
                destination_name=loc_a.name,
                primary_mode=TransitMode.BUS,
                title="BMTC Bus (Route 335E / G-4 Trunk)",
                summary="Direct bus from Kempegowda Bus Station Terminal 1 to Anil Kumble Circle / MG Road.",
                total_duration_minutes=29,
                total_walking_distance_meters=220,
                total_transfers=0,
                estimated_wait_time_minutes=4,
                total_fare_inr=18.0,
                accessibility_score=70.0,
                accessibility_verdict="Partial Accessibility",
                accessibility_concerns=[
                    "Crowded platform boarding at Majestic Terminal 1 (OBS_5).",
                    "Bus entrance step is steep; priority seating not always respected.",
                ],
                recommendation_reasons=[
                    "Continuous point-to-point trunk service running every 4-6 minutes.",
                    "Air-conditioned Vajra bus option available on route 335E.",
                ],
                data_provenance={
                    "bus_schedule": "verified_bmtc_gtfs",
                    "walking_segments": "estimated_walking_speed",
                },
                limitations=[
                    "Travel time varies heavily between 22 and 45 minutes during evening rush hours.",
                ],
                observations=obs_c_a,
                segments=[
                    RouteSegment(
                        id="CA_B_1",
                        mode=TransitMode.WALKING,
                        from_name="Majestic Interchange",
                        to_name="Kempegowda Bus Station Platform 19",
                        from_lat=loc_c.lat,
                        from_lon=loc_c.lon,
                        to_lat=12.977914,
                        to_lon=77.571434,
                        distance_meters=130,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_c.lat, loc_c.lon], [12.977914, 77.571434]],
                    ),
                    RouteSegment(
                        id="CA_B_2",
                        mode=TransitMode.BUS,
                        from_name="Kempegowda Bus Station",
                        to_name="Anil Kumble Circle / MG Road",
                        from_lat=12.977914,
                        from_lon=77.571434,
                        to_lat=12.975400,
                        to_lon=77.605800,
                        distance_meters=4200,
                        duration_minutes=22,
                        transit_line="Route 335E / G-4",
                        agency="BMTC",
                        num_intermediate_stops=6,
                        intermediate_stops=[
                            "Maharani College",
                            "K.R. Circle",
                            "Corporation",
                            "St. Martha's Hospital",
                            "St. Joseph's College",
                            "Mayo Hall",
                        ],
                        fare_inr=18.0,
                        headway_minutes=5,
                        data_source="verified_bmtc_gtfs",
                        wheelchair_accessible=False,
                        polyline=[
                            [12.977914, 77.571434],
                            [12.975000, 77.585000],
                            [12.973000, 77.595000],
                            [12.974500, 77.603000],
                            [12.975400, 77.605800],
                        ],
                    ),
                    RouteSegment(
                        id="CA_B_3",
                        mode=TransitMode.WALKING,
                        from_name="Anil Kumble Circle Bus Stop",
                        to_name="MG Road Metro Entrance A",
                        from_lat=12.975400,
                        from_lon=77.605800,
                        to_lat=loc_a.lat,
                        to_lon=loc_a.lon,
                        distance_meters=90,
                        duration_minutes=1,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[12.975400, 77.605800], [loc_a.lat, loc_a.lon]],
                    ),
                ],
            ),
            # 3. Walking-Only
            JourneyOption(
                id="J_CA_WALK",
                journey_key="C->A",
                origin_key="C",
                destination_key="A",
                origin_name=loc_c.name,
                destination_name=loc_a.name,
                primary_mode=TransitMode.WALKING,
                title="Walking Route via KG Road & Kasturba Rd",
                summary="Long pedestrian walk via Gundopanth St, KG Road and Kasturba Road.",
                total_duration_minutes=53,
                total_walking_distance_meters=3950,
                total_transfers=0,
                estimated_wait_time_minutes=0,
                total_fare_inr=0.0,
                accessibility_score=36.0,
                accessibility_verdict="Significant Physical Barriers",
                accessibility_concerns=[
                    "Long distance (nearly 4 km) with numerous pedestrian crossing conflicts.",
                    "Inconsistent sidewalk continuity along KG Road and Corporation junction.",
                ],
                recommendation_reasons=[
                    "No transit waiting or fare required.",
                ],
                data_provenance={
                    "route": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "Heavy vehicle emissions and high ambient traffic noise along arterial corridors.",
                ],
                observations=obs_c_a,
                segments=[
                    RouteSegment(
                        id="CA_W_1",
                        mode=TransitMode.WALKING,
                        from_name=loc_c.name,
                        to_name=loc_a.name,
                        from_lat=loc_c.lat,
                        from_lon=loc_c.lon,
                        to_lat=loc_a.lat,
                        to_lon=loc_a.lon,
                        distance_meters=3950,
                        duration_minutes=53,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=False,
                        pedestrian_concerns=[
                            "Multiple unramped curb stones, narrow sections, and hazardous vehicle turning conflicts.",
                        ],
                        polyline=[
                            [12.975708, 77.572876],
                            [12.975000, 77.579000],
                            [12.973500, 77.587000],
                            [12.972500, 77.597000],
                            [12.974000, 77.604000],
                            [12.975526, 77.606790],
                        ],
                    )
                ],
            ),
            # 4. Mixed-Mode Option (Metro to Cubbon Park + Scenic Church St Walk)
            JourneyOption(
                id="J_CA_MIXED",
                journey_key="C->A",
                origin_key="C",
                destination_key="A",
                origin_name=loc_c.name,
                destination_name=loc_a.name,
                primary_mode=TransitMode.MIXED,
                title="Metro to Cubbon Park + Paved Promenade Walk",
                summary="Metro to Cubbon Park Station, followed by an accessible walk through Cubbon Park & Church St.",
                total_duration_minutes=24,
                total_walking_distance_meters=950,
                total_transfers=1,
                estimated_wait_time_minutes=3,
                total_fare_inr=15.0,
                accessibility_score=82.0,
                accessibility_verdict="Good Accessibility (Moderate Walk)",
                accessibility_concerns=[
                    "Requires 950m of walking through park promenade.",
                ],
                recommendation_reasons=[
                    "Combines swift subway transit with a quiet, tree-lined, vehicle-free walking environment.",
                    "Elevator access verified at Cubbon Park exit.",
                ],
                data_provenance={
                    "metro_schedule": "verified_bmrcl_gtfs",
                    "walking_segments": "estimated_walking_speed",
                    "accessibility": "google_street_view_and_survey",
                },
                limitations=[
                    "Cubbon Park gates close to public transit walkers after 20:00 PM.",
                ],
                observations=obs_c_a,
                segments=[
                    RouteSegment(
                        id="CA_MX_1",
                        mode=TransitMode.WALKING,
                        from_name="Majestic Station",
                        to_name="Majestic Metro Platform",
                        from_lat=loc_c.lat,
                        from_lon=loc_c.lon,
                        to_lat=12.975751,
                        to_lon=77.573090,
                        distance_meters=140,
                        duration_minutes=2,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[[loc_c.lat, loc_c.lon], [12.975751, 77.573090]],
                    ),
                    RouteSegment(
                        id="CA_MX_2",
                        mode=TransitMode.METRO,
                        from_name="Majestic (KGWA)",
                        to_name="Cubbon Park (CBPK)",
                        from_lat=12.975751,
                        from_lon=77.573090,
                        to_lat=12.980895,
                        to_lon=77.597565,
                        distance_meters=2750,
                        duration_minutes=6,
                        transit_line="Purple Line",
                        agency="BMRCL",
                        num_intermediate_stops=2,
                        intermediate_stops=["Central College", "Vidhana Soudha"],
                        fare_inr=15.0,
                        headway_minutes=5,
                        data_source="verified_bmrcl_gtfs",
                        wheelchair_accessible=True,
                        polyline=[
                            [12.975751, 77.573090],
                            [12.977500, 77.581500],
                            [12.979800, 77.590500],
                            [12.980895, 77.597565],
                        ],
                    ),
                    RouteSegment(
                        id="CA_MX_3",
                        mode=TransitMode.WALKING,
                        from_name="Cubbon Park Metro Exit",
                        to_name="MG Road Station Entrance A",
                        from_lat=12.980895,
                        from_lon=77.597565,
                        to_lat=loc_a.lat,
                        to_lon=loc_a.lon,
                        distance_meters=810,
                        duration_minutes=11,
                        agency="Pedestrian",
                        data_source="estimated_walking_speed",
                        wheelchair_accessible=True,
                        polyline=[
                            [12.980895, 77.597565],
                            [12.978900, 77.600900],
                            [12.976000, 77.604500],
                            [12.975526, 77.606790],
                        ],
                    ),
                ],
            ),
        ],
    }


ALL_JOURNEY_OPTIONS = _build_journey_options()


def get_journeys_for_direction(origin: str, destination: str) -> List[JourneyOption]:
    """Retrieve all available journey alternatives for a directed pair (e.g. A->B)."""
    key = f"{origin.upper()}->{destination.upper()}"
    return ALL_JOURNEY_OPTIONS.get(key, [])


def get_all_journeys() -> Dict[str, List[JourneyOption]]:
    """Return all journeys across A->B, B->C, and C->A."""
    return ALL_JOURNEY_OPTIONS
