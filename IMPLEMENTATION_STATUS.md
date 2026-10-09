# Saakshi: Implementation Status & End-to-End Verification Report

**Project:** Saakshi — Bengaluru Multimodal Pedestrian Accessibility & Transit Planner  
**Verification Date:** 2026-10-09  
**Overall Status:** **Verified Working End-to-End (with Documented External Runtime Limitations)**  

---

## 1. Quick Startup & Environment Instructions

### 1.1 Startup Commands
```bash
# 1. Enter the Nix environment (provides Python 3.12, GDAL, GEOS, system libraries):
nix develop

# 2. Activate the virtual environment (if not automatically activated):
source .venv/bin/activate

# 3. Start the FastAPI backend server (serves both API endpoints and the Web UI):
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Once launched, open your browser to:
**`http://localhost:8000`**

### 1.2 Environment Variables (`.env`)
| Variable | Description | Current Status in Environment |
| :--- | :--- | :--- |
| `GEMMA_LOCAL_ENDPOINT` | Base URL for an OpenAI-compatible local edge vision server (e.g. vLLM or Ollama serving PaliGemma/Qwen2-VL) | `None` (Unset) |
| `GEMINI_API_KEY` | Google AI Studio API key for cloud multimodal inference | `your_gemini_api_key_here` (Placeholder) |
| `GEMMA_MODEL` / `GEMINI_MODEL` | Target multimodal model identifier | `gemma-4-26b-a4b-it` |
| `PORT` / `HOST` | FastAPI server binding parameters | `8000` / `0.0.0.0` |

---

## 2. Categorized Feature Matrix

### Verified Working
- **Full Web Application UI**: Single-page interactive console featuring high-contrast dark theme, accessible typography (Outfit), responsive layout, and SVG micro-indicators.
- **Interactive OpenStreetMap Integration**: Real Leaflet basemap powered by standard OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`), dynamic route polyline rendering, station markers, and camera observation pins.
- **Mode A Journey Exploration (A → B, B → C, C → A)**: Instant corridor switching, alternative route cards, segment breakdowns, travel metrics, fare calculations, and surveyed observation markers.
- **Dynamic Route Ranking**: Live sorting across 4 criteria:
  1. *Fastest* (travel duration)
  2. *Least Walking* (pedestrian distance)
  3. *Fewest Transfers* (transit interchanges)
  4. *Most Accessible* (composite accessibility score)
- **Ground Truth Observation Inspection**: Clicking any route card CTA ("Inspect Ground Evidence & Barriers") or map observation pin opens an evidence inspector panel displaying actual captured Street View photography, street names, and model inspection controls.
- **Mode B Custom Location Planning**: Arbitrary coordinate routing across Bengaluru with predefined trip presets (e.g., Richmond Circle → Commercial Street, Indiranagar → Vidhana Soudha) and input coordinate bounds validation.
- **BMTC & BMRCL GTFS Spatial Matching**: Real-time nearest-stop discovery over `bmtc-gtfs.zip` and `bmrcl-gtfs.zip` `stops.txt`.
- **Image Quality & Safety Filtering**: Automated pre-inference gate rejecting invalid mime types (`text/plain`), corrupt files, empty uploads, and blurry images (Laplacian variance < 100.0).
- **Security & Path Traversal Hardening**: Protected image serving endpoint `GET /api/images/{filename}` preventing directory traversal attacks (`..`), non-image extensions, and unauthorized file reads.
- **Graceful Offline Degradation**: When live inference runtimes are absent, the system honestly reports `runtime_unavailable` / `INCONCLUSIVE` (neutral score `50.0`) without fabricating fake barrier predictions.
- **Automated Test Suite**: 69 / 69 tests passing with **100% statement coverage** across all 12 backend modules.

### Working with Limitations
- **Mode B Transit Schedules**: Performs spatial nearest-stop discovery and haversine transit travel-time estimation (~15 km/h bus, ~1.25 m/s walking) rather than full multi-trip graph routing over `stop_times.txt` and `calendar.txt`.
- **Street View Image Coverage**: 136 real readable PNGs collected and cataloged across 171 planned corridor points. 35 points encountered Google Maps capture timeouts in restricted parks/subways and are documented as explicit coverage gaps in [`data/street_view_manifest.json`](file:///home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project/data/street_view_manifest.json).

### Blocked by External Dependencies
- **Live Multimodal Gemma Inference**: Blocked by the absence of an active OpenAI-compatible local edge vision model server on `localhost` or a valid `GEMINI_API_KEY` secret. Real image bytes were fed to the pipeline during verification; the pipeline verified proper structured failure handling and returned `runtime_unavailable`.

### Broken / Not Implemented
- Dynamic timetable routing across multiple GTFS bus route transfers with calendar exceptions.

---

## 3. Defects Discovered and Resolved During Verification

| Defect ID | Severity | Category | Description | Root Cause | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | **Critical** | Security | Arbitrary File Traversal in `GET /api/images/{filename}` | `backend/planner.py:get_image_path()` used unnormalized path joining without extension filtering or root directory confinement, allowing access to `.env` and `README.md`. | Enforced strict image extension checks (`.png, .jpg, .jpeg, .webp`), path normalization, rejection of `..` segments, and canonical directory resolution restricted to `data/`. Verified with unit and API tests. |
| **DEF-02** | **Medium** | UI / Map | "API KEY REQUIRED" Map Tile Watermarks | Carto tile layer in `backend/static/index.html` was rate-limited and required an active commercial API key. | Switched Leaflet basemap provider to open standard OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`). |
| **DEF-03** | **Medium** | UX / Integration | Missing Mode B Controls & Card Observation CTA | Mode B in the web interface lacked preset trip selectors and custom photo upload controls, while route cards lacked a direct CTA to inspect observations. | Added preset dropdown selector, coordinate boundary validation banners, pedestrian photo upload card calling `POST /api/upload-and-analyze`, and "Inspect Ground Evidence & Barriers" buttons on route cards. |
| **DEF-04** | **Medium** | Layout / CSS | Evidence Panel Modal Rendered Offscreen (y: 1115px) | Flex and grid containers in `.main-layout` and `.content-area` expanded to 1409px when route cards rendered because `body` and `.main-layout` lacked height and overflow constraints. | Added `height: 100vh; overflow: hidden;` to `body`, `min-height: 0; max-height: calc(100vh - 75px);` to `.main-layout`, `height: 100%; overflow: hidden;` to `.content-area`, and `z-index: 2000; max-height: calc(100% - 40px);` to `.evidence-panel`. Modal now floats at `y: 431px` directly inside the viewport. |

