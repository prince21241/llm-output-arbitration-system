"""Combine judge results into claim-level and overall consensus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from app.config import Settings
from app.schemas.claim import Claim
from app.schemas.evaluation import ClaimConsensus, OverallConsensus
from app.schemas.judge import JudgeResult
from app.utils.scoring import RuleBasedScorer, clamp, verdict_from_confidence


class ConsensusEngine:
    """Aggregate judge votes using a replaceable scoring strategy."""

    def __init__(
        self,
        settings: Settings,
        scorer: RuleBasedScorer | None = None,
    ) -> None:
        self._settings = settings
        self._scorer = scorer or RuleBasedScorer()

    def score_claims(
        self,
        claims: Sequence[Claim],
        judge_results: Sequence[JudgeResult],
    ) -> list[ClaimConsensus]:
        """Compute consensus statistics for each extracted claim."""
        by_claim: dict[str, list[JudgeResult]] = defaultdict(list)
        for result in judge_results:
            by_claim[result.claim_id].append(result)

        return [self._score_one(claim, by_claim.get(claim.id, [])) for claim in claims]

    def aggregate(self, claim_scores: Sequence[ClaimConsensus]) -> OverallConsensus:
        """Combine claim-level scores into one document-level consensus.

        Overall support is a confidence-weighted average of claim
        support probabilities. That keeps high-certainty claims more
        influential than weakly judged ones.
        """
        if not claim_scores:
            return OverallConsensus(
                agreement_score=0.0,
                support_score=0.5,
                disagreement_score=0.0,
            )

        weights = [max(score.average_confidence, 1e-9) for score in claim_scores]
        weight_sum = sum(weights)
        support = sum(
            score.support_probability * weight
            for score, weight in zip(claim_scores, weights, strict=True)
        ) / weight_sum
        agreement = sum(
            score.agreement_score * weight
            for score, weight in zip(claim_scores, weights, strict=True)
        ) / weight_sum
        disagreement = sum(
            score.disagreement_score * weight
            for score, weight in zip(claim_scores, weights, strict=True)
        ) / weight_sum

        return OverallConsensus(
            agreement_score=round(clamp(agreement), 4),
            support_score=round(clamp(support), 4),
            disagreement_score=round(clamp(disagreement), 4),
        )

    def _score_one(self, claim: Claim, results: Sequence[JudgeResult]) -> ClaimConsensus:
        supporting = sum(1 for item in results if item.verdict == "supported")
        incorrect = sum(1 for item in results if item.verdict == "incorrect")
        uncertain = sum(1 for item in results if item.verdict == "uncertain")
        total = len(results)

        average_confidence = (
            sum(item.confidence for item in results) / total if total else 0.0
        )
        agreement = max(supporting, incorrect, uncertain) / total if total else 0.0
        disagreement = self._disagreement(supporting, incorrect)
        support_probability = self._scorer.support_probability(results)
        verdict = verdict_from_confidence(
            support_probability,
            self._settings.supported_threshold,
            self._settings.incorrect_threshold,
        )

        return ClaimConsensus(
            claim_id=claim.id,
            supporting_votes=supporting,
            incorrect_votes=incorrect,
            uncertain_votes=uncertain,
            average_confidence=round(average_confidence, 4),
            agreement_score=round(agreement, 4),
            disagreement_score=round(disagreement, 4),
            support_probability=support_probability,
            verdict=verdict,
        )

    def _disagreement(self, supporting: int, incorrect: int) -> float:
        decisive = supporting + incorrect
        if decisive == 0:
            return 0.0
        return 1.0 - (abs(supporting - incorrect) / decisive)
