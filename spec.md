# Saakshi — Frozen MVP Specification v1.0

Hacktoberfest Hack Day Bengaluru ’26 · 4-hour implementation target

Product definition: Saakshi is a single-image, evidence-based pedestrian accessibility checker. It uses Gemma 4 to identify visible accessibility barriers in permitted street-view imagery, applies basic image-quality checks, and presents a qualified result with its limitations.

Primary objective: Deliver a working end-to-end prototype within four hours. No feature outside this specification is required for the MVP.

## 1. Scope freeze

IN SCOPE

Image selection, Gemma 4 vision inference, structured output, OpenCV quality checks, deterministic status rules, one-page UI, basic error handling and a small test set.

OUT OF SCOPE

Live navigation, interactive maps, routing, GPS assignment, user accounts, databases, duplicate detection, freshness decay, re-verification, civic complaints, agency attribution, voice, cloud deployment and multi-user support.

## 2. User workflow

\#chatgpt-mermaid-\_r_n6\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI","Helvetica","Apple Color Emoji","Arial",sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_n6\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_n6\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_n6\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_n6\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_n6\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_n6\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_n6\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_n6\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_n6\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_n6\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_n6\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI","Helvetica","Apple Color Emoji","Arial",sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_n6\_ p{margin:0;}#chatgpt-mermaid-\_r_n6\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI","Helvetica","Apple Color Emoji","Arial",sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_n6\_ .label text,#chatgpt-mermaid-\_r_n6\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .node rect,#chatgpt-mermaid-\_r_n6\_ .node circle,#chatgpt-mermaid-\_r_n6\_ .node ellipse,#chatgpt-mermaid-\_r_n6\_ .node polygon,#chatgpt-mermaid-\_r_n6\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .rough-node .label text,#chatgpt-mermaid-\_r_n6\_ .node .label text,#chatgpt-mermaid-\_r_n6\_ .image-shape .label,#chatgpt-mermaid-\_r_n6\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_n6\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .rough-node .label,#chatgpt-mermaid-\_r_n6\_ .node .label,#chatgpt-mermaid-\_r_n6\_ .image-shape .label,#chatgpt-mermaid-\_r_n6\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_n6\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_n6\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_n6\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_n6\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_n6\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_n6\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_n6\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_n6\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_n6\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI","Helvetica","Apple Color Emoji","Arial",sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_n6\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_n6\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_n6\_ .icon-shape,#chatgpt-mermaid-\_r_n6\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_n6\_ .icon-shape p,#chatgpt-mermaid-\_r_n6\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_n6\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_n6\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_n6\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_n6\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_n6\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_n6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_n6\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_n6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_n6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_n6\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_n6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_n6\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_n6\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r_n6\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_n6\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_n6\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .node rect,#chatgpt-mermaid-\_r_n6\_ .node circle,#chatgpt-mermaid-\_r_n6\_ .node ellipse,#chatgpt-mermaid-\_r_n6\_ .node polygon,#chatgpt-mermaid-\_r_n6\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_n6\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_n6\_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2px,2px;}#chatgpt-mermaid-\_r_n6\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_n6\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_n6\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI","Helvetica","Apple Color Emoji","Arial",sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Select permittedstreet-view imageCheck image quality withOpenCVImage usable?INCONCLUSIVERun Gemma 4 visioninferenceOutput valid and usable?Validate structuredobservationsBarrier reported?BARRIERNO BARRIER OBSERVEDDisplay result andreasonNoYesNoYesYesNo

The interface must display the original image, observations, quality-check result, final status and explanation. It must never describe an image-level assessment as proof that an entire route is accessible.

## 3. Fixed technology stack

| Layer             | Frozen choice                                        |
| ----------------- | ---------------------------------------------------- |
| Language          | Python                                               |
| UI                | Streamlit                                            |
| Vision model      | Gemma 4, using a verified multimodal runtime         |
| Local inference   | Ollama, if the chosen model tag supports image input |
| Image quality     | OpenCV                                               |
| Output validation | Pydantic                                             |
| Data storage      | None required                                        |
| Test data         | 3–5 permitted street-view images                     |
| Deployment        | Run locally                                          |

