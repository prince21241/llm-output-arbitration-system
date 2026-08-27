"""Tests for live-judge JSON parsing."""

from __future__ import annotations

import pytest

from app.judges.llm import JudgeOutputError, parse_judge_output, user_prompt
from app.schemas.claim import Claim


def test_parse_plain_json() -> None:
    verdict, confidence, reason = parse_judge_output(
        '{"verdict":"incorrect","confidence":0.91,"reason":"Launched in 2007."}'
    )
    assert verdict == "incorrect"
    assert confidence == 0.91
    assert "2007" in reason


def test_parse_markdown_fence_and_prose() -> None:
    raw = """Here you go:
```json
{"verdict": "supported", "confidence": 0.8, "reason": "Matches the 2007 launch."}
```
"""
    verdict, confidence, reason = parse_judge_output(raw)
    assert verdict == "supported"
    assert confidence == 0.8
    assert "2007" in reason


def test_parse_clamps_confidence_and_fills_reason() -> None:
    verdict, confidence, reason = parse_judge_output(
        '{"verdict":"uncertain","confidence":1.4,"reason":"  "}'
    )
    assert verdict == "uncertain"
    assert confidence == 1.0
    assert reason == "No reason provided."


def test_parse_rejects_invalid_verdict() -> None:
    with pytest.raises(JudgeOutputError, match="Invalid verdict"):
        parse_judge_output('{"verdict":"wrong","confidence":0.5,"reason":"nope"}')


def test_parse_rejects_empty_and_non_json() -> None:
    with pytest.raises(JudgeOutputError, match="Empty"):
        parse_judge_output("   ")
    with pytest.raises(JudgeOutputError, match="JSON"):
        parse_judge_output("the claim is false")


def test_user_prompt_includes_claim_fields() -> None:
    claim = Claim(id="claim_1", text="The first iPhone was released in 2005.", type="date")
    prompt = user_prompt("When was the first iPhone released?", claim)
    assert "claim_1" in prompt
    assert "date" in prompt
    assert "2005" in prompt
    assert "When was the first iPhone released?" in prompt
