# Saakshi-Access

> **Evidence, not assumptions.** A verification and evidence layer that checks whether a footpath segment is actually clear.

Built by **Team OpenForge** (**Prakhyath S**, **Chiranthan**) for **Hacktoberfest Hack Day Bengaluru '26**.  
**Tracks:** *Best Use of Gemma 4* and *Best Open-Source AI Project*.

---

> [!IMPORTANT]
> **Saakshi-Access is a verification and evidence tool, not a navigation app.** It never labels a path "safe" or "accessible". It states *"no barrier observed on [date], confidence X"*, or *"UNVERIFIED"*.  
> **Decision support only. Not legal advice. Not a safety guarantee.**

---

## The Problem

Maps show that a footpath exists, not whether it is clear today. For wheelchair, cane, low-vision, and senior users, a parked vehicle, debris, or a broken slab can make a segment impassable—and these barriers can change within hours. A wrong "all clear" is significantly more hazardous than no information at all.

---

## What It Does

Given a street-level pedestrian photograph, Saakshi-Access returns one of four statuses, accompanied by the verifiable evidence trail:

| Status | Meaning |
| :--- | :--- |
| **`BARRIER`** | A physical barrier was observed, accompanied by its category and factual visual description. |
| **`CLEAR_OBSERVED`** | No barrier was observed in this image at capture time. *(This is never treated as proof of permanent absence).* |
| **`INCONCLUSIVE`** | Poor image quality, or the visual checks do not support an unambiguous claim. Retake requested. |
| **`UNVERIFIED`** | No recent evidence logged, or the capture timestamp is missing or stale. |

---

## How It Works

```
                                  +-----------------------+
                                  |   Pedestrian Image    |
                                  +-----------+-----------+
                                              |
                                              v
                              +-------------------------------+
                              | Quality Check (OpenCV Heuristic) |
                              +---------------+---------------+
                                              |
                             [Passes Filter]  |  [Fails Filter: Blur / Exposure]
                                              |  --> INCONCLUSIVE (Refusal Gate)
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
         +-----------------------+                         +-----------------------+
         | Check A: OpenCV Witness |                         | Check B: Gemma 4 Witness |
         | Geometric & Edge Quality|                         | Multimodal Vision-Lang |
         +-----------+-----------+                         +-----------+-----------+
                     |                                                 |
                     +------------------------+------------------------+
                                              |
                                              v
                             +---------------------------------+
                             |   Deterministic Gate (Python)   |
                             |   Zero-Hallucination Civic Rule |
                             +----------------+----------------+
                                              |
                                              v
                             +---------------------------------+
                             | Verified Status + Evidence Log  |
                             +---------------------------------+
```

- **Quality Check (OpenCV)**: Evaluates Laplacian blur variance and grayscale exposure histogram dispersion. Poor quality immediately triggers `INCONCLUSIVE` before invoking neural models.
- **Check A (OpenCV)**: Image quality metrics and edge continuity checks.
- **Check B (Gemma 4)**: Multimodal spatial vision model running locally (or via configured endpoint), extracting structured, visible-only barrier observations from a fixed category taxonomy (sidewalks, curb ramps, tactile paving, crosswalks, obstructions, surface damage).
- **Deterministic Gate (Plain Python)**: A pure, unit-tested function that computes the verdict. **No LLM decides the final verdict.** Gemma's output counts only as evidence for what is visibly present, never as proof that an obstacle is absent.
- **Freshness**: Confidence decays with age according to barrier type. Decay rates are declared assumptions, not empirical constants.
- **Architecture**: The React frontend only displays results and telemetry. The FastAPI backend and deterministic gate execute all validation and decisions.

---

## Gate Logic

| Situation | Verdict |
| :--- | :--- |
| Poor image quality (blur / harsh exposure), or too few matching features | **`INCONCLUSIVE`** (Retake requested) |
| Duplicate or previously registered image hash | **Rejected as reused** |
| Gemma reports a barrier and the scene check is consistent | **`BARRIER`** (With category & description) |
| Gemma reports a barrier but the scene check cannot confirm it | **`INCONCLUSIVE`** (Additional vantage requested) |
| No barrier reported, scene matches, capture date is recent | **`CLEAR_OBSERVED`** |
| Capture date is missing, unverified, or too old | **`UNVERIFIED`** |

