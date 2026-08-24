"""Structured results returned by judge models."""

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["supported", "incorrect", "uncertain"]


class JudgeResult(BaseModel):
    """One judge's evaluation of a single claim."""

    judge: str = Field(..., min_length=1)
    claim_id: str = Field(..., min_length=1)
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)
