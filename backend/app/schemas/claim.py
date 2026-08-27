"""Claim models produced by the claim extractor."""

from typing import Literal

from pydantic import BaseModel, Field

ClaimType = Literal["factual", "numerical", "date", "unknown"]


class Evidence(BaseModel):
    """One retrieved source used to check a claim."""

    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    snippet: str = Field(..., min_length=1)
    source: str = Field(default="wikipedia", min_length=1)
    overlap: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Token overlap between the claim and this snippet.",
    )


class Claim(BaseModel):
    """A single extracted statement from an AI answer."""

    id: str = Field(..., description="Stable identifier such as claim_1.")
    text: str = Field(..., min_length=1, description="Original claim text.")
    type: ClaimType = Field(..., description="Heuristic claim category.")
    evidence: list[Evidence] = Field(default_factory=list)
