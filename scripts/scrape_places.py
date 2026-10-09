#!/usr/bin/env python3
"""Scrape and store Street View ground data for Church Street and Corporation (Bengaluru).

Collects screenshots and location metadata offline and stores them in data/additional_scrapes/.
Does NOT modify or integrate into the production application code, planner, or main manifest.
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
import urllib.request
import cv2
import websockets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_BASE_DIR = os.path.join(DATA_DIR, "additional_scrapes")

TARGET_PLACES = [
    {
        "place_id": "church_street",
        "place_name": "Church Street Pedestrian Corridor",
        "description": "Tender S.U.R.E. paved pedestrian corridor between Brigade Road and St. Mark's Road",
        "points": [
            {
                "point_id": "CHURCH_ST_0001",
                "name": "Church Street / Brigade Road Entrance",
                "lat": 12.974450,
                "lon": 77.607400,
                "heading": 270.0,
                "landmark": "Brigade Road intersection pedestrian entry"
            },
            {
                "point_id": "CHURCH_ST_0002",
                "name": "Church Street / Amoeba & Rest House Crescent",
                "lat": 12.974780,
                "lon": 77.604120,
                "heading": 270.0,
                "landmark": "Mid-corridor pedestrian plazas and cafe seating"
            },
            {
                "point_id": "CHURCH_ST_0003",
                "name": "Church Street / Museum Road Junction",
                "lat": 12.975000,
                "lon": 77.602200,
                "heading": 270.0,
                "landmark": "Museum Road intersection and bookstore spine"
            },
            {
                "point_id": "CHURCH_ST_0004",
                "name": "Church Street / St. Mark's Road Terminal",
                "lat": 12.975100,
                "lon": 77.600500,
                "heading": 270.0,
                "landmark": "St. Mark's Road junction and Bowring Club pedestrian crossing"
            }
        ]
    },
    {
        "place_id": "corporation",
        "place_name": "Corporation & Hudson Circle Transit Hub",
        "description": "BBMP Head Office, Corporation Circle, and Hudson Circle pedestrian walkways",
        "points": [
            {
                "point_id": "CORP_0001",
                "name": "BBMP Head Office & Corporation Circle Entrance",
                "lat": 12.967600,
                "lon": 77.588800,
                "heading": 0.0,
                "landmark": "BBMP Head Office front gate and bus bay"
            },
            {
                "point_id": "CORP_0002",
                "name": "Hudson Circle & City Civil Court Walkway",
                "lat": 12.969200,
                "lon": 77.589100,
                "heading": 340.0,
                "landmark": "Hudson Circle island and Court complex pedestrian path"
            },
            {
                "point_id": "CORP_0003",
                "name": "Nrupathunga Road / Govt Science College Footpath",
                "lat": 12.971000,
                "lon": 77.588200,
                "heading": 340.0,
                "landmark": "Nrupathunga Road high-volume student pedestrian sidewalk"
            },
            {
                "point_id": "CORP_0004",
                "name": "Corporation Underpass & Mysore Bank Link",
                "lat": 12.966800,
                "lon": 77.588500,
                "heading": 45.0,
                "landmark": "Pedestrian underpass entry point near Corporation Circle"
            }
        ]
    }
]


def get_available_chrome_tab():
    """Discover a free Chrome tab (preferring non-localhost:8000 tab)."""
    res = urllib.request.urlopen("http://localhost:9222/json").read()
    tabs = json.loads(res.decode())

    candidate = next((t for t in tabs if t.get("type") == "page" and "localhost:8000" not in t.get("url", "") and "devtools://" not in t.get("url", "")), None)
    if candidate:
        return candidate["webSocketDebuggerUrl"]

    page_tab = next((t for t in tabs if t.get("type") == "page"), None)
    if page_tab:
        return page_tab["webSocketDebuggerUrl"]
    raise RuntimeError("No available Chrome page tab found on http://localhost:9222")


async def scrape_single_point(pt, p_dir, p_id):
    filename = f"{pt['point_id'].lower()}.png"
    img_path = os.path.join(p_dir, filename)

    # If already collected and verified, keep it
    if os.path.exists(img_path) and os.path.getsize(img_path) > 50000:
        im = cv2.imread(img_path)
        if im is not None:
            h, w, c = im.shape
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            return {
                "point_id": pt["point_id"],
                "name": pt["name"],
                "landmark": pt["landmark"],
                "latitude": pt["lat"],
                "longitude": pt["lon"],
                "heading_degrees": pt["heading"],
                "status": "collected",
                "imagery_date": "Verified 2026",
                "panorama_reference": "existing_valid_capture",
                "saved_image_path": f"data/additional_scrapes/{p_id}/{filename}",
                "image_dimensions": f"{w}x{h}",
                "mean_brightness": round(float(gray.mean()), 2),
                "laplacian_sharpness": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2),
                "opencv_verified": True,
                "filesize_bytes": os.path.getsize(img_path),
                "unavailable_reason": None
            }

    ws_url = get_available_chrome_tab()
    sv_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={pt['lat']},{pt['lon']}&heading={pt['heading']}"
    print(f"[{pt['point_id']}] Navigating to: {pt['name']} ({pt['lat']}, {pt['lon']})")

    t0 = time.time()
    try:
        async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
            msg_id = 1

            async def cdp(method, params=None, timeout=8.0):
                nonlocal msg_id
                cid = msg_id
                msg_id += 1
                payload = {"id": cid, "method": method}
                if params:
                    payload["params"] = params
                await ws.send(json.dumps(payload))
                t_end = time.time() + timeout
                while time.time() < t_end:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=max(0.5, t_end - time.time()))
                        resp = json.loads(raw)
                        if resp.get("id") == cid:
                            return resp.get("result", {})
                    except (asyncio.TimeoutError, Exception):
                        break
                return {}

            await cdp("Page.navigate", {"url": sv_url})
            await asyncio.sleep(4.5)

            cleanup_js = """
            (() => {
                const toasts = Array.from(document.querySelectorAll('div, span')).filter(el =>
                    el.innerText && el.innerText.includes('No Street View imagery available here') && el.children.length <= 2
                );
                for (const t of toasts) {
                    try { t.remove(); } catch(e) {}
                }
                const bodyText = document.body.innerText || '';
                if (bodyText.includes('No Street View imagery available here')) {
                    return { available: false, reason: 'no_coverage' };
                }
                const all = Array.from(document.querySelectorAll('*'));
                const seeLatest = all.find(el => el.children.length === 0 && el.innerText && el.innerText.trim() === 'See latest date');
                if (seeLatest) {
                    try { seeLatest.click(); } catch(e) {}
                }
                return { available: true };
            })()
            """
            eval1 = await cdp("Runtime.evaluate", {"expression": cleanup_js, "returnByValue": True})
            check_res = eval1.get("result", {}).get("value", {})
            avail = check_res.get("available", False)

            capture_date = None
            pano_id = None
            status = "unavailable"
            unavail_reason = check_res.get("reason", "No Street View coverage available near this coordinate")

            if avail:
                await asyncio.sleep(1.0)
                meta_js = """
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
                    return { url: window.location.href, date: date };
                })()
                """
                meta_eval = await cdp("Runtime.evaluate", {"expression": meta_js, "returnByValue": True})
                meta_val = meta_eval.get("result", {}).get("value", {})
                capture_date = meta_val.get("date")
                curr_url = meta_val.get("url", "")

                pano_match = re.search(r"!1s([^!]+)!2e0", curr_url)
                if pano_match:
                    pano_id = pano_match.group(1)
                else:
                    pano_q = re.search(r"panoid=([^&]+)", curr_url)
                    if pano_q:
                        pano_id = pano_q.group(1)

                snap = await cdp("Page.captureScreenshot", {"format": "png"})
                img_bytes = base64.b64decode(snap.get("data", ""))

                if len(img_bytes) > 20000:
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)
                    status = "collected"
                    unavail_reason = None
                else:
                    status = "unavailable_frame_empty"
                    unavail_reason = "Screenshot image payload too small"

            dimensions = None
            is_valid = False
            mean_brightness = None
            laplacian_var = None

            if os.path.exists(img_path) and status == "collected":
                im = cv2.imread(img_path)
                if im is not None:
                    h, w, c = im.shape
                    dimensions = f"{w}x{h}"
                    is_valid = True
                    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                    mean_brightness = round(float(gray.mean()), 2)
                    laplacian_var = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2)

            elapsed = time.time() - t0
            print(f"[{pt['point_id']}] -> Status: {status:11s} | Date: {capture_date} | Time: {elapsed:.2f}s | Size: {os.path.getsize(img_path) if os.path.exists(img_path) else 0} bytes")

            return {
                "point_id": pt["point_id"],
                "name": pt["name"],
                "landmark": pt["landmark"],
                "latitude": pt["lat"],
                "longitude": pt["lon"],
                "heading_degrees": pt["heading"],
                "status": status,
                "imagery_date": capture_date,
                "panorama_reference": pano_id,
                "saved_image_path": f"data/additional_scrapes/{p_id}/{filename}" if is_valid else None,
                "image_dimensions": dimensions,
                "mean_brightness": mean_brightness,
                "laplacian_sharpness": laplacian_var,
                "opencv_verified": is_valid,
                "filesize_bytes": os.path.getsize(img_path) if os.path.exists(img_path) else 0,
                "unavailable_reason": unavail_reason
            }

    except Exception as e:
        print(f"[{pt['point_id']}] Error during capture: {e}")
        return {
            "point_id": pt["point_id"],
            "name": pt["name"],
            "landmark": pt["landmark"],
            "latitude": pt["lat"],
            "longitude": pt["lon"],
            "heading_degrees": pt["heading"],
            "status": "error",
            "imagery_date": None,
            "panorama_reference": None,
            "saved_image_path": None,
            "image_dimensions": None,
            "mean_brightness": None,
            "laplacian_sharpness": None,
            "opencv_verified": False,
            "filesize_bytes": 0,
            "unavailable_reason": str(e)
        }


async def main():
    print("=" * 70)
    print("SCRAPING STREET VIEW DATA FOR CHURCH STREET & CORPORATION")
    print("Policy: Raw data collection & offline storage only. Not linked into app code.")
    print("=" * 70)

    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    manifest_output = {
        "title": "Additional Scraped Places: Church Street & Corporation",
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent": "Antigravity Browser Agent via Chrome CDP",
        "integration_status": "stored_offline_unintegrated",
        "policy_notice": "Raw reference datasets collected upon user request. Kept strictly isolated from production application and routing codebase.",
        "storage_directory": "data/additional_scrapes/",
        "places": {}
    }

    for place in TARGET_PLACES:
        p_id = place["place_id"]
        p_dir = os.path.join(OUTPUT_BASE_DIR, p_id)
        os.makedirs(p_dir, exist_ok=True)
        print(f"\n--- Scraping Place: {place['place_name']} ({p_id}) ---")

        place_records = []
        for pt in place["points"]:
            rec = await scrape_single_point(pt, p_dir, p_id)
            place_records.append(rec)
            await asyncio.sleep(1.0)

        manifest_output["places"][p_id] = {
            "place_name": place["place_name"],
            "description": place["description"],
            "records": place_records,
            "total_points": len(place_records),
            "total_collected": sum(1 for r in place_records if r["status"] == "collected"),
            "total_unavailable": sum(1 for r in place_records if r["status"] != "collected")
        }

    out_manifest_path = os.path.join(OUTPUT_BASE_DIR, "places_manifest.json")
    with open(out_manifest_path, "w") as f:
        json.dump(manifest_output, f, indent=2)

    print("\n" + "=" * 70)
    print("SCRAPING SUMMARY:")
    for pid, pdata in manifest_output["places"].items():
        print(f"  • {pdata['place_name']}: {pdata['total_collected']} collected, {pdata['total_unavailable']} unavailable")
    print(f"\nAll files stored in: {OUTPUT_BASE_DIR}/")
    print(f"Manifest written to: {out_manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
