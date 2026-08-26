"""Shared prompt, JSON parsing, and HTTP helpers for live LLM judges."""

from __future__ import annotations

import json
import re
from abc import abstractmethod

import httpx

from app.judges.base import BaseJudge
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult, Verdict

_VALID_VERDICTS = {"supported", "incorrect", "uncertain"}
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

JUDGE_SYSTEM_PROMPT = """You are a factuality judge. Decide whether one claim from an AI answer is factually correct.

Return JSON only, with this schema:
{"verdict":"supported"|"incorrect"|"uncertain","confidence":<number 0 to 1>,"reason":"<one or two sentences>"}

Rules:
- supported: the claim is factually correct
- incorrect: the claim is factually wrong
- uncertain: you do not have enough knowledge to decide
- confidence is how sure you are of your verdict
- If evidence snippets are provided, prefer them when they clearly confirm or contradict the claim
- If evidence is weak, off-topic, or missing, you may still use training knowledge, and you should say uncertain when you are not sure
- Do not wrap the JSON in markdown.
"""


class JudgeOutputError(ValueError):
    """Raised when a provider response cannot be turned into a JudgeResult."""


class LlmJudge(BaseJudge):
    """Base class for HTTP-backed judges that return structured JSON."""

    def __init__(
        self,
        name: str,
        timeout: float = 20.0,
        max_tokens: int = 256,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(name=name)
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._client = client

    async def evaluate_claim(self, question: str, claim: Claim) -> JudgeResult:
        raw = await self._complete(JUDGE_SYSTEM_PROMPT, user_prompt(question, claim))
        verdict, confidence, reason = parse_judge_output(raw)
        return JudgeResult(
            judge=self.name,
            claim_id=claim.id,
            verdict=verdict,
            confidence=confidence,
            reason=reason,
        )

    @abstractmethod
    async def _complete(self, system: str, user: str) -> str:
        """Call the provider and return the assistant text."""

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
    ) -> httpx.Response:
        timeout = httpx.Timeout(self._timeout, connect=min(5.0, self._timeout))
        if self._client is not None:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        else:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=payload,
                )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise JudgeOutputError(
                f"{self.name} HTTP {exc.response.status_code}"
            ) from exc
        return response


def user_prompt(question: str, claim: Claim) -> str:
    parts = [
        f"Question:\n{question.strip()}",
        f"Claim ID: {claim.id}",
        f"Claim type: {claim.type}",
        f"Claim:\n{claim.text.strip()}",
    ]
    if claim.evidence:
        lines = []
        for index, item in enumerate(claim.evidence, start=1):
            lines.append(
                f"{index}. {item.title} ({item.source})\n{item.snippet}\n{item.url}"
            )
        parts.append("Evidence:\n" + "\n\n".join(lines))
    else:
        parts.append("Evidence:\nNone retrieved.")
    parts.append("Return JSON only.")
    return "\n\n".join(parts)


def parse_judge_output(text: str) -> tuple[Verdict, float, str]:
    """Parse a model completion into a verdict, confidence, and reason."""
    if not text or not str(text).strip():
        raise JudgeOutputError("Empty judge response.")

    payload = _extract_json(str(text))
    verdict = str(payload.get("verdict", "")).strip().lower()
    if verdict not in _VALID_VERDICTS:
        raise JudgeOutputError(f"Invalid verdict: {verdict!r}")

    try:
        confidence = float(payload.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise JudgeOutputError("Invalid confidence.") from exc
    confidence = min(1.0, max(0.0, confidence))

    reason = str(payload.get("reason", "")).strip()
    if not reason:
        reason = "No reason provided."
    return verdict, confidence, reason  # type: ignore[return-value]


def _extract_json(text: str) -> dict[str, object]:
    stripped = _FENCE_RE.sub("", text.strip()).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise JudgeOutputError("Judge response did not contain JSON.")
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise JudgeOutputError("Judge response was not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise JudgeOutputError("Judge JSON must be an object.")
    return parsed
