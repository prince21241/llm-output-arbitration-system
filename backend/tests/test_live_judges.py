"""HTTP-backed live judges, using in-process mocked transports only."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.judges.claude_judge import CLAUDE_URL, ClaudeJudge
from app.judges.gemini_judge import GeminiJudge
from app.judges.llm import JudgeOutputError
from app.judges.openai_judge import OPENAI_URL, OpenAIJudge
from app.main import build_default_evaluator, create_app
from app.pipeline.judge_router import JudgeRouter
from app.schemas.claim import Claim

CLAIM = Claim(
    id="claim_1",
    text="The first iPhone was released in 2005.",
    type="date",
)
QUESTION = "When was the first iPhone released?"
VERDICT_JSON = json.dumps(
    {
        "verdict": "incorrect",
        "confidence": 0.91,
        "reason": "The first iPhone launched in 2007, not 2005.",
    }
)


@pytest.mark.asyncio
async def test_openai_judge_parses_chat_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == OPENAI_URL
        assert request.headers["authorization"] == "Bearer sk-test"
        payload = json.loads(request.content)
        assert payload["model"] == "gpt-4o-mini"
        assert payload["response_format"]["type"] == "json_object"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": VERDICT_JSON}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        judge = OpenAIJudge(api_key="sk-test", client=client)
        result = await judge.evaluate_claim(QUESTION, CLAIM)

    assert result.judge == "openai"
    assert result.claim_id == "claim_1"
    assert result.verdict == "incorrect"
    assert result.confidence == 0.91
    assert "2007" in result.reason


@pytest.mark.asyncio
async def test_claude_judge_parses_text_blocks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == CLAUDE_URL
        assert request.headers["x-api-key"] == "ant-test"
        assert request.headers["anthropic-version"] == "2023-06-01"
        payload = json.loads(request.content)
        assert payload["model"] == "claude-haiku-4-5"
        assert payload["system"]
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": VERDICT_JSON}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        judge = ClaudeJudge(api_key="ant-test", client=client)
        result = await judge.evaluate_claim(QUESTION, CLAIM)

    assert result.judge == "claude"
    assert result.verdict == "incorrect"
    assert result.confidence == 0.91


@pytest.mark.asyncio
async def test_gemini_judge_skips_thought_parts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        assert "generativelanguage.googleapis.com" in url
        assert "gemini-2.5-flash" in url
        assert request.headers["x-goog-api-key"] == "gem-test"
        payload = json.loads(request.content)
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"thought": True, "text": "internal scratchpad"},
                                {"text": VERDICT_JSON},
                            ]
                        }
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        judge = GeminiJudge(api_key="gem-test", client=client)
        result = await judge.evaluate_claim(QUESTION, CLAIM)

    assert result.judge == "gemini"
    assert result.verdict == "incorrect"
    assert "internal scratchpad" not in result.reason


@pytest.mark.asyncio
async def test_openai_http_error_is_skipped_by_router() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(500, json={"error": "provider down"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        live = OpenAIJudge(api_key="sk-test", client=client)
        router = JudgeRouter(judges=[live])
        results = await router.evaluate_claims(QUESTION, [CLAIM])

    assert results == []


@pytest.mark.asyncio
async def test_openai_rejects_missing_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json={"choices": [{"message": {}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        judge = OpenAIJudge(api_key="sk-test", client=client)
        with pytest.raises(JudgeOutputError, match="missing message content"):
            await judge.evaluate_claim(QUESTION, CLAIM)


def test_health_reports_live_judge_names() -> None:
    evaluator = build_default_evaluator(settings=Settings(openai_api_key="sk-test"))
    client = TestClient(create_app(evaluator=evaluator))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "live"
    assert body["judges"] == ["openai"]
    assert body["service"] == "llm-output-arbitrator"
