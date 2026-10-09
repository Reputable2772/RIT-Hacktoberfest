"""Configuration settings for Saakshi Backend."""

import os
from typing import List
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # GEMINI_MODEL takes precedence; GEMMA_MODEL accepted as alias/fallback
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or os.getenv("GEMMA_MODEL") or "gemma-4-26b-a4b-it"
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Image quality heuristic thresholds
    # Documented as heuristics, not calibrated accessibility metrics
    BLUR_THRESHOLD: float = float(os.getenv("BLUR_THRESHOLD", "100.0"))
    DARK_BRIGHTNESS_THRESHOLD: float = float(os.getenv("DARK_BRIGHTNESS_THRESHOLD", "35.0"))
    BRIGHT_BRIGHTNESS_THRESHOLD: float = float(os.getenv("BRIGHT_BRIGHTNESS_THRESHOLD", "220.0"))


settings = Settings()
