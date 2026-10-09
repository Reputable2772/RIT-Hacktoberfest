# Saakshi — Pedestrian Accessibility Evidence Checker (Backend)

Saakshi is an evidence-based pedestrian accessibility image checker. It analyzes single street-view images to detect visible physical accessibility barriers (e.g. steps without ramps, sidewalk obstructions, broken pavement, curbs), applies defensive OpenCV image quality gates, and outputs deterministic, qualified assessment results with explicit limitations.

---

## 1. Architecture & Design Principles

- **Separation of Concerns:** The vision model acts strictly as an objective observation extractor describing visual evidence. The backend owns the final verdict.
- **Defensive Quality Gate:** OpenCV checks image readability (blur and under/overexposure) before any model call is dispatched.
- **Deterministic Evidence Gate:** No arbitrary confidence numbers. The result is strictly mapped to `BARRIER`, `NO_BARRIER_OBSERVED`, or `INCONCLUSIVE`.
- **Honest Limitations:** Single-image assessment only. The system never claims a pedestrian route is "accessible" or "safe".

---

## 2. Directory Structure

```text
├── backend/
│   ├── __init__.py
│   ├── config.py           # Environment and heuristic threshold configuration
│   ├── evidence_gate.py    # Deterministic status rules and limitations
│   ├── gemma.py            # Google google-genai SDK integration and parsing
│   ├── image_quality.py    # OpenCV blur, exposure, and readability checks
│   ├── main.py             # FastAPI endpoints (GET /health, POST /api/analyze)
│   └── schemas.py          # Pydantic request/response and observation models
├── tests/
│   ├── __init__.py
│   ├── test_api.py         # End-to-end API tests with mocked inference
│   ├── test_evidence_gate.py # Deterministic gate unit tests
│   └── test_image_quality.py # OpenCV quality heuristic tests
├── .env.example            # Template for environment variables
├── .gitignore              # Ignores .env, .venv, bytecode, and nix artifacts
├── flake.nix               # Reproducible Nix flake development shell
├── requirements.txt        # Python dependency manifest
└── README.md
```

---

## 3. Development Setup

### Using Nix Flake

Enter the Nix development shell:

```bash
nix develop
```

This shell provides:
- Python 3.12
- Native libraries (`glib`, `libGL`, `zlib`, `stdenv.cc.cc.lib`) for OpenCV and NumPy C-extensions
- Automatic `.venv` activation and environment setup

### Installing Python Dependencies

Within the development environment, dependencies can be installed using `pip`:

```bash
pip install -r requirements.txt
```

---

## 4. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Environment Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemma-4-26b-a4b-it` | Model identifier (also accepts `GEMMA_MODEL` as alias) |
| `MAX_UPLOAD_MB` | `10` | Maximum image upload size in megabytes |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowed origins |
| `APP_ENV` | `development` | Environment name |
| `BLUR_THRESHOLD` | `100.0` | Heuristic Laplacian variance threshold (higher = sharper) |
| `DARK_BRIGHTNESS_THRESHOLD` | `35.0` | Heuristic minimum mean pixel intensity (0–255) |
| `BRIGHT_BRIGHTNESS_THRESHOLD` | `220.0` | Heuristic maximum mean pixel intensity (0–255) |

> **Note on Heuristic Thresholds:**
> The blur and exposure metrics are computational heuristics for image readability, **not calibrated accessibility metrics**.

---

## 5. Running the Backend Server

Start the FastAPI application with Uvicorn:

```bash
# Inside nix develop:
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## 6. Running Tests

Run the automated test suite completely offline (no API key or network access required):

```bash
# Inside nix develop:
pytest -v
```

All model calls in tests are mocked, validating:
- `GET /health` endpoint
- File upload validations (unsupported MIME types, empty files, size limits)
- OpenCV quality rejection skipping model inference
- Deterministic verdicts (`BARRIER`, `NO_BARRIER_OBSERVED`, `INCONCLUSIVE`)
- Resilience to malformed JSON, model schema deviations, and API timeouts

---

## 7. API Specification

### `GET /health`
Returns system status and configured model without external API calls.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "app": "saakshi",
  "version": "1.0.0",
  "configured_model": "gemma-4-26b-a4b-it"
}
```

### `POST /api/analyze`
Upload a single street-view image for accessibility barrier assessment.

- **Request:** `multipart/form-data`
- **Field:** `image` (binary, JPEG/PNG/WebP, up to 10 MB)

**Response `200 OK`:**
```json
{
  "status": "BARRIER",
  "observations": {
    "visible_barriers": [
      {
        "type": "stairs",
        "description": "Flight of 4 steps with no adjacent ramp",
        "location": "entrance to path",
        "visibility": "clear"
      }
    ],
    "visible_features": ["tactile_paving"],
    "uncertain_observations": [],
    "limitations": ["Single camera perspective"]
  },
  "image_quality": {
    "passed": true,
    "laplacian_variance": 312.4,
    "mean_brightness": 128.5,
    "issues": []
  },
  "limitations": [
    "Assessment is based strictly on a single 2D street-view image.",
    "Result does not guarantee that the route, path, or entrance is safe or fully accessible.",
    "Physical cross-slopes, exact path widths, and continuous path clearance outside the camera frame cannot be measured.",
    "Transient obstacles (e.g. parked vehicles, temporary works) may change over time."
  ],
  "reason": "Clear physical accessibility barrier(s) detected in the pedestrian area: stairs (entrance to path)."
}
```

---

## 8. Status Semantics & Evidence Gate

| Status | Condition | Meaning |
|---|---|---|
| `BARRIER` | Usable image + clearly visible barrier | Evidence of physical obstruction or barrier to pedestrian mobility was observed in the image. |
| `NO_BARRIER_OBSERVED` | Usable image + no barriers reported | No barriers observed within the visible camera angle. Qualified by limitations. |
| `INCONCLUSIVE` | Poor image quality, API error, malformed output, or relevant visual ambiguity | No defensible verdict can be reached from the available visual evidence. |

---

## 9. Known Model Limitations & Availability Note

- **Gemma Vision Availability:** As of current Google AI Studio API releases, Gemma 2 models (`gemma-2-2b-it`, `gemma-2-27b-it`) are text-only and do not accept multimodal image inputs via Google AI Studio's API endpoint.
- **Multimodal Models:** Multimodal vision input on the Google API is supported by Gemini models (e.g. `gemini-2.0-flash`).
- **Configurability:** Saakshi retains `GEMINI_MODEL` (and fallback `GEMMA_MODEL`) as fully configurable environment variables. If a multimodal Gemma endpoint or proxy is deployed, configure its identifier in `GEMINI_MODEL` without code modifications.
