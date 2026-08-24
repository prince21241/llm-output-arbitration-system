"""Orchestrate claim extraction, judging, and consensus."""

from __future__ import annotations

from app.config import Settings
from app.pipeline.claim_extractor import ClaimExtractor
from app.pipeline.consensus import ConsensusEngine
from app.pipeline.judge_router import JudgeRouter
from app.schemas.evaluation import EvaluateResponse
from app.schemas.judge import Verdict
from app.utils.scoring import verdict_from_confidence


class EvaluationError(Exception):
    """Raised when the evaluation pipeline cannot produce a result."""


class Evaluator:
    """High-level pipeline: extract → judge → consensus → verdict.

    Provider-specific judge classes are injected through ``JudgeRouter``.
    Scoring is injected through ``ConsensusEngine``, so a later
    ``MLConfidenceModel`` can replace the rule-based scorer without
    touching this class or the HTTP layer.
    """

    def __init__(
        self,
        claim_extractor: ClaimExtractor,
        judge_router: JudgeRouter,
        consensus_engine: ConsensusEngine,
        settings: Settings,
    ) -> None:
        self._claim_extractor = claim_extractor
        self._judge_router = judge_router
        self._consensus_engine = consensus_engine
        self._settings = settings

    async def evaluate(self, question: str, answer: str) -> EvaluateResponse:
        """Run the full Phase 1 evaluation for one question/answer pair."""
        question = question.strip()
        answer = answer.strip()
        if not question:
            raise EvaluationError("Question must not be blank.")
        if not answer:
            raise EvaluationError("Answer must not be blank.")

        claims = await self._claim_extractor.extract(answer)
        if not claims:
            raise EvaluationError("No claims could be extracted from the answer.")

        judge_results = await self._judge_router.evaluate_claims(question, claims)
        if not judge_results:
            raise EvaluationError("All judges failed to evaluate the extracted claims.")

        claim_consensus = self._consensus_engine.score_claims(claims, judge_results)
        overall = self._consensus_engine.aggregate(claim_consensus)
        verdict: Verdict = verdict_from_confidence(
            overall.support_score,
            self._settings.supported_threshold,
            self._settings.incorrect_threshold,
        )

        return EvaluateResponse(
            question=question,
            answer=answer,
            claims=claims,
            judge_results=judge_results,
            claim_consensus=claim_consensus,
            consensus=overall,
            final_confidence=overall.support_score,
            verdict=verdict,
        )
