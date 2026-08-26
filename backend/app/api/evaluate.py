"""POST /api/v1/evaluate — thin HTTP adapter over the Evaluator."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import require_auth
from app.pipeline.evaluator import EvaluationError, Evaluator
from app.schemas.evaluation import EvaluateResponse
from app.schemas.request import EvaluateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def get_evaluator(request: Request) -> Evaluator:
    """Resolve the evaluator from application state (dependency injection)."""
    evaluator = getattr(request.app.state, "evaluator", None)
    if evaluator is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal evaluation failure.",
        )
    return evaluator


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Evaluate an AI answer against a user question",
)
async def evaluate_answer(
    payload: EvaluateRequest,
    evaluator: Evaluator = Depends(get_evaluator),
    user_id: str | None = Depends(require_auth),
) -> EvaluateResponse:
    """Extract claims, collect judge opinions, and return consensus."""
    del user_id
    try:
        return await evaluator.evaluate(payload.question, payload.answer)
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
