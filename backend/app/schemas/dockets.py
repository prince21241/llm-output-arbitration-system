"""Saved docket payloads. user_id is never serialized to clients."""

from pydantic import BaseModel, Field

from app.schemas.evaluation import EvaluateResponse


class SavedDocket(BaseModel):
    """One docket owned by the signed-in user."""

    id: str
    saved_at: str
    result: EvaluateResponse


class DocketListResponse(BaseModel):
    """Dockets for the current user only."""

    dockets: list[SavedDocket] = Field(default_factory=list)
