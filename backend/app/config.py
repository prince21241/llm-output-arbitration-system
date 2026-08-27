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


def _as_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Provider API keys enable Phase 2 live judges."""

    app_env: str = "development"
    debug: bool = True
    service_name: str = "llm-output-arbitrator"

    supported_threshold: float = 0.75
    incorrect_threshold: float = 0.35

    use_mock_judges: bool = False
    judge_timeout_seconds: float = 20.0
    judge_max_tokens: int = 256

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    xai_api_key: str = ""
    deepseek_api_key: str = ""
    kimi_api_key: str = ""

    enable_evidence: bool = True
    use_ml_scorer: bool = True
    wikipedia_language: str = "en"

    clerk_secret_key: str = ""
    clerk_jwt_key: str = ""
    clerk_authorized_parties: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )
    database_path: str = "data/arbitrator.sqlite3"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            debug=_as_bool(os.getenv("DEBUG"), True),
            service_name=os.getenv("SERVICE_NAME", "llm-output-arbitrator"),
            supported_threshold=_as_float(os.getenv("SUPPORTED_THRESHOLD"), 0.75),
            incorrect_threshold=_as_float(os.getenv("INCORRECT_THRESHOLD"), 0.35),
            use_mock_judges=_as_bool(os.getenv("USE_MOCK_JUDGES"), False),
            judge_timeout_seconds=_as_float(os.getenv("JUDGE_TIMEOUT_SECONDS"), 20.0),
            judge_max_tokens=_as_int(os.getenv("JUDGE_MAX_TOKENS"), 256),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            xai_api_key=os.getenv("XAI_API_KEY", ""),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            kimi_api_key=os.getenv("KIMI_API_KEY", ""),
            enable_evidence=_as_bool(os.getenv("ENABLE_EVIDENCE"), True),
            use_ml_scorer=_as_bool(os.getenv("USE_ML_SCORER"), True),
            wikipedia_language=os.getenv("WIKIPEDIA_LANGUAGE", "en"),
            clerk_secret_key=os.getenv("CLERK_SECRET_KEY", "").strip(),
            clerk_jwt_key=_clerk_jwt_key(),
            clerk_authorized_parties=_clerk_authorized_parties(),
            database_path=os.getenv("DATABASE_PATH", "data/arbitrator.sqlite3").strip()
            or "data/arbitrator.sqlite3",
        )


def _clerk_jwt_key() -> str:
    raw = os.getenv("CLERK_JWT_KEY", "")
    return raw.replace("\\n", "\n").strip()


def _clerk_authorized_parties() -> tuple[str, ...]:
    raw = os.getenv(
        "CLERK_AUTHORIZED_PARTIES",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    parties = tuple(part.strip() for part in raw.split(",") if part.strip())
    return parties or (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings.from_env()
