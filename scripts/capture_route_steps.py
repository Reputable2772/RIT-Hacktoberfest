#!/usr/bin/env python3
"""Capture all turn-by-turn route steps in Street View from Church Street to Corporation Circle.

Operates purely on the active Google Maps route in the browser.
Saves screenshots isolated in data/additional_scrapes/church_to_corporation/.
Does NOT modify any application or backend code.
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
import urllib.request
import websockets

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "additional_scrapes",
    "church_to_corporation"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def capture_all_route_steps():
    print("=" * 70)
    print("CAPTURING ALL ROUTE STEPS: CHURCH STREET -> CORPORATION CIRCLE")
    print("Output directory:", OUTPUT_DIR)
    print("=" * 70)

    res = urllib.request.urlopen("http://localhost:9222/json").read()
    tabs = json.loads(res.decode())
    target = next(t for t in tabs if t["id"] == "48A05569C5DB79B3556F98ABB6B6986F")
    ws_url = target["webSocketDebuggerUrl"]
    print("Connected to Chrome CDP:", ws_url)

    manifest = {
        "route_title": "Church Street to Corporation Circle Walking Route",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "Google Maps Active Route via Antigravity Chrome Agent",
        "output_directory": "data/additional_scrapes/church_to_corporation/",
        "steps": []
    }

    async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
        msg_id = 1

        async def cdp(method, params=None, timeout=10.0):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            payload = {"id": cid, "method": method, "params": params or {}}
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

        # Loop through steps until no "Next step" button remains or 15 steps max
        for i in range(2, 14):
            # Read step info
            info_js = """
            (() => {
                const stepText = Array.from(document.querySelectorAll("div")).find(d => (d.innerText || "").startsWith("Step "));
                const hasNext = Array.from(document.querySelectorAll("button")).some(b => (b.innerText || "").includes("Next step"));
                const hasPrev = Array.from(document.querySelectorAll("button")).some(b => (b.innerText || "").includes("Previous step"));
                const dateEl = Array.from(document.querySelectorAll("span, div")).find(el => /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{4}$/.test((el.innerText || "").trim()));
                return {
                    stepFullText: stepText ? stepText.innerText : "Step " + i,
                    hasNext: hasNext,
                    hasPrev: hasPrev,
                    imageryDate: dateEl ? dateEl.innerText.trim() : null,
                    url: window.location.href
                };
            })()
            """
            info = (await cdp("Runtime.evaluate", {"expression": info_js, "returnByValue": True})).get("result", {}).get("value", {})
            full_text = info.get("stepFullText", f"Step {i}")
            lines = [l.strip() for l in full_text.split("\n") if l.strip()]
            header = lines[0] if len(lines) > 0 else f"Step {i}"
            instruction = lines[1] if len(lines) > 1 else ""
            dist = lines[2] if len(lines) > 2 else ""

            clean_name = re.sub(r"[^a-zA-Z0-9]+", "_", f"{header}_{instruction}").strip("_").lower()[:50]
            filename = f"step_{i:02d}_{clean_name}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)

            # Capture screenshot
            snap = await cdp("Page.captureScreenshot", {"format": "png"})
            data_bytes = base64.b64decode(snap.get("data", ""))
            with open(filepath, "wb") as f:
                f.write(data_bytes)

            size_kb = len(data_bytes) // 1024
            print(f"[{i:02d}] Captured: {header} | {instruction} ({dist}) -> {filename} ({size_kb} KB)")

            step_entry = {
                "step_number": i,
                "header": header,
                "instruction": instruction,
                "distance": dist,
                "imagery_date": info.get("imageryDate"),
                "filename": filename,
                "relative_path": f"data/additional_scrapes/church_to_corporation/{filename}",
                "filesize_bytes": len(data_bytes),
                "url": info.get("url")
            }
            manifest["steps"].append(step_entry)

            if not info.get("hasNext"):
                print("Reached final destination step of the route!")
                break

            # Click "Next step"
            click_next_js = """
            (() => {
                const btn = Array.from(document.querySelectorAll("button")).find(b => (b.innerText || "").includes("Next step"));
                if (btn) { btn.click(); return true; }
                return false;
            })()
            """
            await cdp("Runtime.evaluate", {"expression": click_next_js})
            await asyncio.sleep(3.5)

    manifest_path = os.path.join(OUTPUT_DIR, "route_steps_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 70)
    print("ROUTE STEP CAPTURE COMPLETED SUCCESSFULLY!")
    print(f"Total steps captured: {len(manifest['steps'])}")
    print(f"Manifest written to: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(capture_all_route_steps())
