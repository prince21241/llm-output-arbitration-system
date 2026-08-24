"""Fan-out claims to every registered judge concurrently."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from app.judges.base import BaseJudge
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult

logger = logging.getLogger(__name__)


class JudgeRouter:
    """Dispatch each claim to each judge without coupling to providers."""

    def __init__(self, judges: Sequence[BaseJudge] | None = None) -> None:
        self._judges: list[BaseJudge] = list(judges or [])

    @property
    def judges(self) -> tuple[BaseJudge, ...]:
        return tuple(self._judges)

    def register(self, judge: BaseJudge) -> None:
        """Add a judge at runtime so new providers do not require evaluator changes."""
        self._judges.append(judge)

    async def evaluate_claims(self, question: str, claims: Sequence[Claim]) -> list[JudgeResult]:
        """Evaluate every claim with every judge, in parallel.

        A single judge failure is logged and skipped so the rest of the
        evaluation can still complete.
        """
        if not self._judges:
            return []

        tasks = [
            self._safe_evaluate(judge, question, claim)
            for claim in claims
            for judge in self._judges
        ]
        gathered = await asyncio.gather(*tasks)
        return [result for result in gathered if result is not None]

    async def _safe_evaluate(
        self,
        judge: BaseJudge,
        question: str,
        claim: Claim,
    ) -> JudgeResult | None:
        try:
            return await judge.evaluate_claim(question, claim)
        except Exception:
            logger.exception(
                "Judge %s failed while evaluating %s",
                judge.name,
                claim.id,
            )
            return None
