"""Google Gemini generateContent judge."""

from __future__ import annotations

import httpx

from app.judges.llm import JudgeOutputError, LlmJudge

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiJudge(LlmJudge):
    """Evaluate claims with a Gemini model."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: float = 20.0,
        max_tokens: int = 256,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            name="gemini",
            timeout=timeout,
            max_tokens=max_tokens,
            client=client,
        )
        self._api_key = api_key
        self._model = model

    async def _complete(self, system: str, user: str) -> str:
        url = GEMINI_URL_TEMPLATE.format(model=self._model)
        response = await self._request(
            "POST",
            url,
            headers={
                "x-goog-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            payload={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": self._max_tokens,
                    "responseMimeType": "application/json",
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
        )
        body = response.json()
        feedback = body.get("promptFeedback") or {}
        if isinstance(feedback, dict) and feedback.get("blockReason"):
            raise JudgeOutputError("Gemini blocked the prompt.")
        try:
            parts = body["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise JudgeOutputError("Gemini response was missing candidates.") from exc
        texts: list[str] = []
        if isinstance(parts, list):
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if part.get("thought"):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text)
        if not texts:
            raise JudgeOutputError("Gemini response had no text parts.")
        return "\n".join(texts)
