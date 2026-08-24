"""FastAPI application factory and composition root."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.evaluate import router as evaluate_router
from app.config import Settings, get_settings
from app.judges.base import BaseJudge
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.pipeline.claim_extractor import ClaimExtractor
from app.pipeline.consensus import ConsensusEngine
from app.pipeline.evaluator import Evaluator
from app.pipeline.judge_router import JudgeRouter
from app.utils.scoring import RuleBasedScorer

logger = logging.getLogger(__name__)


def build_default_evaluator(
    settings: Settings | None = None,
    judges: Sequence[BaseJudge] | None = None,
) -> Evaluator:
    """Wire Phase 1 defaults. Swap judges or scorer here, not in routes."""
    resolved = settings or get_settings()
    router = JudgeRouter(judges=list(judges) if judges is not None else [MockJudgeA(), MockJudgeB()])
    return Evaluator(
        claim_extractor=ClaimExtractor(),
        judge_router=router,
        consensus_engine=ConsensusEngine(settings=resolved, scorer=RuleBasedScorer()),
        settings=resolved,
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
        version="0.1.0",
        description=(
            "Phase 1 backend: extract claims from an AI answer, collect mock "
            "judge evaluations, and return a preliminary confidence score."
        ),
    )
    app.state.evaluator = evaluator or build_default_evaluator(settings)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

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
