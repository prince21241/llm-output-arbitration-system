"""Orchestrate claim extraction, evidence, judging, and consensus."""

from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.pipeline.claim_extractor import ClaimExtractor
from app.pipeline.consensus import ConsensusEngine
from app.pipeline.evidence import EvidenceRetriever, NullEvidenceRetriever
from app.pipeline.judge_router import JudgeRouter
from app.schemas.evaluation import EvaluateResponse
from app.schemas.judge import Verdict
from app.utils.scoring import verdict_from_confidence

logger = logging.getLogger(__name__)


class EvaluationError(Exception):
    """Raised when the evaluation pipeline cannot produce a result."""


class Evaluator:
    """High-level pipeline: extract → evidence → judge → consensus → verdict.

    Provider-specific judge classes are injected through ``JudgeRouter``.
    Scoring is injected through ``ConsensusEngine``, so ``MLConfidenceModel``
    can replace the rule-based scorer without touching this class or HTTP.
    """

    def __init__(
        self,
        claim_extractor: ClaimExtractor,
        judge_router: JudgeRouter,
        consensus_engine: ConsensusEngine,
        settings: Settings,
        evidence_retriever: EvidenceRetriever | None = None,
        scorer_name: str = "rule",
    ) -> None:
        self._claim_extractor = claim_extractor
        self._judge_router = judge_router
        self._consensus_engine = consensus_engine
        self._settings = settings
        self._evidence_retriever = evidence_retriever or NullEvidenceRetriever()
        self._scorer_name = scorer_name

    @property
    def judge_names(self) -> tuple[str, ...]:
        """Stable identifiers of judges currently registered on the router."""
        return tuple(judge.name for judge in self._judge_router.judges)

    @property
    def mode(self) -> str:
        """Return ``mock`` when every registered judge is a mock, else ``live``."""
        names = self.judge_names
        if names and all(name.startswith("mock_") for name in names):
            return "mock"
        return "live" if names else "mock"

    @property
    def scorer_name(self) -> str:
        return self._scorer_name

    @property
    def evidence_enabled(self) -> bool:
        return not isinstance(self._evidence_retriever, NullEvidenceRetriever)

    async def evaluate(self, question: str, answer: str) -> EvaluateResponse:
        """Run the full evaluation for one question/answer pair."""
        question = question.strip()
        answer = answer.strip()
        if not question:
            raise EvaluationError("Question must not be blank.")
        if not answer:
            raise EvaluationError("Answer must not be blank.")

        claims = await self._claim_extractor.extract(answer)
        if not claims:
            raise EvaluationError("No claims could be extracted from the answer.")

        claims = await self._attach_evidence(claims)
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
            scorer=self._scorer_name,
        )

    async def _attach_evidence(self, claims: list) -> list:
        gathered = await asyncio.gather(
            *[self._evidence_retriever.retrieve(claim) for claim in claims],
            return_exceptions=True,
        )
        attached = []
        for claim, result in zip(claims, gathered, strict=True):
            if isinstance(result, Exception):
                logger.exception("Evidence lookup failed for %s: %s", claim.id, result)
                attached.append(claim.model_copy(update={"evidence": []}))
            else:
                attached.append(claim.model_copy(update={"evidence": result}))
        return attached
