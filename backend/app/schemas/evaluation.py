"""Outbound evaluation models returned by the API."""

from pydantic import BaseModel, Field

from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult, Verdict


class ClaimConsensus(BaseModel):
    """Aggregated judge votes and scores for one claim."""

    claim_id: str
    supporting_votes: int = Field(..., ge=0)
    incorrect_votes: int = Field(..., ge=0)
    uncertain_votes: int = Field(..., ge=0)
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    agreement_score: float = Field(..., ge=0.0, le=1.0)
    disagreement_score: float = Field(..., ge=0.0, le=1.0)
    support_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Preliminary, uncalibrated support score for this claim.",
    )
    verdict: Verdict


class OverallConsensus(BaseModel):
    """Document-level agreement and preliminary support."""

    agreement_score: float = Field(..., ge=0.0, le=1.0)
    support_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Preliminary confidence that the answer is supported.",
    )
    disagreement_score: float = Field(..., ge=0.0, le=1.0)


class EvaluateResponse(BaseModel):
    """Full evaluation payload returned by POST /api/v1/evaluate."""

    question: str
    answer: str
    claims: list[Claim]
    judge_results: list[JudgeResult]
    claim_consensus: list[ClaimConsensus]
    consensus: OverallConsensus
    final_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Preliminary overall confidence score (not a calibrated probability).",
    )
    verdict: Verdict
    scorer: str = Field(
        default="rule",
        description="Scoring strategy used for support_probability (rule or ml).",
    )