Fallback rule: If the local Gemma setup is not working by minute 30, switch to a verified compatible inference method. If that is not feasible, use precomputed outputs only as an explicitly labelled demo fallback—not as evidence of live model inference.

## 4. Gemma output contract

Gemma must return structured observations, not a final accessibility verdict.

Example:

```
{
  "visible_barriers": [
    {
      "type": "obstruction",
      "description": "A parked vehicle appears to occupy part of the pedestrian path.",
      "location": "right side",
      "visibility": "clear"
    }
  ],
  "visible_features": [
    "curb"
  ],
  "uncertain_observations": [],
  "limitations": [
    "Full pedestrian-path width cannot be determined."
  ]
}
```

This is an illustrative schema, not a guaranteed model response. Validate the actual output and handle malformed JSON, timeouts and missing fields.

The model must not invent measurements, infer invisible features, or label an entire street accessible based on one image.

## 5. Deterministic status rules

Implement these rules exactly for the MVP:

| Condition                                                    | Final status          |
| ------------------------------------------------------------ | --------------------- |
| OpenCV quality check fails                                   | `INCONCLUSIVE`        |
| Gemma inference fails or output is invalid                   | `INCONCLUSIVE`        |
| A visible barrier is reported in a usable image              | `BARRIER`             |
| No barrier is reported in a usable image                     | `NO BARRIER OBSERVED` |
| Evidence is ambiguous or a required observation is uncertain | `INCONCLUSIVE`        |

For the last rule, do not treat every uncertainty in an image as a failure. Only uncertainty relevant to the assessment should force abstention.

No numerical confidence score is required. Do not present an uncalibrated model score as the probability that a path is accessible.

## 6. One-page interface

The entire application should fit on one Streamlit page.

# Saakshi

Pedestrian accessibility evidence checker

Street-view image

Select an image from the permitted sample set.

Image upload or sample selector

### Image quality

Blur / exposure check

Pass / Fail

### Observed evidence

- Visible barriers
- Visible accessibility features
- Uncertain observations

### Assessment result

INCONCLUSIVE

Example only: the image quality is insufficient to support an assessment.

Image-level assessment only. This result is not a safety guarantee or proof of current accessibility.

## 7. Frozen four-hour execution plan

| Elapsed time | Deliverable                              | Priority |
| ------------ | ---------------------------------------- | -------- |
| 00:00–00:30  | Working model inference and app skeleton | P0       |
| 00:30–01:30  | Gemma output and OpenCV checks           | P0       |
| 01:30–02:30  | Evidence gate and complete UI            | P0       |
| 02:30–03:15  | Error handling and three test scenarios  | P0       |
| 03:15–04:00  | Integration, demo rehearsal and buffer   | P0       |

The clock is a hard limit. Do not spend the final hour adding features.

## 8. Acceptance criteria

The MVP is complete only when all of the following work:

- The application starts locally using documented commands.
- A permitted image can be selected and displayed.
- Gemma 4 performs actual image inference.
- Structured observations are validated before use.
- OpenCV rejects at least one deliberately poor-quality image.
- A visible barrier produces `BARRIER`.
- An ambiguous or unusable image produces `INCONCLUSIVE`.
- The result includes an explanation and explicit limitations.
- A failed model call does not crash the application or produce a false clear result.
- The demo clearly distinguishes live inference from any cached fallback.

## 9. Final repository structure

```
saakshi/
├── app.py
├── vision.py
├── evidence_gate.py
├── schemas.py
├── requirements.txt
├── README.md
├── .gitignore
└── sample_images/
    └── README.md
```

Keep the modules small. `vision.py` handles model inference and image-quality checks; `evidence_gate.py` handles status rules; `schemas.py` validates observations; `app.py` renders the interface.

The sample-image directory should contain images only when their applicable usage terms permit redistribution. Otherwise, document how to obtain the permitted test images without committing them.

## 10. Definition of done

The frozen deliverable is a locally runnable, single-page Streamlit application that performs real Gemma 4 vision inference, checks image quality with OpenCV, returns one of three defensible statuses, and explains the evidence and limitations.

No map, database, routing, freshness algorithm, fraud detection or civic workflow is necessary to call this MVP complete.

The specification is now frozen at v1.0. Any additional feature must replace an existing task or wait until after the four-hour deadline.