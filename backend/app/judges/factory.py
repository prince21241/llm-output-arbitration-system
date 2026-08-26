"""Select mock or live judges from settings, without touching routes."""

from __future__ import annotations

from collections.abc import Sequence

from app.config import Settings
from app.judges.base import BaseJudge
from app.judges.claude_judge import ClaudeJudge
from app.judges.gemini_judge import GeminiJudge
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.judges.openai_judge import OpenAIJudge


def build_judges(settings: Settings) -> list[BaseJudge]:
    """Return live judges for configured API keys, otherwise the Phase 1 mocks.

    Tests and key-less local runs keep the deterministic mocks. Setting any of
    OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY registers that
    provider. USE_MOCK_JUDGES=true forces mocks even when keys are present.
    """
    if settings.use_mock_judges:
        return _mock_judges()

    judges: list[BaseJudge] = []
    timeout = settings.judge_timeout_seconds
    max_tokens = settings.judge_max_tokens

    if settings.openai_api_key.strip():
        judges.append(
            OpenAIJudge(
                api_key=settings.openai_api_key.strip(),
                model=settings.openai_model,
                timeout=timeout,
                max_tokens=max_tokens,
            )
        )
    if settings.anthropic_api_key.strip():
        judges.append(
            ClaudeJudge(
                api_key=settings.anthropic_api_key.strip(),
                model=settings.anthropic_model,
                timeout=timeout,
                max_tokens=max_tokens,
            )
        )
    if settings.gemini_api_key.strip():
        judges.append(
            GeminiJudge(
                api_key=settings.gemini_api_key.strip(),
                model=settings.gemini_model,
                timeout=timeout,
                max_tokens=max_tokens,
            )
        )

    return judges or _mock_judges()


def judge_mode(judges: Sequence[BaseJudge]) -> str:
    """Return ``mock`` when every registered judge is a mock, else ``live``."""
    names = [judge.name for judge in judges]
    if names and all(name.startswith("mock_") for name in names):
        return "mock"
    if not names:
        return "mock"
    return "live"


def _mock_judges() -> list[BaseJudge]:
    return [MockJudgeA(), MockJudgeB()]
