"""Claim models produced by the claim extractor."""

from typing import Literal

from pydantic import BaseModel, Field

ClaimType = Literal["factual", "numerical", "date", "unknown"]


class Claim(BaseModel):
    """A single extracted statement from an AI answer."""

    id: str = Field(..., description="Stable identifier such as claim_1.")
    text: str = Field(..., min_length=1, description="Original claim text.")
    type: ClaimType = Field(..., description="Heuristic claim category.")
