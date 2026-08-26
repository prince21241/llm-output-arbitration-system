"""FastAPI application factory and composition root."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.evaluate import router as evaluate_router
from app.config import Settings, get_settings
from app.judges.base import BaseJudge
from app.judges.factory import build_judges
from app.ml.model import MLConfidenceModel
from app.pipeline.claim_extractor import ClaimExtractor
from app.pipeline.consensus import ConsensusEngine
from app.pipeline.evaluator import Evaluator
from app.pipeline.evidence import EvidenceRetriever, NullEvidenceRetriever, WikipediaEvidenceRetriever
from app.pipeline.judge_router import JudgeRouter
from app.utils.scoring import ConfidenceScorer, RuleBasedScorer

logger = logging.getLogger(__name__)


def build_scorer(settings: Settings) -> tuple[ConfidenceScorer, str]:
    """Load the ML scorer when enabled and an artifact exists, else the rule formula."""
    if settings.use_ml_scorer:
        model = MLConfidenceModel.load()
        if model is not None:
            return model, "ml"
    return RuleBasedScorer(), "rule"


def build_evidence_retriever(
    settings: Settings,
    evidence_retriever: EvidenceRetriever | None = None,
) -> EvidenceRetriever:
    if evidence_retriever is not None:
        return evidence_retriever
    if settings.enable_evidence:
        return WikipediaEvidenceRetriever(language=settings.wikipedia_language)
    return NullEvidenceRetriever()


def build_default_evaluator(
    settings: Settings | None = None,
    judges: Sequence[BaseJudge] | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
) -> Evaluator:
    """Wire pipeline defaults. Swap judges or scorer here, not in routes."""
    resolved = settings or get_settings()
    selected = list(judges) if judges is not None else build_judges(resolved)
    scorer, scorer_name = build_scorer(resolved)
    return Evaluator(
        claim_extractor=ClaimExtractor(),
        judge_router=JudgeRouter(judges=selected),
        consensus_engine=ConsensusEngine(settings=resolved, scorer=scorer),
        settings=resolved,
        evidence_retriever=build_evidence_retriever(resolved, evidence_retriever),
        scorer_name=scorer_name,
    )


def create_app(evaluator: Evaluator | None = None) -> FastAPI:
    """Build the FastAPI application with injected pipeline services."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = FastAPI(
        title="LLM Output Arbitration System",
        version="0.3.0",
        description=(
            "Extract claims, retrieve Wikipedia evidence, collect judge "
            "evaluations, and score them with a rule formula or a trained "
            "confidence model."
        ),
    )
    resolved_evaluator = evaluator or build_default_evaluator(settings)
    app.state.evaluator = resolved_evaluator
    logger.info(
        "Registered judges (%s): %s",
        resolved_evaluator.mode,
        ", ".join(resolved_evaluator.judge_names) or "(none)",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, Any]:
        evaluator: Evaluator = app.state.evaluator
        return {
            "status": "ok",
            "service": settings.service_name,
            "mode": evaluator.mode,
            "judges": list(evaluator.judge_names),
            "scorer": evaluator.scorer_name,
            "evidence": evaluator.evidence_enabled,
            "auth": bool(settings.clerk_secret_key),
        }

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content={"detail": _public_validation_errors(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del request
        if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError)):
            raise exc
        logger.exception("Unhandled application error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal evaluation failure."},
        )

    app.include_router(evaluate_router, prefix="/api/v1", tags=["evaluation"])
    return app


def _public_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Return JSON-safe validation errors without leaking exception objects."""
    public: list[dict[str, Any]] = []
    for error in exc.errors():
        loc = error.get("loc", ())
        item: dict[str, Any] = {
            "loc": list(loc),
            "msg": error.get("msg", "Invalid input"),
            "type": error.get("type", "value_error"),
        }
        if "input" in error:
            item["input"] = error["input"]
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            item["ctx"] = {key: str(value) for key, value in ctx.items()}
        public.append(item)
    return public


app = create_app()
