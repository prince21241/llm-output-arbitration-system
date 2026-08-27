"""Tests for live vs mock judge selection."""

from __future__ import annotations

from app.config import Settings
from app.judges.claude_judge import ClaudeJudge
from app.judges.factory import build_judges, judge_mode
from app.judges.gemini_judge import GeminiJudge
from app.judges.openai_judge import OpenAIJudge


def test_no_keys_uses_mocks() -> None:
    judges = build_judges(Settings())
    assert [judge.name for judge in judges] == ["mock_judge_a", "mock_judge_b"]
    assert judge_mode(judges) == "mock"


def test_whitespace_keys_are_ignored() -> None:
    judges = build_judges(Settings(openai_api_key="   ", gemini_api_key="\n"))
    assert [judge.name for judge in judges] == ["mock_judge_a", "mock_judge_b"]


def test_each_key_registers_its_provider() -> None:
    openai = build_judges(Settings(openai_api_key="sk-test"))
    assert len(openai) == 1
    assert isinstance(openai[0], OpenAIJudge)
    assert judge_mode(openai) == "live"

    claude = build_judges(Settings(anthropic_api_key="ant-test"))
    assert len(claude) == 1
    assert isinstance(claude[0], ClaudeJudge)

    gemini = build_judges(Settings(gemini_api_key="gem-test"))
    assert len(gemini) == 1
    assert isinstance(gemini[0], GeminiJudge)


def test_all_keys_register_three_live_judges() -> None:
    judges = build_judges(
        Settings(
            openai_api_key="sk-test",
            anthropic_api_key="ant-test",
            gemini_api_key="gem-test",
        )
    )
    assert [judge.name for judge in judges] == ["openai", "claude", "gemini"]
    assert judge_mode(judges) == "live"


def test_use_mock_judges_overrides_keys() -> None:
    judges = build_judges(
        Settings(openai_api_key="sk-test", use_mock_judges=True)
    )
    assert [judge.name for judge in judges] == ["mock_judge_a", "mock_judge_b"]
    assert judge_mode(judges) == "mock"