*Historical imagery supports historical observations, not confirmation of current conditions.*

---

## Status of This Project

*A transparent inventory of active vs. planned capabilities:*

| Component | Status | Details |
| :--- | :--- | :--- |
| **Image Quality Check (OpenCV)** | **Done** | Laplacian blur variance & exposure checks in `image_quality.py`. |
| **Gemma 4 Observations** | **Done** | Structured 6-criterion schema evaluation in `gemma.py`. |
| **Deterministic Gate + Unit Tests** | **Done** | 69 unit & integration tests passing (`pytest tests/`). |
| **Evidence UI (React + Vite + Tailwind)** | **Done** | Evidence Analysis Workspace & Multimodal Transit Corridors. |
| **Multimodal Transit Corridors** | **Done** | Mode A (Metro Purple Line, Bus, Walk) & Mode B (Point-to-point GTFS). |
| **Benchmark Harness & Metrics** | **Done** | False-reassurance rate tracking and ground-truth validation. |
| **Freshness Decay** | **Simulated** | Time-based confidence decay heuristics across observation ages. |
| **In-app GPS Capture** | **Planned** | Native EXIF geo-tagging & hardware compass heading ingestion. |
| **Hash-chained Evidence Log** | **Planned** | Merkle-tree chained tamper-evident audit ledger. |
| **Volunteer Re-verification Closure Loop** | **Planned** | Peer-audited civic verification task dispatch. |
| **Owner Attribution & Escalation** | **Planned** | Human-approved municipal grievance ticket generation. |

---

## Tech Stack

