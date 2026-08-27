"""POST /api/v1/evaluate — thin HTTP adapter over the Evaluator."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_docket_store, get_evaluator
from app.auth import require_auth
from app.pipeline.evaluator import EvaluationError, Evaluator
from app.schemas.evaluation import EvaluateResponse
from app.schemas.request import EvaluateRequest
from app.storage.dockets import DocketStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    response_model_exclude_none=True,
    summary="Evaluate an AI answer against a user question",
)
async def evaluate_answer(
    payload: EvaluateRequest,
    evaluator: Evaluator = Depends(get_evaluator),
    store: DocketStore = Depends(get_docket_store),
    user_id: str | None = Depends(require_auth),
) -> EvaluateResponse:
    """Extract claims, collect judge opinions, and return consensus."""
    try:
        result = await evaluator.evaluate(payload.question, payload.answer)
    except EvaluationError as exc:
        logger.warning("Evaluation rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    except Exception:
        logger.exception("Unexpected evaluation failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal evaluation failure.",
        ) from None

    if not user_id:
        return result

    try:
        saved = store.upsert(user_id, result)
    except Exception:
        logger.exception("Failed to persist docket for user")
        return result

    return result.model_copy(update={"id": saved.id, "saved_at": saved.saved_at})
