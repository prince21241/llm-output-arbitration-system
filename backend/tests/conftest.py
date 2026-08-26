"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Keep unit tests on deterministic mocks even if a local .env has live keys.
os.environ["USE_MOCK_JUDGES"] = "true"
os.environ["ENABLE_EVIDENCE"] = "false"
os.environ["USE_ML_SCORER"] = "false"
os.environ["CLERK_SECRET_KEY"] = ""
os.environ["CLERK_JWT_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.main import build_default_evaluator, create_app

get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    evaluator = build_default_evaluator(judges=[MockJudgeA(), MockJudgeB()])
    return TestClient(create_app(evaluator=evaluator))
