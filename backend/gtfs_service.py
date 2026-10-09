"""GTFS service for querying BMRCL (Metro) and BMTC (Bus) transit feeds.

Reads directly from data/gtfs/bmrcl.zip and data/gtfs/bmtc.zip to provide
genuine stop metadata, coordinates, and spatial stop matching for Bengaluru.
"""

import csv
import io
import math
import os
import zipfile
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BMRCL_ZIP_PATH = os.path.join(BASE_DIR, "data", "gtfs", "bmrcl.zip")
BMTC_ZIP_PATH = os.path.join(BASE_DIR, "data", "gtfs", "bmtc.zip")


class GTFSStop(BaseModel):
    stop_id: str
    stop_name: str
    lat: float
    lon: float
    agency: str = "BMTC"
    distance_meters: Optional[int] = None


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


class GTFSIndex:
    """In-memory cache for quick spatial stop lookups from GTFS feeds."""

    def __init__(self):
        self._bmrcl_stops: List[GTFSStop] = []
        self._bmtc_stops: List[GTFSStop] = []
        self._loaded: bool = False

    def load_if_needed(self):
        """Lazily load stops from zip archives into memory."""
        if self._loaded:
            return

        # Load BMRCL Metro stops
        if os.path.exists(BMRCL_ZIP_PATH):
            try:
                with zipfile.ZipFile(BMRCL_ZIP_PATH) as z:
                    if "stops.txt" in z.namelist():
                        with z.open("stops.txt") as f:
                            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                            for row in reader:
                                lat = row.get("stop_lat")
                                lon = row.get("stop_lon")
                                if lat and lon:
                                    self._bmrcl_stops.append(
                                        GTFSStop(
                                            stop_id=row["stop_id"],
                                            stop_name=row.get("stop_name", "Metro Station"),
                                            lat=float(lat),
                                            lon=float(lon),
                                            agency="BMRCL",
                                        )
                                    )
            except Exception as e:
                print(f"Warning: Failed to load BMRCL GTFS: {e}")

        # Load BMTC Bus stops
        if os.path.exists(BMTC_ZIP_PATH):
            try:
                with zipfile.ZipFile(BMTC_ZIP_PATH) as z:
                    if "stops.txt" in z.namelist():
                        with z.open("stops.txt") as f:
                            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                            for row in reader:
                                lat = row.get("stop_lat")
                                lon = row.get("stop_lon")
                                if lat and lon:
                                    self._bmtc_stops.append(
                                        GTFSStop(
                                            stop_id=row["stop_id"],
                                            stop_name=row.get("stop_name", "Bus Stop"),
                                            lat=float(lat),
                                            lon=float(lon),
                                            agency="BMTC",
                                        )
                                    )
            except Exception as e:
                print(f"Warning: Failed to load BMTC GTFS: {e}")

        self._loaded = True

    @property
    def bmtc_stops_count(self) -> int:
        self.load_if_needed()
        return len(self._bmtc_stops)

    @property
    def bmrcl_stops_count(self) -> int:
        self.load_if_needed()
        return len(self._bmrcl_stops)

    def find_nearest_bmtc_stops(
        self, lat: float, lon: float, limit: int = 3
    ) -> List[GTFSStop]:
        """Find the closest genuine BMTC bus stops to a coordinate."""
        self.load_if_needed()
        if not self._bmtc_stops:
            return []

        scored = []
        for s in self._bmtc_stops:
            dist = haversine_distance_meters(lat, lon, s.lat, s.lon)
            scored.append((dist, s))

        scored.sort(key=lambda x: x[0])
        results = []
        for dist, s in scored[:limit]:
            item = s.model_copy()
            item.distance_meters = dist
            results.append(item)
        return results

    def find_nearest_bmrcl_stations(
        self, lat: float, lon: float, limit: int = 3
    ) -> List[GTFSStop]:
        """Find the closest genuine BMRCL metro stations to a coordinate."""
        self.load_if_needed()
        if not self._bmrcl_stops:
            return []

        scored = []
        for s in self._bmrcl_stops:
            dist = haversine_distance_meters(lat, lon, s.lat, s.lon)
            scored.append((dist, s))

        scored.sort(key=lambda x: x[0])
        results = []
        for dist, s in scored[:limit]:
            item = s.model_copy()
            item.distance_meters = dist
            results.append(item)
        return results


# Global singleton
gtfs_index = GTFSIndex()
