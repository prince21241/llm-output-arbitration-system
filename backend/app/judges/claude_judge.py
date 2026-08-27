"""Anthropic Messages API judge."""

from __future__ import annotations

import httpx

from app.judges.llm import JudgeOutputError, LlmJudge

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class ClaudeJudge(LlmJudge):
    """Evaluate claims with a Claude model."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5",
        timeout: float = 20.0,
        max_tokens: int = 256,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            name="claude",
            timeout=timeout,
            max_tokens=max_tokens,
            client=client,
        )
        self._api_key = api_key
        self._model = model

    async def _complete(self, system: str, user: str) -> str:
        response = await self._request(
            "POST",
            CLAUDE_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            payload={
                "model": self._model,
                "max_tokens": self._max_tokens,
                "temperature": 0,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        body = response.json()
        blocks = body.get("content")
        if not isinstance(blocks, list):
            raise JudgeOutputError("Claude response was missing content.")
        texts: list[str] = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text)
        if not texts:
            raise JudgeOutputError("Claude response had no text blocks.")
        return "\n".join(texts)