---

## 4. Summary of Files Changed

- [`backend/planner.py`](file:///home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project/backend/planner.py):
  - Hardened `get_image_path()` with path normalization, strict extension whitelist, traversal rejection, and directory containment.
- [`backend/static/index.html`](file:///home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project/backend/static/index.html):
  - Fixed desktop and mobile layout overflow constraints.
  - Switched map tile provider to OpenStreetMap.
  - Added Mode B trip presets and coordinate boundary validation.
  - Added pedestrian photo upload and analysis card.
  - Added route card observation inspection button.
- [`scripts/browser_qa_suite.py`](file:///home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project/scripts/browser_qa_suite.py):
  - Built autonomous Playwright Chrome browser test suite covering page load, journey switching, filter ranking, breaking attempts, custom trip planning, image upload errors, and mobile responsiveness.
- [`tests/test_coverage_completion.py`](file:///home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project/tests/test_coverage_completion.py):
  - Added `test_get_image_path_security_checks()` and comprehensive mock integration tests achieving 100% statement coverage.

---

## 5. Automated Test Suite Results

**Test Command:**
```bash
nix develop --command pytest --cov=backend --cov-report=term-missing
```

**Results:**
```text
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project
plugins: anyio-4.15.1, cov-7.1.0
collected 69 items

tests/test_api.py .........                                              [ 13%]
tests/test_coverage_completion.py .............................          [ 55%]
tests/test_evidence_gate.py .........                                    [ 68%]
tests/test_image_quality.py ........                                     [ 79%]
tests/test_multimodal_planner.py ......                                  [ 88%]
tests/test_scoring_and_provenance.py ........                            [100%]

================================ tests coverage ================================
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
backend/__init__.py                     0      0   100%
backend/accessibility_findings.py      44      0   100%
backend/config.py                      16      0   100%
backend/evidence_gate.py               31      0   100%
backend/gemma.py                      113      0   100%
backend/gtfs_service.py               100      0   100%
backend/image_quality.py               36      0   100%
backend/locations.py                   22      0   100%
backend/main.py                       117      0   100%
backend/planner.py                    218      0   100%
backend/schemas.py                     68      0   100%
backend/transit_data.py                68      0   100%
-----------------------------------------------------------------
TOTAL                                 833      0   100%
======================== 69 passed, 1 warning in 3.53s =========================
```

---

## 6. Browser Verification Results for Primary Journeys

Browser testing was conducted using headless Google Chrome (`Playwright 1.63.0`) against the live Uvicorn daemon at `http://localhost:8000`.

### 6.1 Journey A → B (MG Road Metro → Cubbon Park Metro)
- **Route Cards Rendered:** 3 alternatives:
  1. *BMRCL Purple Line Metro (Direct)*: 9 min duration, 210m walking, 0 transfers, ₹10 fare, accessibility score 50/100 (Moderate).
  2. *Direct Street Walk via Church St & Kasturba Rd*: 25 min duration, 2,009m walking, 0 transfers, ₹0 fare, accessibility score 50/100.
  3. *BMTC Direct Bus via MG Road Corridor*: 14 min duration, 320m walking, 0 transfers, ₹15 fare, accessibility score 50/100.
- **Map & Evidence Agreement:** Leaflet map drew purple route line and positioned 3 camera observation markers (`OBS_1`, `OBS_2`, `OBS_3`). Clicking `OBS_1` loaded Church Street Street View image (`0001.png`) into the floating evidence inspector.

### 6.2 Journey B → C (Cubbon Park Metro → Majestic)
- **Route Cards Rendered:** 3 alternatives:
  1. *BMRCL Purple Line Metro (Direct to Majestic)*: 15 min duration, 260m walking, 0 transfers, ₹15 fare, accessibility score 50/100.
  2. *BMTC Direct Bus Corridor (Sheshadri Road)*: 28 min duration, 380m walking, 0 transfers, ₹15 fare, accessibility score 50/100.
  3. *Full Walking Route via Sheshadri Road*: 58 min duration, 4,730m walking, 0 transfers, ₹0 fare, accessibility score 50/100.
- **Map & Evidence Agreement:** Leaflet map updated center and route polyline; camera pins updated to B → C corridor observations.

### 6.3 Journey C → A (Majestic → MG Road Metro)
- **Route Cards Rendered:** 4 alternatives:
  1. *BMRCL Purple Line Metro (Direct to MG Road)*: 15 min duration, 210m walking, 0 transfers, ₹15 fare, accessibility score 50/100.
  2. *BMTC Direct Bus via K.G. Road & MG Road*: 30 min duration, 350m walking, 0 transfers, ₹20 fare, accessibility score 50/100.
  3. *BMRCL Metro via Interchange*: 18 min duration, 420m walking, 1 transfer, ₹20 fare, accessibility score 50/100.
  4. *Direct Street Walk via Kempegowda & MG Road*: 74 min duration, 5,980m walking, 0 transfers, ₹0 fare, accessibility score 50/100.
- **Map & Evidence Agreement:** Map centered on Majestic / MG Road corridor; route polylines and observation pins updated dynamically.

### 6.4 Exploratory Breaking & Input Validation Tests
1. **Rapid Tab Clicking:** Switched between A→B, B→C, and C→A rapidly (15 cycles); state remained synchronized without stale card overlays or UI crashes.
2. **Empty Mode B Inputs:** Clicking "Compute Custom Route" with blank origin/destination triggered validation banner: `"Please enter both origin and destination names."`
3. **Out-of-Bounds Coordinates:** Inputting latitude `999.0` triggered error banner: `"Coordinates out of bounds (Latitude: -90..90, Longitude: -180..180)."`.
4. **Unsupported File Upload:** Uploading `test_invalid.txt` triggered rejection banner: `"Upload Rejected: Unsupported format 'text/plain'. Supported: image/jpeg, image/jpg, image/png, image/webp"`.
5. **Blurry Image Upload:** Uploading `test_blurry.jpg` triggered quality gate rejection: `"Upload Rejected: Image failed quality check: Image is too blurry for reliable assessment (Laplacian variance: 0.9 < 100.0)"`.
6. **Mobile Viewport (390 x 844 px):** Layout stacked cleanly into a single vertical column with interactive map preview, scrollable routing sidebar, and full-width evidence overlay.

---

## 7. Verification Artifacts & Screenshots

The browser test suite generated visual verification artifacts stored in the workspace artifact directory:
- Initial Page Load: `qa_01_initial_load.png`
- Evidence Modal Inspector: `qa_02_evidence_modal.png`
- Mode B Custom Routes: `qa_03_mode_b_custom_routes.png`
- Image Quality Upload Rejection: `qa_04_upload_evaluated.png`
- Mobile Viewport: `qa_05_mobile_viewport.png`
- Automated Test Run Report: `browser_qa_report.json`
