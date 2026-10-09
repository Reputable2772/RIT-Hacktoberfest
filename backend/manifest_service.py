"""Manifest-driven observation loader, validator, and reconciliation service.

Handles:
- Loading and parsing data/street_view_manifest.json (171 planned points).
- Reconciling with the 136 collected screenshots in data/street_view/ (a_to_b, b_to_c, c_to_a).
- Safe image path resolution preventing path traversal.
- Coordinate validation against Bengaluru bounds and route geometry polylines.
- Image usability checks (dimensions, OpenCV decode, brightness, Laplacian blur variance).
- Duplicate image detection (SHA-256) to prevent double-counting.
- Preserving full provenance: route_id, direction, sequence_number, heading, chainage, imagery date, collection status.
- Explicit unassessed handling for the 35 unavailable gap points.
- Backward compatibility for legacy OBS_1–OBS_5 identifiers.
"""

import hashlib
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

from backend.schemas import (
    GemmaVisualAnalysis,
    ObservationCoverageSummary,
    RouteCoverageReport,
    StreetViewObservationItem,
)

logger = logging.getLogger(__name__)

# Canonical bounding box for Bengaluru metropolitan region
BENGALURU_LAT_MIN = 12.85
BENGALURU_LAT_MAX = 13.15
BENGALURU_LON_MIN = 77.40
BENGALURU_LON_MAX = 77.75

# Backward compatibility mapping for legacy demo points
LEGACY_OBS_MAP: Dict[str, str] = {
    "OBS_1": "OBS_A_TO_B_0001",  # MG Road departure (0001.png)
    "OBS_2": "OBS_A_TO_B_0033",  # Kasturba Road connector (0011.png)
    "OBS_3": "OBS_B_TO_C_0001",  # Cubbon Park departure (0001.png)
    "OBS_4": "OBS_B_TO_C_0005",  # Maharani College / Sheshadri Rd (0005.png)
    "OBS_5": "OBS_B_TO_C_0008",  # GPO / Ambedkar Veedhi intersection (0008.png)
}

REVERSE_LEGACY_MAP: Dict[str, str] = {v: k for k, v in LEGACY_OBS_MAP.items()}

ROUTE_METADATA: Dict[str, Dict[str, Any]] = {
    "a_to_b": {
        "name": "MG Road Metro to Cubbon Park Metro",
        "direction": "A -> B",
        "corridor": "A->B",
        "target_spacing_m": 50.0,
    },
    "b_to_c": {
        "name": "Cubbon Park Metro to Majestic Interchange",
        "direction": "B -> C",
        "corridor": "B->C",
        "target_spacing_m": 80.0,
    },
    "c_to_a": {
        "name": "Majestic Interchange to MG Road Metro",
        "direction": "C -> A",
        "corridor": "C->A",
        "target_spacing_m": 90.0,
    },
}


def _point_to_segment_distance_m(
    p_lat: float, p_lon: float, a_lat: float, a_lon: float, b_lat: float, b_lon: float
) -> float:
    """Compute shortest distance in meters from point P to line segment AB using planar projection."""
    x2 = (b_lon - a_lon) * 111320.0 * math.cos(math.radians(a_lat))
    y2 = (b_lat - a_lat) * 110540.0
    xp = (p_lon - a_lon) * 111320.0 * math.cos(math.radians(a_lat))
    yp = (p_lat - a_lat) * 110540.0

    seg_len_sq = x2 * x2 + y2 * y2
    if seg_len_sq <= 1e-9:
        return math.hypot(xp, yp)

    t = max(0.0, min(1.0, (xp * x2 + yp * y2) / seg_len_sq))
    proj_x = t * x2
    proj_y = t * y2
    return math.hypot(xp - proj_x, yp - proj_y)


