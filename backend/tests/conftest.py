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
from app.storage.dockets import SqliteDocketStore

get_settings.cache_clear()


def make_test_client(
    tmp_path,
    evaluator=None,
) -> TestClient:
    store = SqliteDocketStore(tmp_path / "dockets.sqlite3")
    resolved = evaluator or build_default_evaluator(
        judges=[MockJudgeA(), MockJudgeB()],
    )
    return TestClient(create_app(evaluator=resolved, docket_store=store))


@pytest.fixture
def client(tmp_path) -> TestClient:
    return make_test_client(tmp_path)
