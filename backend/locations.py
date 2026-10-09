"""Canonical configuration for fixed demo locations in Bengaluru.

All components MUST import canonical coordinates and metadata from this module
to avoid independent coordinate drift or hardcoding.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DemoLocation(BaseModel):
    id: str = Field(..., description="Short identifier (LOC_A, LOC_B, LOC_C)")
    key: str = Field(..., description="Key letter ('A', 'B', 'C')")
    name: str = Field(..., description="Display name")
    short_name: str = Field(..., description="Abbreviated label for cards/badges")
    canonical_name: str = Field(..., description="Full verified address/place name")
    lat: float = Field(..., description="WGS84 latitude")
    lon: float = Field(..., description="WGS84 longitude")
    place_ref: str = Field(..., description="Canonical agency/OSM place reference")
    osm_ref: str = Field(..., description="OpenStreetMap node reference")
    description: str = Field(..., description="Contextual description")
    accessible_entrances: List[str] = Field(
        default_factory=list,
        description="List of verified accessible station entrance IDs",
    )


# Canonical verified coordinates from official BMRCL GTFS / OpenStreetMap
FIXED_LOCATIONS: Dict[str, DemoLocation] = {
    "A": DemoLocation(
        id="LOC_A",
        key="A",
        name="MG Road Metro Station",
        short_name="MG Road (A)",
        canonical_name="MG Road Metro Station, Mahatma Gandhi Road, Ashok Nagar, Bengaluru",
        lat=12.975526,
        lon=77.606790,
        place_ref="BMRCL:MAGR",
        osm_ref="node/MG_Road_Metro",
        description="MG Road / Church Street commercial pedestrian precinct; BMRCL Purple Line Station.",
        accessible_entrances=["MAGR_A", "MAGR_B", "MAGR_C", "MAGR_D"],
    ),
    "B": DemoLocation(
        id="LOC_B",
        key="B",
        name="Cubbon Park Metro Station",
        short_name="Cubbon Park (B)",
        canonical_name="Cubbon Park Metro Station, Kasturba Road, Bengaluru",
        lat=12.980958,
        lon=77.597570,
        place_ref="BMRCL:CBPK",
        osm_ref="node/Cubbon_Park_Metro",
        description="Kasturba Road / Cubbon Park recreational and government precinct; BMRCL Purple Line Station.",
        accessible_entrances=["CBPK_A", "CBPK_B", "CBPK_D"],
    ),
    "C": DemoLocation(
        id="LOC_C",
        key="C",
        name="Nadaprabhu Kempegowda Station, Majestic",
        short_name="Majestic (C)",
        canonical_name="Nadaprabhu Kempegowda Station Majestic / Kempegowda Bus Station (KBS), Bengaluru",
        lat=12.975708,
        lon=77.572876,
        place_ref="BMRCL:KGWA",
        osm_ref="node/Majestic_Interchange",
        description="Central transit interchange connecting BMRCL Purple/Green lines and BMTC bus terminals.",
        accessible_entrances=["KGWA_A", "KGWA_B", "KGWA_C", "KGWA_D", "KGWA_E"],
    ),
}


def get_location(key: str) -> DemoLocation:
    """Retrieve fixed demo location by key ('A', 'B', or 'C')."""
    normalized = key.upper().strip()
    if normalized not in FIXED_LOCATIONS:
        raise KeyError(f"Unknown demo location '{key}'. Valid options are 'A', 'B', 'C'.")
    return FIXED_LOCATIONS[normalized]


def get_all_locations() -> List[DemoLocation]:
    """Return all fixed demo locations in sequence."""
    return [FIXED_LOCATIONS["A"], FIXED_LOCATIONS["B"], FIXED_LOCATIONS["C"]]