class ManifestService:
    """Service to load, audit, validate, and serve the 171 manifest observations and 136 images."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        manifest_filename: str = "data/street_view_manifest.json",
    ):
        if base_dir is None:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = base_dir

        self.manifest_path = os.path.join(self.base_dir, manifest_filename)
        self.data_dir = os.path.join(self.base_dir, "data")
        self.street_view_dir = os.path.join(self.data_dir, "street_view")
        self.routes_dir = os.path.join(self.data_dir, "routes")

        self._manifest_data: Optional[Dict[str, Any]] = None
        self._route_geometries: Dict[str, List[Tuple[float, float]]] = {}
        self._audit_results: Optional[Dict[str, Any]] = None
        self._duplicate_pairs: List[Tuple[str, str]] = []

        # Preload data on instantiation
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self._manifest_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load manifest on init: {e}")

        self._preload_route_geometries()

    def _preload_route_geometries(self):
        for route_id in ("a_to_b", "b_to_c", "c_to_a"):
            geom_file = os.path.join(self.routes_dir, route_id, "route_geometry.json")
            if os.path.exists(geom_file):
                try:
                    with open(geom_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        raw_coords = data.get("geometry", {}).get("coordinates", [])
                        coords = [(pt[1], pt[0]) for pt in raw_coords]
                        self._route_geometries[route_id] = coords
                except Exception as e:
                    logger.error(f"Failed to preload geometry for {route_id}: {e}")

    def load_manifest(self) -> Dict[str, Any]:
        """Load manifest from disk or return cached dictionary."""
        if self._manifest_data is not None:
            return self._manifest_data
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self._manifest_data = json.load(f)
                return self._manifest_data
        raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")

    def load_route_geometries(self) -> Dict[str, List[Tuple[float, float]]]:
        """Load GeoJSON LineString coordinates for all 3 routes."""
        if not self._route_geometries:
            self._preload_route_geometries()
        return self._route_geometries

    def resolve_image_path(self, relative_or_filename: str) -> Optional[str]:
        """Safely resolve an image path on disk, strictly preventing path traversal.

        Guarantees that the resulting canonical path resides strictly within the data directory.
        """
        if not relative_or_filename:
            return None

        # Extension whitelist
        ext = os.path.splitext(relative_or_filename)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            return None

        # Reject path traversal tokens
        norm = os.path.normpath(relative_or_filename).lstrip(os.path.sep)
        parts = norm.split(os.path.sep)
        if ".." in parts:
            return None

        real_data_dir = os.path.realpath(self.data_dir)

        # Candidates to check
        candidates = [
            os.path.join(self.base_dir, norm),
            os.path.join(self.street_view_dir, "a_to_b", os.path.basename(norm)),
            os.path.join(self.street_view_dir, "b_to_c", os.path.basename(norm)),
            os.path.join(self.street_view_dir, "c_to_a", os.path.basename(norm)),
            os.path.join(self.data_dir, "observations", os.path.basename(norm)),
        ]

        for cand in candidates:
            real_cand = os.path.realpath(cand)
            if real_cand.startswith(real_data_dir + os.path.sep) and os.path.isfile(real_cand):
                return real_cand

        return None

    def audit_and_reconcile(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Perform comprehensive reconciliation and validation across all 171 manifest points."""
        if self._audit_results is not None and not force_refresh:
            return self._audit_results

        manifest = self.load_manifest()
        geometries = self.load_route_geometries()
        observations = manifest.get("observations", [])

        disk_files: Set[str] = set()
        for r in ("a_to_b", "b_to_c", "c_to_a"):
            r_dir = os.path.join(self.street_view_dir, r)
            if os.path.exists(r_dir):
                for fname in os.listdir(r_dir):
                    if fname.endswith(".png"):
                        disk_files.add(os.path.relpath(os.path.join(r_dir, fname), self.base_dir).replace("\\", "/"))

        manifest_files: Set[str] = set()
        missing_files: List[Dict[str, Any]] = []
        file_to_obs: Dict[str, List[str]] = {}

        collected_count = 0
        unavailable_count = 0
        decoded_images_count = 0
        unusable_images: List[Dict[str, Any]] = []

        out_of_bounds: List[Dict[str, Any]] = []
        swapped_coords: List[Dict[str, Any]] = []
        chainage_anomalies: List[Dict[str, Any]] = []
        geometry_divergences: List[Dict[str, Any]] = []

        hash_to_obs: Dict[str, List[str]] = {}
        route_stats: Dict[str, Dict[str, int]] = {
            "a_to_b": {"planned": 0, "collected": 0, "unavailable": 0},
            "b_to_c": {"planned": 0, "collected": 0, "unavailable": 0},
            "c_to_a": {"planned": 0, "collected": 0, "unavailable": 0},
        }

        prev_obs_by_route: Dict[str, Dict[str, Any]] = {}

        for obs in observations:
            obs_id = obs["observation_id"]
            route_id = obs["route_id"]
            status = obs.get("collection_status")

            route_stats[route_id]["planned"] += 1

            # Bounds & Swapped Coords Check
            lat, lon = obs["latitude"], obs["longitude"]
            if not (BENGALURU_LAT_MIN <= lat <= BENGALURU_LAT_MAX and BENGALURU_LON_MIN <= lon <= BENGALURU_LON_MAX):
                out_of_bounds.append({"obs_id": obs_id, "lat": lat, "lon": lon})
            if 77.0 <= lat <= 78.0 and 12.0 <= lon <= 14.0:
                swapped_coords.append({"obs_id": obs_id, "lat": lat, "lon": lon})

            # Chainage monotonicity check
            dist = obs.get("distance_along_route_m", 0.0)
            if route_id in prev_obs_by_route:
                prev_dist = prev_obs_by_route[route_id].get("distance_along_route_m", 0.0)
                if dist < prev_dist:
                    chainage_anomalies.append({
                        "obs_id": obs_id,
                        "prev_id": prev_obs_by_route[route_id]["observation_id"],
                        "prev_dist": prev_dist,
                        "dist": dist,
                    })
            prev_obs_by_route[route_id] = obs

            # Geometry proximity check
            route_coords = geometries.get(route_id, [])
            if len(route_coords) >= 2:
                min_dist_to_route = float("inf")
                for i in range(len(route_coords) - 1):
                    a_lat, a_lon = route_coords[i]
                    b_lat, b_lon = route_coords[i + 1]
                    d = _point_to_segment_distance_m(lat, lon, a_lat, a_lon, b_lat, b_lon)
                    if d < min_dist_to_route:
                        min_dist_to_route = d
                if min_dist_to_route > 50.0:
                    geometry_divergences.append({
                        "obs_id": obs_id,
                        "route_id": route_id,
                        "distance_m": round(min_dist_to_route, 2),
                    })

            # File verification
            if status == "collected":
                collected_count += 1
                route_stats[route_id]["collected"] += 1
                rel_path = obs.get("relative_path")
                if not rel_path:
                    missing_files.append({"obs_id": obs_id, "error": "Missing relative_path"})
                    continue

                manifest_files.add(rel_path)
                file_to_obs.setdefault(rel_path, []).append(obs_id)

                abs_path = self.resolve_image_path(rel_path)
                if not abs_path or not os.path.exists(abs_path):
                    missing_files.append({"obs_id": obs_id, "path": rel_path})
                    continue

                img = cv2.imread(abs_path)
                if img is None:
                    unusable_images.append({"obs_id": obs_id, "reason": "Failed to decode via OpenCV"})
                    continue

                decoded_images_count += 1
                h, w, c = img.shape
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean_bright = float(np.mean(gray))
                std_bright = float(np.std(gray))
                lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

                is_black = mean_bright < 10.0
                is_white = mean_bright > 245.0
                is_flat = std_bright < 10.0
                is_blurred = lap_var < 20.0

                if is_black or is_white or is_flat or is_blurred:
                    issues = []
                    if is_black:
                        issues.append("black_frame")
                    if is_white:
                        issues.append("white_frame")
                    if is_flat:
                        issues.append("low_contrast")
                    if is_blurred:
                        issues.append("severe_blur")
                    unusable_images.append({
                        "obs_id": obs_id,
                        "path": rel_path,
                        "issues": issues,
                    })

                with open(abs_path, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                hash_to_obs.setdefault(file_hash, []).append(obs_id)

            elif status == "unavailable":
                unavailable_count += 1
                route_stats[route_id]["unavailable"] += 1

        orphaned_files = list(disk_files - manifest_files)
        duplicate_assignments = {k: v for k, v in file_to_obs.items() if len(v) > 1}

        duplicate_pairs: List[Tuple[str, str]] = []
        for file_hash, obs_ids in hash_to_obs.items():
            if len(obs_ids) > 1:
                duplicate_pairs.append((obs_ids[0], obs_ids[1]))
        self._duplicate_pairs = duplicate_pairs

        self._audit_results = {
            "total_observations": len(observations),
            "collected_count": collected_count,
            "unavailable_count": unavailable_count,
            "decoded_images_count": decoded_images_count,
            "unusable_images": unusable_images,
            "missing_files": missing_files,
            "orphaned_files": orphaned_files,
            "duplicate_assignments": duplicate_assignments,
            "duplicate_content_pairs": duplicate_pairs,
            "out_of_bounds": out_of_bounds,
            "swapped_coords": swapped_coords,
            "chainage_anomalies": chainage_anomalies,
            "geometry_divergences": geometry_divergences,
            "route_stats": route_stats,
            "status": "PASS" if len(missing_files) == 0 and len(unusable_images) == 0 else "FAIL",
        }
        return self._audit_results

    def get_duplicate_pairs(self) -> List[Tuple[str, str]]:
        if not self._duplicate_pairs:
            self.audit_and_reconcile()
        return self._duplicate_pairs

    def is_duplicate_observation(self, obs_id_a: str, obs_id_b: str) -> bool:
        pairs = self.get_duplicate_pairs()
        for p1, p2 in pairs:
            if (obs_id_a == p1 and obs_id_b == p2) or (obs_id_a == p2 and obs_id_b == p1):
                return True
        return False

    def get_observations(
        self,
        route_id: Optional[str] = None,
        collection_status: Optional[str] = None,
        legacy_only: bool = False,
        analysis_cache: Optional[Dict[str, GemmaVisualAnalysis]] = None,
    ) -> List[StreetViewObservationItem]:
        """Return list of validated StreetViewObservationItem models with full provenance."""
        manifest = self.load_manifest()
        raw_obs = manifest.get("observations", [])
        results: List[StreetViewObservationItem] = []

        cache = analysis_cache if analysis_cache is not None else {}

        # First, build items for the 171 manifest observations
        manifest_items: List[StreetViewObservationItem] = []
        for obs in raw_obs:
            oid = obs["observation_id"]
            rid = obs["route_id"]
            status = obs.get("collection_status", "unavailable")

            if route_id and rid != route_id:
                continue

            if collection_status and status != collection_status:
                continue

            rel_path = obs.get("relative_path")
            has_file = False
            img_url = None
            if status == "collected" and rel_path:
                import sys
                main_mod = sys.modules.get("backend.main")
                get_img_fn = getattr(main_mod, "get_image_path", None) if main_mod else None
                if not get_img_fn:
                    from backend.planner import get_image_path as get_img_fn
                abs_path = get_img_fn(rel_path)
                has_file = abs_path is not None and os.path.exists(abs_path)
                if has_file:
                    img_url = f"/api/images/{rel_path}"

            analysis_obj = cache.get(oid)
            if not analysis_obj and oid in REVERSE_LEGACY_MAP:
                legacy_id = REVERSE_LEGACY_MAP[oid]
                analysis_obj = cache.get(legacy_id)

            if analysis_obj:
                obs_status = "analysis_completed"
            elif has_file:
                obs_status = "ready_for_analysis"
            else:
                obs_status = "image_uncollected"

            display_name = obs.get("nearest_route_position") or f"Route {rid} Point #{obs['sequence_number']}"
            if oid in REVERSE_LEGACY_MAP:
                display_name = f"{display_name} ({REVERSE_LEGACY_MAP[oid]})"

            item = StreetViewObservationItem(
                id=oid,
                route_id=rid,
                direction=obs.get("direction", ""),
                sequence_number=obs.get("sequence_number", 0),
                image_sequence_number=obs.get("image_sequence_number"),
                name=display_name,
                location=f"{obs.get('nearest_route_position', 'Walking Path')} ({obs.get('direction', '')})",
                lat=obs["latitude"],
                lon=obs["longitude"],
                heading=obs.get("heading_degrees", 0.0),
                distance_along_route_m=obs.get("distance_along_route_m", 0.0),
                nearest_feature=obs.get("nearest_route_position", ""),
                imagery_date=obs.get("imagery_date"),
                image_filename=obs.get("filename"),
                image_url=img_url,
                image_available=has_file,
                collection_status=status,
                unavailable_reason=obs.get("unavailable_reason"),
                status=obs_status,
                analysis=analysis_obj,
                is_usable_evidence=has_file,
                usability_issue=None if has_file else obs.get("unavailable_reason"),
            )
            manifest_items.append(item)

        if legacy_only:
            # Return only the 5 legacy demo mapped items with their legacy IDs
            legacy_items = []
            for leg_id, canon_id in LEGACY_OBS_MAP.items():
                match = next((item for item in manifest_items if item.id == canon_id), None)
                if match:
                    item_copy = match.model_copy()
                    item_copy.id = leg_id
                    legacy_items.append(item_copy)
            return legacy_items

        # Build legacy alias items for backward compatibility when not filtered by route
        if not route_id and not collection_status:
            import sys
            main_mod = sys.modules.get("backend.main")
            get_img_fn = getattr(main_mod, "get_image_path", None) if main_mod else None
            if not get_img_fn:
                from backend.planner import get_image_path as get_img_fn
            from backend.planner import PREPARED_IMAGES_MAP

            legacy_aliases: List[StreetViewObservationItem] = []
            for leg_id, canon_id in LEGACY_OBS_MAP.items():
                match = next((item for item in manifest_items if item.id == canon_id), None)
                if match:
                    item_copy = match.model_copy()
                    item_copy.id = leg_id
                    legacy_fname = PREPARED_IMAGES_MAP.get(leg_id, {}).get("filename", "")
                    legacy_path = get_img_fn(legacy_fname)
                    has_leg_file = legacy_path is not None and os.path.exists(legacy_path)
                    item_copy.image_available = has_leg_file
                    if leg_id in cache:
                        item_copy.analysis = cache[leg_id]
                        item_copy.status = "analysis_completed"
                    elif has_leg_file:
                        item_copy.status = "ready_for_analysis"
                    else:
                        item_copy.status = "image_uncollected"
                    legacy_aliases.append(item_copy)
            return manifest_items + legacy_aliases

        return manifest_items

    def get_observation_by_id(
        self,
        obs_id: str,
        analysis_cache: Optional[Dict[str, GemmaVisualAnalysis]] = None,
    ) -> Optional[StreetViewObservationItem]:
        """Fetch a single observation by either its canonical manifest ID or legacy OBS_1–5 ID."""
        canonical_id = LEGACY_OBS_MAP.get(obs_id, obs_id)
        all_obs = self.get_observations(analysis_cache=analysis_cache)
        for o in all_obs:
            if o.id == obs_id or o.id == canonical_id:
                return o
        return None

    def get_route_coverage_reports(
        self, analysis_cache: Optional[Dict[str, GemmaVisualAnalysis]] = None
    ) -> Dict[str, RouteCoverageReport]:
        """Return structured RouteCoverageReport models for all 3 walking routes."""
        reports: Dict[str, RouteCoverageReport] = {}
        # Only take the manifest items (avoid legacy duplicate counting)
        manifest = self.load_manifest()
        raw_obs = manifest.get("observations", [])

        all_obs = self.get_observations(analysis_cache=analysis_cache)
        manifest_obs = [o for o in all_obs if o.id.startswith("OBS_A_") or o.id.startswith("OBS_B_") or o.id.startswith("OBS_C_")]

        for route_id, meta in ROUTE_METADATA.items():
            r_obs = [o for o in manifest_obs if o.route_id == route_id]
            coll = sum(1 for o in r_obs if o.collection_status == "collected")
            unav = sum(1 for o in r_obs if o.collection_status == "unavailable")
            analyzed = sum(1 for o in r_obs if o.status == "analysis_completed")
            usable = sum(1 for o in r_obs if o.is_usable_evidence)

            max_dist = max((o.distance_along_route_m for o in r_obs), default=0.0)

            reports[route_id] = RouteCoverageReport(
                route_id=route_id,
                direction=meta["direction"],
                name=meta["name"],
                distance_meters=round(max_dist, 1),
                target_spacing_meters=meta["target_spacing_m"],
                total_planned=len(r_obs),
                collected_count=coll,
                unavailable_count=unav,
                analyzed_count=analyzed,
                usable_evidence_count=usable,
                image_directory=f"data/street_view/{route_id}",
            )

        return reports

    def get_overall_summary(
        self, analysis_cache: Optional[Dict[str, GemmaVisualAnalysis]] = None
    ) -> ObservationCoverageSummary:
        """Return high-level summary across all 171 observations."""
        reports = self.get_route_coverage_reports(analysis_cache=analysis_cache)
        total_planned = sum(r.total_planned for r in reports.values())
        collected = sum(r.collected_count for r in reports.values())
        unavailable = sum(r.unavailable_count for r in reports.values())
        analyzed = sum(r.analyzed_count for r in reports.values())

        return ObservationCoverageSummary(
            total_planned=total_planned,
            collected=collected,
            unavailable=unavailable,
            analyzed=analyzed,
        )


manifest_service = ManifestService()
