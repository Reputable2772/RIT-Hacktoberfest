#!/usr/bin/env python3
"""Automated Street View screenshot collection along pedestrian walking routes.

Captures actual browser screenshots using the Google Chrome browser agent via CDP.
Strictly collects screenshots and metadata; does NOT perform image analysis,
accessibility labelling, or Gemma inference.
"""

import asyncio
import base64
import json
import math
import os
import re
import sys
import time
import urllib.request
import cv2
import websockets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROUTES_DIR = os.path.join(DATA_DIR, "routes")
STREET_VIEW_DIR = os.path.join(DATA_DIR, "street_view")
MANIFEST_PATH = os.path.join(DATA_DIR, "street_view_manifest.json")


def haversine(c1, c2):
    """Distance in meters between two [lon, lat] coordinates."""
    R = 6371000
    lat1, lon1 = math.radians(c1[1]), math.radians(c1[0])
    lat2, lon2 = math.radians(c2[1]), math.radians(c2[0])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * R * math.asin(math.sqrt(a))


def bearing(c1, c2):
    """Initial bearing in degrees from c1 to c2."""
    lat1, lon1 = math.radians(c1[1]), math.radians(c1[0])
    lat2, lon2 = math.radians(c2[1]), math.radians(c2[0])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    b = math.degrees(math.atan2(y, x))
    return round((b + 360.0) % 360.0, 1)


def sample_route_points(route_data, target_step_m=50.0):
    """Generate ordered observation points along the route geometry."""
    coords = route_data["geometry"]["coordinates"]  # list of [lon, lat]
    steps = route_data.get("steps", [])

    # Collect key step positions
    step_locations = []
    for s in steps:
        man = s.get("maneuver", {})
        if "location" in man:
            step_locations.append({
                "loc": man["location"],
                "name": s.get("name", "road"),
                "type": man.get("type", "maneuver"),
                "modifier": man.get("modifier", "")
            })

    samples = []
    # Point 0
    init_heading = bearing(coords[0], coords[1]) if len(coords) > 1 else 0.0
    samples.append({
        "lat": round(coords[0][1], 6),
        "lon": round(coords[0][0], 6),
        "distance_along_route_m": 0.0,
        "heading": init_heading,
        "nearest_feature": "Route Origin / Departure"
    })

    accum_dist = 0.0
    last_sample_dist = 0.0

    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        seg_dist = haversine(p1, p2)
        if seg_dist == 0:
            continue
        seg_heading = bearing(p1, p2)

        while (accum_dist + seg_dist - last_sample_dist) >= target_step_m:
            frac = (last_sample_dist + target_step_m - accum_dist) / seg_dist
            if frac > 1.0:
                break
            interp_lon = p1[0] + frac * (p2[0] - p1[0])
            interp_lat = p1[1] + frac * (p2[1] - p1[1])
            last_sample_dist += target_step_m
            samples.append({
                "lat": round(interp_lat, 6),
                "lon": round(interp_lon, 6),
                "distance_along_route_m": round(last_sample_dist, 1),
                "heading": seg_heading,
                "nearest_feature": f"Pedestrian path (~{int(last_sample_dist)}m from origin)"
            })

        accum_dist += seg_dist

    # Destination point
    dest = coords[-1]
    last_h = samples[-1]["heading"] if samples else 0.0
    samples.append({
        "lat": round(dest[1], 6),
        "lon": round(dest[0], 6),
        "distance_along_route_m": round(accum_dist, 1),
        "heading": last_h,
        "nearest_feature": "Route Destination / Arrival"
    })

    return samples


def get_chrome_ws_url():
    """Discover Chrome remote debugging WebSocket URL."""
    res = urllib.request.urlopen("http://localhost:9222/json").read()
    tabs = json.loads(res.decode())
    # Prefer existing Google Maps tab
    maps_tab = next((t for t in tabs if t.get("type") == "page" and "google.com/maps" in t.get("url", "")), None)
    if maps_tab:
        return maps_tab["webSocketDebuggerUrl"]
    page_tab = next((t for t in tabs if t.get("type") == "page"), None)
    if page_tab:
        return page_tab["webSocketDebuggerUrl"]
    raise RuntimeError("No active browser page tab found on http://localhost:9222")