- **AI & Vision**: Google Gemma 4 (open weights) multimodal vision via Ollama (`gemma4:e4b` / `gemma4:e2b`) or Google GenAI API fallback.
- **Classical Vision**: OpenCV (`opencv-python-headless`), NumPy, SHA-256 fingerprinting.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, Uvicorn, GTFS processing.
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Leaflet / React-Leaflet, Framer Motion.
- **Testing**: pytest (69 test cases), custom end-to-end integration suite.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Optional local inference: [Ollama](https://ollama.com/) with Gemma 4:
  ```bash
  ollama pull gemma4:e4b   # or gemma4:e2b
  ```

### 1. Backend Setup
```bash
# From workspace root
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Install frontend dependencies
npm install

# Configure environment variables
# Copy .env.example to .env
# VITE_BACKEND_URL=http://localhost:8000
# VITE_USE_MOCK=false

npm run dev
```
> *Note:* When `VITE_USE_MOCK=true` is set, a prominent amber simulation banner is rendered across the header to declare that simulated telemetry is active.

### 3. Running Tests
```bash
# Run complete test suite (unit tests, image quality, gate logic, routing)
python -m pytest tests/

# Run end-to-end contract verification
python scripts/verify_all_endpoints_and_contracts.py
```

---

## API Specification

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Health status and configured vision model. |
| `/api/analyze` | `POST` | Dual-witness image intake, OpenCV pre-gate quality, and deterministic verdict. |
| `/api/locations` | `GET` | Canonical Mode A demo transit locations (MG Road, Cubbon Park, Majestic). |
| `/api/journeys` | `GET` | Multimodal transit route alternatives with dynamic sorting (`fastest`, `best_accessibility`). |
| `/api/observations` | `GET` | Prepared Street View camera observation points with Gemma status. |
| `/api/analyze-observation/{id}` | `POST` | Trigger multimodal inference on prepared Street View imagery. |
| `/api/custom-journey` | `POST` | Mode B arbitrary point-to-point GTFS multimodal route planning. |
| `/api/upload-and-analyze` | `POST` | Upload custom pedestrian connector photo for route re-ranking. |
| `/api/samples` | `GET` | Curated sample images for field inspection demonstration. |
| `/api/benchmark` | `GET` | Benchmark evaluation telemetry and false-reassurance metrics. |
| `/api/segments` | `GET` | Historical audited corridor segments with coordinates and imagery. |

---

## Evaluation & Metrics

The headline metric of Saakshi-Access is the **false-reassurance rate**:  
$$\text{False Reassurance Rate} = \frac{\text{Staged barrier images falsely classified as clear}}{\text{Total barrier images evaluated}}$$

In accessibility audits, declaring an impassable footpath clear causes severe physical entrapment. Saakshi-Access actively optimizes against false reassurance rather than raw accuracy.  
We also report barrier precision, recall, INCONCLUSIVE refusal rate, and single-image inference latency.

---

## Limitations

- **Small Staged Pilot**: Evaluated on focused Bengaluru corridors (MG Road, Cubbon Park, Majestic, Residency Road). This is not blanket citywide coverage.
- **Staged vs. Wild Barriers**: Staged barriers can be simpler than real chaotic street conditions. Hard cases (harsh glare, water logging, tree roots, dense shadows) are cataloged.
- **Authenticity Boundary**: AI-generated, cropped, or edited photos cannot be completely prevented. SHA-256 fingerprinting guarantees ledger integrity, not physical truth.
- **Dimensionality**: Sidewalk width, precise ramp slope angles, and tactile curb heights cannot be reliably measured from a single uncalibrated 2D photograph.
- **Human Centricity**: Built as an engineer-led hackathon prototype without disabled users directly in the testing loop. Field testing with disability advocacy groups is the necessary next milestone.
- **Decay Heuristics**: Freshness decay rates are stated engineering assumptions, not empirically measured urban degradation constants.

---

## Data and Attribution

- **Field Imagery**: Original pedestrian observations and staged obstruction captures taken along Bengaluru corridors.
- **Transit & Map Data**: [OpenStreetMap](https://www.openstreetmap.org/) contributors (ODbL, treated as claims, not ground truth). BMRCL Purple Line station locations and BMTC bus routes from GTFS schedule feeds.
- **Taxonomy**: Barrier categories adapted from the [Project Sidewalk](https://projectsidewalk.io/) open taxonomy.
- **Regional Context**: CAG, Moving Without Barriers, Chennai perception survey (~270 respondents). Used as context, not direct Bengaluru measurements.

---

## Related Work

Saakshi-Access builds upon principles pioneered by **Project Sidewalk** and **AccessMap**. Our primary contributions are:
1. Freshness-aware evidence confidence that decays over time.
2. Explicit refusal gates (`INCONCLUSIVE`) to eradicate false safety assurances.
3. A purely deterministic Python decision gate where LLMs provide descriptive evidence rather than final verdicts.
4. Multimodal GTFS transit integration bridging last-mile pedestrian reality with public transport.

---

## Privacy and Responsible Use

- **Local Inference Support**: Gemma can run locally via Ollama without sending pedestrian photos to third-party cloud APIs.
- **Neutral Civic Tone**: Factual, non-accusatory reporting. No naming of individual businesses, property owners, or municipal departments.
- **Human-in-the-Loop**: Any civic escalation requires human review and confirmation.

---

## Roadmap

- **Phase 1 (Hackathon MVP - Current)**: Dual-witness vision analysis, OpenCV quality pre-filter, deterministic verdict gate, multimodal GTFS planner, evidence UI.
- **Phase 2**: In-app GPS capture, hash-chained evidence ledger, volunteer re-verification loop.
- **Phase 3**: Field trials with disabled commuter groups, municipal escalation pipeline, and expansion across Bengaluru transit hubs.

---

## Team OpenForge

- **Prakhyath S** (Lead): Deterministic gate, Gemma & OpenCV checks, backend API, GTFS multimodal planner.
- **Chiranthan**: UI architecture, evaluation benchmark, visual evidence collection.

---

## Licence

Licensed under the [Apache License, Version 2.0](LICENSE).  
Copyright © 2026 Team OpenForge.
