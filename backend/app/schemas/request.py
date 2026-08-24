"""Inbound API request models."""

from pydantic import BaseModel, Field, field_validator


class EvaluateRequest(BaseModel):
    """User question plus the AI-generated answer to evaluate."""

    question: str = Field(..., min_length=1, description="The original user question.")
    answer: str = Field(..., min_length=1, description="The AI-generated response to audit.")

    @field_validator("question", "answer")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
