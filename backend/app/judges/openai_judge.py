"""OpenAI Chat Completions judge."""

from __future__ import annotations

import httpx

from app.judges.llm import JudgeOutputError, LlmJudge

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIJudge(LlmJudge):
    """Evaluate claims with an OpenAI chat model."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 20.0,
        max_tokens: int = 256,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            name="openai",
            timeout=timeout,
            max_tokens=max_tokens,
            client=client,
        )
        self._api_key = api_key
        self._model = model

    async def _complete(self, system: str, user: str) -> str:
        response = await self._request(
            "POST",
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": self._model,
                "temperature": 0,
                "max_tokens": self._max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise JudgeOutputError("OpenAI response was missing message content.") from exc
        if not isinstance(content, str):
            raise JudgeOutputError("OpenAI response content was not text.")
        return content