async def run_collection():
    print("=" * 70)
    print("STARTING STREET VIEW SCREENSHOT COLLECTION WORKFLOW")
    print("=" * 70)

    ws_url = get_chrome_ws_url()
    print(f"Connected to Chrome CDP WebSocket: {ws_url}")

    route_configs = [
        {
            "route_id": "a_to_b",
            "direction": "A -> B",
            "name": "MG Road Metro Station to Cubbon Park Metro Station",
            "geom_file": os.path.join(ROUTES_DIR, "a_to_b", "route_geometry.json"),
            "img_dir": os.path.join(STREET_VIEW_DIR, "a_to_b"),
            "target_spacing_m": 50.0,
        },
        {
            "route_id": "b_to_c",
            "direction": "B -> C",
            "name": "Cubbon Park Metro Station to Nadaprabhu Kempegowda Station Majestic",
            "geom_file": os.path.join(ROUTES_DIR, "b_to_c", "route_geometry.json"),
            "img_dir": os.path.join(STREET_VIEW_DIR, "b_to_c"),
            "target_spacing_m": 80.0,
        },
        {
            "route_id": "c_to_a",
            "direction": "C -> A",
            "name": "Nadaprabhu Kempegowda Station Majestic to MG Road Metro Station",
            "geom_file": os.path.join(ROUTES_DIR, "c_to_a", "route_geometry.json"),
            "img_dir": os.path.join(STREET_VIEW_DIR, "c_to_a"),
            "target_spacing_m": 90.0,
        },
    ]

    manifest = {
        "collection_title": "Bengaluru Metro Pedestrian Corridors Street View Evidence",
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "collection_agent": "Antigravity Chrome Browser Agent via CDP",
        "policy_notice": "Google Street View imagery captured for pedestrian accessibility documentation. All rights reserved by Google LLC and imagery contributors. Strictly un-analyzed collection.",
        "routes": {},
        "total_observations_planned": 0,
        "total_screenshots_saved": 0,
        "total_uncovered_observations": 0,
        "observations": []
    }

    async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
        msg_id = 1

        async def cdp_call(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            payload = {"id": cid, "method": method}
            if params:
                payload["params"] = params
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        for rc in route_configs:
            route_id = rc["route_id"]
            os.makedirs(rc["img_dir"], exist_ok=True)
            with open(rc["geom_file"], "r") as f:
                route_data = json.load(f)

            planned_points = sample_route_points(route_data, target_step_m=rc["target_spacing_m"])
            print(f"\n--- Processing Route {route_id} ({rc['direction']}) ---")
            print(f"Total distance: {route_data['distance_meters']:.1f}m | Planned observations: {len(planned_points)}")

            route_manifest_info = {
                "route_id": route_id,
                "direction": rc["direction"],
                "name": rc["name"],
                "distance_meters": route_data["distance_meters"],
                "duration_seconds": route_data["duration_seconds"],
                "target_spacing_meters": rc["target_spacing_m"],
                "total_planned": len(planned_points),
                "collected_count": 0,
                "unavailable_count": 0,
                "image_directory": f"data/street_view/{route_id}/",
                "observations": []
            }

            for idx, pt in enumerate(planned_points):
                seq_num = idx + 1
                obs_id = f"OBS_{route_id.upper()}_{seq_num:04d}"
                filename = f"{seq_num:04d}.png"
                img_path = os.path.join(rc["img_dir"], filename)

                t0 = time.time()
                sv_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={pt['lat']},{pt['lon']}&heading={pt['heading']}"

                # Navigate
                await cdp_call("Page.navigate", {"url": sv_url})
                await asyncio.sleep(2.5)

                # DOM inspection, cleanup toasts, and latest date selection
                cleanup_and_check = """
                (() => {
                    // Remove lingering toast notifications
                    const toasts = Array.from(document.querySelectorAll('div, span')).filter(el =>
                        el.innerText && el.innerText.includes('No Street View imagery available here') && el.children.length <= 2
                    );
                    for (const t of toasts) {
                        try { t.remove(); } catch(e) {}
                    }

                    // Check if current view is genuinely unavailable
                    const bodyText = document.body.innerText || '';
                    if (bodyText.includes('No Street View imagery available here')) {
                        return { available: false, reason: 'no_coverage' };
                    }

                    // Check if 'See latest date' is directly present
                    const all = Array.from(document.querySelectorAll('*'));
                    const seeLatest = all.find(el => el.children.length === 0 && el.innerText && el.innerText.trim() === 'See latest date');
                    if (seeLatest) {
                        try { seeLatest.click(); } catch(e) {}
                    } else {
                        // Or open 'See more dates'
                        const moreBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('See more dates'));
                        if (moreBtn) {
                            try { moreBtn.click(); } catch(e) {}
                        }
                    }

                    return { available: true };
                })()
                """
                eval1 = await cdp_call("Runtime.evaluate", {"expression": cleanup_and_check, "returnByValue": True})
                check_res = eval1.get("result", {}).get("value", {})

                capture_date = None
                pano_id = None
                actual_status = "unavailable"
                unavail_reason = None

                if check_res.get("available"):
                    # Wait briefly for date update
                    await asyncio.sleep(0.7)

                    # Select leaf if 'See latest date' popped up
                    pick_latest_leaf = """
                    (() => {
                        const all = Array.from(document.querySelectorAll('*'));
                        const seeLatest = all.find(el => el.children.length === 0 && el.innerText && el.innerText.trim() === 'See latest date');
                        if (seeLatest) {
                            try { seeLatest.click(); } catch(e) {}
                            return true;
                        }
                        return false;
                    })()
                    """
                    await cdp_call("Runtime.evaluate", {"expression": pick_latest_leaf, "returnByValue": True})
                    await asyncio.sleep(0.5)

                    # Read current URL and capture date
                    extract_meta = """
                    (() => {
                        let date = null;
                        const dateEl = Array.from(document.querySelectorAll('span, div')).find(el => /Image capture:/.test(el.innerText || ''));
                        if (dateEl) {
                            const m = dateEl.innerText.match(/Image capture:\\s*([A-Za-z]+\\s+\\d{4}|\\d{4})/);
                            if (m) date = m[1];
                        }
                        if (!date) {
                            const dateCard = Array.from(document.querySelectorAll('div, span')).find(el => /\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{4}\\b/.test(el.innerText || ''));
                            if (dateCard) {
                                const m = dateCard.innerText.match(/\\b([A-Za-z]{3}\\s+\\d{4})\\b/);
                                if (m) date = m[1];
                            }
                        }
                        return {
                            url: window.location.href,
                            date: date
                        };
                    })()
                    """
                    meta_eval = await cdp_call("Runtime.evaluate", {"expression": extract_meta, "returnByValue": True})
                    meta_val = meta_eval.get("result", {}).get("value", {})
                    capture_date = meta_val.get("date")

                    curr_url = meta_val.get("url", "")
                    # Extract pano ID from URL
                    pano_match = re.search(r"!1s([^!]+)!2e0", curr_url)
                    if pano_match:
                        pano_id = pano_match.group(1)
                    else:
                        pano_q = re.search(r"panoid=([^&]+)", curr_url)
                        if pano_q:
                            pano_id = pano_q.group(1)

                    # Capture actual screenshot via CDP
                    snap = await cdp_call("Page.captureScreenshot", {"format": "png"})
                    img_bytes = base64.b64decode(snap.get("data", ""))

                    if len(img_bytes) > 20000:
                        with open(img_path, "wb") as f:
                            f.write(img_bytes)
                        actual_status = "collected"
                    else:
                        actual_status = "unavailable"
                        unavail_reason = "Screenshot image payload too small (black/empty frame)"
                else:
                    actual_status = "unavailable"
                    unavail_reason = "No Street View coverage available near this coordinate"

                if actual_status == "collected":
                    route_manifest_info["collected_count"] += 1
                    manifest["total_screenshots_saved"] += 1
                else:
                    route_manifest_info["unavailable_count"] += 1
                    manifest["total_uncovered_observations"] += 1

                obs_entry = {
                    "observation_id": obs_id,
                    "route_id": route_id,
                    "direction": rc["direction"],
                    "sequence_number": seq_num,
                    "filename": filename if actual_status == "collected" else None,
                    "relative_path": f"data/street_view/{route_id}/{filename}" if actual_status == "collected" else None,
                    "latitude": pt["lat"],
                    "longitude": pt["lon"],
                    "heading_degrees": pt["heading"],
                    "distance_along_route_m": pt["distance_along_route_m"],
                    "nearest_route_position": pt["nearest_feature"],
                    "imagery_date": capture_date,
                    "panorama_reference": pano_id,
                    "collection_status": actual_status,
                    "storage_and_reuse_permissions": "google_street_view_browser_capture_local_research_only",
                    "unavailable_reason": unavail_reason
                }

                route_manifest_info["observations"].append(obs_entry)
                manifest["observations"].append(obs_entry)

                elapsed = time.time() - t0
                date_str = capture_date if capture_date else "default"
                print(f"[{route_id.upper()} {seq_num:04d}/{len(planned_points):04d}] {actual_status.upper():11s} | Date: {date_str:10s} | {pt['distance_along_route_m']:6.1f}m | {elapsed:4.2f}s | {pt['nearest_feature']}")

            manifest["total_observations_planned"] += len(planned_points)
            manifest["routes"][route_id] = route_manifest_info

    # Save manifest
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest successfully saved to {MANIFEST_PATH}")

    # Post-collection verification
    print("\n" + "=" * 70)
    print("RUNNING POST-COLLECTION FILE VERIFICATION")
    print("=" * 70)

    total_valid = 0
    total_failed = 0

    for obs in manifest["observations"]:
        if obs["collection_status"] == "collected":
            fpath = os.path.join(BASE_DIR, obs["relative_path"])
            if not os.path.exists(fpath):
                print(f"ERROR: File missing {fpath}")
                total_failed += 1
                continue
            img = cv2.imread(fpath)
            if img is None:
                print(f"ERROR: Corrupt image {fpath}")
                total_failed += 1
                continue
            h, w, c = img.shape
            if h < 100 or w < 100:
                print(f"ERROR: Abnormal dimensions ({w}x{h}) {fpath}")
                total_failed += 1
                continue
            total_valid += 1

    print(f"Verified files: {total_valid} valid images successfully read by OpenCV.")
    print(f"Failed files: {total_failed}")
    print(f"Total collected: {manifest['total_screenshots_saved']}")
    print(f"Total uncovered/unavailable: {manifest['total_uncovered_observations']}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_collection())
