"""Replaceable preliminary scoring helpers.

Phase 1 uses a transparent signed-confidence rule. Later phases can
swap ``RuleBasedScorer`` for ``MLConfidenceModel.predict(features)``
without changing the FastAPI route.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult, Verdict


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Restrict ``value`` to the inclusive range [lower, upper]."""
    return max(lower, min(upper, value))


def signed_contribution(verdict: Verdict, confidence: float) -> float:
    """Map a judge verdict onto a signed confidence contribution.

    supported  → +confidence
    incorrect  → -confidence
    uncertain  → 0
    """
    if verdict == "supported":
        return confidence
    if verdict == "incorrect":
        return -confidence
    return 0.0


def verdict_from_confidence(
    confidence: float,
    supported_threshold: float,
    incorrect_threshold: float,
) -> Verdict:
    """Convert a preliminary confidence score into a discrete verdict."""
    if confidence >= supported_threshold:
        return "supported"
    if confidence <= incorrect_threshold:
        return "incorrect"
    return "uncertain"


class ConfidenceScorer(Protocol):
    """Scoring strategy used by the consensus engine.

    A future ``MLConfidenceModel`` should implement this same method
    (or wrap ``predict`` behind it) so the evaluator stays unchanged.
    """

    def support_probability(
        self,
        results: Sequence[JudgeResult],
        claim: Claim | None = None,
    ) -> float:
        """Return a preliminary support score in [0, 1]."""


class RuleBasedScorer:
    """Deterministic Phase 1 scorer.

    Signed contributions are averaged, then linearly mapped from
    [-1, 1] into [0, 1]:

        support_probability = (mean(signed) + 1) / 2

    This is **not** a calibrated probability.
    """

    def support_probability(
        self,
        results: Sequence[JudgeResult],
        claim: Claim | None = None,
    ) -> float:
        del claim
        if not results:
            return 0.5
        total = sum(signed_contribution(item.verdict, item.confidence) for item in results)
        mean_signed = total / len(results)
        return round(clamp((mean_signed + 1.0) / 2.0), 4)
