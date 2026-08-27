"""Shared FastAPI dependencies. Routes stay free of construction details."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.pipeline.evaluator import Evaluator
from app.storage.dockets import DocketStore


def get_evaluator(request: Request) -> Evaluator:
    evaluator = getattr(request.app.state, "evaluator", None)
    if evaluator is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal evaluation failure.",
        )
    return evaluator


def get_docket_store(request: Request) -> DocketStore:
    store = getattr(request.app.state, "docket_store", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal evaluation failure.",
        )
    return store
