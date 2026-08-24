"""Abstract judge interface.

Every provider (mock or live) implements ``evaluate_claim`` so the
router and evaluator never depend on a specific vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult


class BaseJudge(ABC):
    """Common contract for all claim-evaluation judges."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        """Stable identifier recorded on each ``JudgeResult``."""
        return self._name

    @abstractmethod
    async def evaluate_claim(self, question: str, claim: Claim) -> JudgeResult:
        """Evaluate one claim in the context of the original question."""
