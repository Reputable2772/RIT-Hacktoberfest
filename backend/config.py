"""Configuration settings for Saakshi Backend."""

import os
from typing import List
from dotenv import load_dotenv

# Load .env if present
load_dotenv(override=True)


class Settings:
    _gemini_api_key: str = None
    _gemini_model: str = None
    _allowed_origins: List[str] = None

    @property
    def GEMINI_API_KEY(self) -> str:
        if self._gemini_api_key is not None:
            return self._gemini_api_key
        load_dotenv(override=True)
        return os.getenv("GEMINI_API_KEY", "")

    @GEMINI_API_KEY.setter
    def GEMINI_API_KEY(self, val: str) -> None:
        self._gemini_api_key = val

    @GEMINI_API_KEY.deleter
    def GEMINI_API_KEY(self) -> None:
        self._gemini_api_key = None

    @property
    def GEMINI_MODEL(self) -> str:
        if self._gemini_model is not None:
            return self._gemini_model
        load_dotenv(override=True)
        return os.getenv("GEMINI_MODEL") or os.getenv("GEMMA_MODEL") or "gemma-4-26b-a4b-it"

    @GEMINI_MODEL.setter
    def GEMINI_MODEL(self, val: str) -> None:
        self._gemini_model = val

    @GEMINI_MODEL.deleter
    def GEMINI_MODEL(self) -> None:
        self._gemini_model = None

    GEMMA_LOCAL_ENDPOINT: str = os.getenv("GEMMA_LOCAL_ENDPOINT", "")
    ALLOW_OFFLINE_DEMO_FALLBACK: bool = os.getenv("ALLOW_OFFLINE_DEMO_FALLBACK", "false").lower() in ("true", "1", "yes")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "15"))

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self._allowed_origins is not None:
            return self._allowed_origins
        load_dotenv(override=True)
        raw = os.getenv("ALLOWED_ORIGINS", "*")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @ALLOWED_ORIGINS.setter
    def ALLOWED_ORIGINS(self, val: List[str]) -> None:
        self._allowed_origins = val

    @ALLOWED_ORIGINS.deleter
    def ALLOWED_ORIGINS(self) -> None:
        self._allowed_origins = None

    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Image quality heuristic thresholds
    # Documented as heuristics, not calibrated accessibility metrics
    BLUR_THRESHOLD: float = float(os.getenv("BLUR_THRESHOLD", "30.0"))
    DARK_BRIGHTNESS_THRESHOLD: float = float(os.getenv("DARK_BRIGHTNESS_THRESHOLD", "35.0"))
    BRIGHT_BRIGHTNESS_THRESHOLD: float = float(os.getenv("BRIGHT_BRIGHTNESS_THRESHOLD", "220.0"))

    # Routing engine settings
    ROUTING_SERVICE_URL: str = os.getenv("ROUTING_SERVICE_URL", "")
    ROUTING_TIMEOUT_SECONDS: float = float(os.getenv("ROUTING_TIMEOUT_SECONDS", "2.0"))
    FORCE_ROUTING_FALLBACK: bool = os.getenv("FORCE_ROUTING_FALLBACK", "false").lower() in ("true", "1", "yes")


settings = Settings()
