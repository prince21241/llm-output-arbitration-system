"""Clerk session-token tests for the evaluate route."""

from __future__ import annotations

from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi.testclient import TestClient

from app.config import get_settings
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.main import build_default_evaluator, create_app

IPHONE_PAYLOAD = {
    "question": "When was the first iPhone released?",
    "answer": "The first iPhone was released in 2005.",
}


def _client() -> TestClient:
    evaluator = build_default_evaluator(judges=[MockJudgeA(), MockJudgeB()])
    return TestClient(create_app(evaluator=evaluator))


def test_evaluate_stays_public_without_clerk_secret(client: TestClient) -> None:
    response = client.post("/api/v1/evaluate", json=IPHONE_PAYLOAD)
    assert response.status_code == 200


def test_evaluate_rejects_missing_token_when_clerk_configured(monkeypatch) -> None:
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.auth.authenticate_request",
        lambda request, options: RequestState(status=AuthStatus.SIGNED_OUT),
    )
    try:
        response = _client().post("/api/v1/evaluate", json=IPHONE_PAYLOAD)
    finally:
        get_settings.cache_clear()
    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in to evaluate answers."


def test_evaluate_accepts_signed_in_clerk_user(monkeypatch) -> None:
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.auth.authenticate_request",
        lambda request, options: RequestState(
            status=AuthStatus.SIGNED_IN,
            payload={"sub": "user_test"},
        ),
    )
    try:
        response = _client().post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer test-token"},
        )
    finally:
        get_settings.cache_clear()
    assert response.status_code == 200
    assert response.json()["question"] == IPHONE_PAYLOAD["question"]
