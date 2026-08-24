"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Provider API keys are optional in Phase 1."""

    app_env: str = "development"
    debug: bool = True
    service_name: str = "llm-output-arbitrator"

    supported_threshold: float = 0.75
    incorrect_threshold: float = 0.35

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    xai_api_key: str = ""
    deepseek_api_key: str = ""
    kimi_api_key: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            debug=_as_bool(os.getenv("DEBUG"), True),
            service_name=os.getenv("SERVICE_NAME", "llm-output-arbitrator"),
            supported_threshold=_as_float(os.getenv("SUPPORTED_THRESHOLD"), 0.75),
            incorrect_threshold=_as_float(os.getenv("INCORRECT_THRESHOLD"), 0.35),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            xai_api_key=os.getenv("XAI_API_KEY", ""),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            kimi_api_key=os.getenv("KIMI_API_KEY", ""),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings.from_env()
