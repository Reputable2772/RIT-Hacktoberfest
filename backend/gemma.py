"""Google AI API integration for model vision analysis.

Uses Google's official `google-genai` Python SDK.
Reads credentials from GEMINI_API_KEY and model name from GEMINI_MODEL (fallback: GEMMA_MODEL).
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
from backend.schemas import ModelObservations

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


def clean_json_response(raw_text: str) -> str:
    """Extract JSON string from potential markdown code blocks."""
    text = raw_text.strip()
    # Check for markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def get_genai_client() -> Optional[genai.Client]:
    """Instantiate and return a google-genai Client if API key is configured."""
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_actual_key_here" or api_key == "your_gemini_api_key_here":
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
    """Send image to the configured vision model and parse structured observations.

    Returns:
        Tuple of (ModelObservations, Optional[str error_message])
    """
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
