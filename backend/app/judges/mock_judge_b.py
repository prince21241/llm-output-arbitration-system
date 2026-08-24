"""Deterministic mock judge B."""

from __future__ import annotations

from app.judges.base import BaseJudge
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult, Verdict


class MockJudgeB(BaseJudge):
    """Second mock judge with slightly different confidence values."""

    def __init__(self) -> None:
        super().__init__(name="mock_judge_b")

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
                0.92,
                "The date conflicts with known information: the first iPhone launched in 2007.",
            )
        if has_first_iphone and "2007" in text:
            return (
                "supported",
                0.88,
                "This matches the commonly cited 2007 iPhone launch year.",
            )
        return (
            "uncertain",
            0.50,
            "Mock judge B cannot verify this claim from its limited table.",
        )
