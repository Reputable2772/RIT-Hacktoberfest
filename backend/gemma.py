"""Google AI API integration for multimodal image analysis.

Uses Google's official `google-genai` Python SDK.
Reads credentials from GEMINI_API_KEY and model name from GEMINI_MODEL (fallback: GEMMA_MODEL).
Sends real image bytes directly to the model as a types.Part.from_bytes binary payload.
Enforces structured output parsing and validation via Pydantic.
"""

import json
import logging
import re
from typing import Optional, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError

from backend.config import settings
from backend.schemas import (
    AccessibilityCriterionFinding,
    ConfidenceRating,
    FeatureStatus,
    GemmaVisualAnalysis,
    ModelObservations,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an objective computer vision assistant assessing street-view images for pedestrian accessibility barriers.
Analyze only what is directly visible in the image.
Do NOT attempt to give a final verdict like "accessible" or "inaccessible".
Do NOT invent measurements or assume features that cannot be seen.

You must return a single JSON object with EXACTLY this structure:
{
  "visible_barriers": [
    {
      "type": "obstruction | curb | stairs | broken_pavement | debris | narrow_path | drop_off",
      "description": "Factual description of the barrier",
      "location": "left sidewalk | path center | right side | curb edge | entrance",
      "visibility": "clear | partial | uncertain"
    }
  ],
  "visible_features": [
    "curb_ramp", "tactile_paving", "wide_sidewalk", "handrail", "level_crossing"
  ],
  "uncertain_observations": [
    "Description of visual ambiguity affecting path assessment (e.g. shadowed ground, distant obstruction)"
  ],
  "limitations": [
    "Image-specific limitations (e.g. single camera angle, occluded background)"
  ]
}
"""

PEDESTRIAN_CRITERIA_PROMPT = """You are an objective computer vision assistant evaluating ground-level pedestrian accessibility.
Examine this image and assess the following 6 specific criteria:
1. sidewalk: Is a dedicated pedestrian sidewalk/footpath present and continuous?
2. curb_ramps: Are dropped curb ramps present at crossings or changes in elevation?
3. tactile_paving: Is tactile ground paving (blister or directional tiles for visual impairment) visible?
4. pedestrian_crossings: Are designated pedestrian crosswalks (zebra markings, signals) present?
5. obstructions: Are physical obstructions (parked vehicles, poles, street vendors, debris) encroaching on the pedestrian path?
6. surface_damage: Is visible surface damage (broken pavers, deep potholes, tree root buckling, cracks) present?

Rules:
- For status, use ONLY: "present", "absent", or "unknown".
- If an object is partially obscured, out of frame, too distant, or ambiguous, use "unknown". Do NOT infer absence from an incomplete view!
- For confidence, use ONLY: "high", "medium", or "low".
- Write a short factual explanation based strictly on visible evidence in the image.
- Calculate an overall accessibility score between 0.0 (severely obstructed/inaccessible) and 100.0 (fully accessible, ramped, clear).

Return a single JSON object with EXACTLY this structure:
{
  "sidewalk": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "curb_ramps": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "tactile_paving": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "pedestrian_crossings": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "obstructions": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "surface_damage": {
    "status": "present" | "absent" | "unknown",
    "confidence": "high" | "medium" | "low",
    "explanation": "..."
  },
  "calculated_accessibility_score": 85.0,
  "summary": "...",
  "limitations": ["..."]
}
"""


def clean_json_response(raw_text: str) -> str:
    """Extract JSON string from potential markdown code blocks."""
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def get_genai_client() -> Optional[genai.Client]:
    """Instantiate and return a google-genai Client if API key is configured."""
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key in ("your_actual_key_here", "your_gemini_api_key_here"):
        from dotenv import load_dotenv
        import os
        load_dotenv(override=True)
        env_key = os.getenv("GEMINI_API_KEY", "")
        if env_key and env_key not in ("your_actual_key_here", "your_gemini_api_key_here"):
            api_key = env_key
        else:
            return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize google-genai client: {e}")
        return None


def analyze_image_with_model(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    client: Optional[genai.Client] = None,
    model_name: Optional[str] = None,
) -> Tuple[Optional[ModelObservations], Optional[str]]:
    """Send image bytes to the configured model for raw observation detection."""
    selected_model = model_name or settings.GEMINI_MODEL
    active_client = client or get_genai_client()

    if active_client is None:
        return None, (
            f"Google API key not configured. Set GEMINI_API_KEY environment variable. "
            f"(Target model: {selected_model})"
        )

    try:
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        response = active_client.models.generate_content(
            model=selected_model,
            contents=[
                SYSTEM_PROMPT,
                image_part,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        raw_text = getattr(response, "text", None)
        if not raw_text:
            return None, "Model returned an empty response"

        cleaned_json = clean_json_response(raw_text)
        data = json.loads(cleaned_json)
        observations = ModelObservations.model_validate(data)
        return observations, None

    except APIError as api_err:
        logger.error(f"Google GenAI API error calling model '{selected_model}': {api_err}")
        return None, f"Model API error ({selected_model}): {str(api_err)}"
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode model JSON: {json_err}")
        return None, f"Model returned invalid JSON: {str(json_err)}"
    except ValidationError as val_err:
        logger.error(f"Model output schema validation error: {val_err}")
        return None, f"Model output schema validation error: {str(val_err)}"
    except Exception as exc:
        logger.error(f"Unexpected error in model inference: {exc}")
        return None, f"Model inference error: {str(exc)}"


def create_unavailable_analysis(
    image_id: str,
    location_id: Optional[str] = None,
    segment_id: Optional[str] = None,
    reason: str = "Visual evidence not collected or runtime unavailable",
    status: str = "image_unavailable",
    model_used: Optional[str] = None,
) -> GemmaVisualAnalysis:
    """Construct an explicit unassessed/unavailable analysis object with honest provenance."""
    def unknown_finding(criterion: str, label: str) -> AccessibilityCriterionFinding:
        return AccessibilityCriterionFinding(
            criterion=criterion,
            label=label,
            status=FeatureStatus.UNKNOWN,
            confidence=ConfidenceRating.LOW,
            explanation=f"Unassessed: {reason}",
        )

    return GemmaVisualAnalysis(
        image_id=image_id,
        location_id=location_id,
        segment_id=segment_id,
        status=status,
        inference_source="unavailable",
        model_used=model_used or settings.GEMINI_MODEL,
        evidence_status="INCONCLUSIVE",
        sidewalk=unknown_finding("sidewalk", "Sidewalk Presence & Continuity"),
        curb_ramps=unknown_finding("curb_ramps", "Curb Ramps"),
        tactile_paving=unknown_finding("tactile_paving", "Tactile Paving"),
        pedestrian_crossings=unknown_finding("pedestrian_crossings", "Pedestrian Crossings"),
        obstructions=unknown_finding("obstructions", "Obstructions & Encroachment"),
        surface_damage=unknown_finding("surface_damage", "Surface Damage"),
        calculated_accessibility_score=50.0,
        summary=f"Visual accessibility unassessed: {reason}",
        limitations=[reason],
    )


def analyze_pedestrian_image_multimodal(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    image_id: str = "IMG_0",
    location_id: Optional[str] = None,
    segment_id: Optional[str] = None,
    client: Optional[genai.Client] = None,
    model_name: Optional[str] = None,
) -> Tuple[Optional[GemmaVisualAnalysis], Optional[str]]:
    """Send real image bytes to Gemma to extract 6 structured accessibility criteria.

    Passes binary image content directly to the configured multimodal runtime.
    Supports either an edge/local Gemma runtime (via GEMMA_LOCAL_ENDPOINT)
    or Google GenAI API. If no runtime is available, returns an explicit error
    without fabricating live execution.
    """
    selected_model = model_name or settings.GEMINI_MODEL

    # 1. Attempt edge / local Gemma runtime if configured
    local_endpoint = settings.GEMMA_LOCAL_ENDPOINT
    if local_endpoint:
        try:
            import base64
            import httpx

            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": selected_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PEDESTRIAN_CRITERIA_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                            },
                        ],
                    }
                ],
                "response_format": {"type": "json_object"},
            }
            with httpx.Client(timeout=30.0) as http_client:
                resp = http_client.post(f"{local_endpoint.rstrip('/')}/v1/chat/completions", json=payload)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    content = resp_data["choices"][0]["message"]["content"]
                    data = json.loads(clean_json_response(content))
                    return _parse_gemma_criteria_response(
                        data=data,
                        image_id=image_id,
                        location_id=location_id,
                        segment_id=segment_id,
                        model_used=selected_model,
                        inference_source="live_local_gemma",
                    ), None
        except Exception as local_err:
            logger.warning(f"Local Gemma runtime failed: {local_err}")

    # 2. Attempt Google GenAI API
    active_client = client or get_genai_client()
    if active_client is None:
        return None, (
            f"No live Gemma runtime or valid API key available. "
            f"Configure GEMMA_LOCAL_ENDPOINT or GEMINI_API_KEY. (Target model: {selected_model})"
        )

    try:
        # Construct actual binary image part
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        response = active_client.models.generate_content(
            model=selected_model,
            contents=[
                PEDESTRIAN_CRITERIA_PROMPT,
                image_part,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        raw_text = getattr(response, "text", None)
        if not raw_text:
            return None, "Model returned an empty response"

        cleaned_json = clean_json_response(raw_text)
        data = json.loads(cleaned_json)

        return _parse_gemma_criteria_response(
            data=data,
            image_id=image_id,
            location_id=location_id,
            segment_id=segment_id,
            model_used=selected_model,
            inference_source="live_gemma_api",
        ), None

    except APIError as api_err:
        logger.error(f"Google GenAI API error calling model '{selected_model}': {api_err}")
        return None, f"Model API error ({selected_model}): {str(api_err)}"
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode model JSON: {json_err}")
        return None, f"Model returned invalid JSON: {str(json_err)}"
    except ValidationError as val_err:
        logger.error(f"Model output schema validation error: {val_err}")
        return None, f"Model output schema validation error: {str(val_err)}"
    except Exception as exc:
        logger.error(f"Unexpected error in model inference: {exc}")
        return None, f"Model inference error: {str(exc)}"


def _parse_gemma_criteria_response(
    data: dict,
    image_id: str,
    location_id: Optional[str],
    segment_id: Optional[str],
    model_used: str,
    inference_source: str,
) -> GemmaVisualAnalysis:
    """Helper to parse raw model JSON into validated GemmaVisualAnalysis."""
    def parse_criterion(key: str, label: str) -> AccessibilityCriterionFinding:
        sub = data.get(key, {})
        return AccessibilityCriterionFinding(
            criterion=key,
            label=label,
            status=FeatureStatus(sub.get("status", "unknown").lower()),
            confidence=ConfidenceRating(sub.get("confidence", "low").lower()),
            explanation=sub.get("explanation", "No explanation provided."),
        )

    # Determine evidence status
    ob = data.get("obstructions", {}).get("status", "").lower()
    sd = data.get("surface_damage", {}).get("status", "").lower()
    if ob == "present" or sd == "present":
        ev_status = "BARRIER"
    elif ob == "absent" and sd == "absent":
        ev_status = "NO_BARRIER_OBSERVED"
    else:
        ev_status = "INCONCLUSIVE"

    return GemmaVisualAnalysis(
        image_id=image_id,
        location_id=location_id,
        segment_id=segment_id,
        status="completed",
        inference_source=inference_source,
        model_used=model_used,
        evidence_status=ev_status,
        sidewalk=parse_criterion("sidewalk", "Sidewalk Presence & Continuity"),
        curb_ramps=parse_criterion("curb_ramps", "Curb Ramps"),
        tactile_paving=parse_criterion("tactile_paving", "Tactile Paving"),
        pedestrian_crossings=parse_criterion("pedestrian_crossings", "Pedestrian Crossings"),
        obstructions=parse_criterion("obstructions", "Obstructions & Encroachment"),
        surface_damage=parse_criterion("surface_damage", "Surface Damage"),
        calculated_accessibility_score=float(data.get("calculated_accessibility_score", 50.0)),
        summary=data.get("summary", "Visual analysis completed."),
        limitations=data.get("limitations", ["Single camera perspective assessment only."]),
    )
