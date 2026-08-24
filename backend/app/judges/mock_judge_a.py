"""Deterministic mock judge A."""

from __future__ import annotations

from app.judges.base import BaseJudge
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult, Verdict


class MockJudgeA(BaseJudge):
    """First mock judge with a small, hard-coded knowledge table."""

    def __init__(self) -> None:
        super().__init__(name="mock_judge_a")

    async def evaluate_claim(self, question: str, claim: Claim) -> JudgeResult:
        text = claim.text.lower()
        verdict, confidence, reason = self._lookup(text)
        return JudgeResult(
            judge=self.name,
            claim_id=claim.id,
            verdict=verdict,
            confidence=confidence,
            reason=reason,
        )

    def _lookup(self, text: str) -> tuple[Verdict, float, str]:
        has_first_iphone = "first iphone" in text
        if has_first_iphone and "2005" in text:
            return (
                "incorrect",
                0.95,
                "The first iPhone was released in 2007, not 2005.",
            )
        if has_first_iphone and "2007" in text:
            return (
                "supported",
                0.93,
                "The first iPhone was released in 2007, matching this claim.",
            )
        return (
            "uncertain",
            0.55,
            "Mock judge A has no dedicated knowledge for this claim.",
        )
