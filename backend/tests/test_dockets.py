"""Saved dockets are isolated by Clerk user id."""

from __future__ import annotations

from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi.testclient import TestClient

from app.config import get_settings
from conftest import make_test_client

IPHONE_PAYLOAD = {
    "question": "When was the first iPhone released?",
    "answer": "The first iPhone was released in 2005.",
}

SUPPORTED_PAYLOAD = {
    "question": "When was the first iPhone released?",
    "answer": "The first iPhone was released in 2007.",
}


def _sign_in(monkeypatch, user_id: str) -> None:
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.auth.authenticate_request",
        lambda request, options: RequestState(
            status=AuthStatus.SIGNED_IN,
            payload={"sub": user_id},
        ),
    )


def test_dockets_require_sign_in_when_clerk_configured(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.auth.authenticate_request",
        lambda request, options: RequestState(status=AuthStatus.SIGNED_OUT),
    )
    try:
        client = make_test_client(tmp_path)
        response = client.get("/api/v1/dockets")
    finally:
        get_settings.cache_clear()
    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in to evaluate answers."


def test_user_cannot_list_or_delete_another_users_docket(monkeypatch, tmp_path) -> None:
    current = {"id": "user_a"}

    def fake_auth(request, options):
        del request, options
        return RequestState(
            status=AuthStatus.SIGNED_IN,
            payload={"sub": current["id"]},
        )

    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr("app.auth.authenticate_request", fake_auth)
    try:
        client = make_test_client(tmp_path)
        created = client.post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer token-a"},
        )
        assert created.status_code == 200
        docket_id = created.json()["id"]
        assert docket_id

        own = client.get(
            "/api/v1/dockets",
            headers={"Authorization": "Bearer token-a"},
        )
        assert own.status_code == 200
        assert [item["id"] for item in own.json()["dockets"]] == [docket_id]
        assert "user_id" not in own.json()["dockets"][0]
        assert own.json()["dockets"][0]["result"]["question"] == IPHONE_PAYLOAD["question"]

        current["id"] = "user_b"
        other_list = client.get(
            "/api/v1/dockets",
            headers={"Authorization": "Bearer token-b"},
        )
        assert other_list.status_code == 200
        assert other_list.json()["dockets"] == []

        other_get = client.get(
            f"/api/v1/dockets/{docket_id}",
            headers={"Authorization": "Bearer token-b"},
        )
        assert other_get.status_code == 404
        assert other_get.json()["detail"] == "Docket not found."

        other_delete = client.delete(
            f"/api/v1/dockets/{docket_id}",
            headers={"Authorization": "Bearer token-b"},
        )
        assert other_delete.status_code == 404

        current["id"] = "user_a"
        still_there = client.get(
            f"/api/v1/dockets/{docket_id}",
            headers={"Authorization": "Bearer token-a"},
        )
        assert still_there.status_code == 200
        assert still_there.json()["id"] == docket_id
    finally:
        get_settings.cache_clear()


def test_same_question_is_not_shared_across_users(monkeypatch, tmp_path) -> None:
    current = {"id": "user_a"}

    def fake_auth(request, options):
        del request, options
        return RequestState(
            status=AuthStatus.SIGNED_IN,
            payload={"sub": current["id"]},
        )

    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_dummy")
    get_settings.cache_clear()
    monkeypatch.setattr("app.auth.authenticate_request", fake_auth)
    try:
        client = make_test_client(tmp_path)
        first = client.post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer token-a"},
        )
        current["id"] = "user_b"
        second = client.post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer token-b"},
        )
        listed = client.get(
            "/api/v1/dockets",
            headers={"Authorization": "Bearer token-b"},
        )
    finally:
        get_settings.cache_clear()
    assert first.json()["id"] != second.json()["id"]
    assert [item["id"] for item in listed.json()["dockets"]] == [second.json()["id"]]


def test_same_question_updates_existing_docket_for_that_user(monkeypatch, tmp_path) -> None:
    _sign_in(monkeypatch, "user_a")
    try:
        client = make_test_client(tmp_path)
        first = client.post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer token-a"},
        )
        second = client.post(
            "/api/v1/evaluate",
            json=IPHONE_PAYLOAD,
            headers={"Authorization": "Bearer token-a"},
        )
        listed = client.get(
            "/api/v1/dockets",
            headers={"Authorization": "Bearer token-a"},
        )
    finally:
        get_settings.cache_clear()
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(listed.json()["dockets"]) == 1


def test_owner_can_delete_own_docket(monkeypatch, tmp_path) -> None:
    _sign_in(monkeypatch, "user_a")
    try:
        client = make_test_client(tmp_path)
        created = client.post(
            "/api/v1/evaluate",
            json=SUPPORTED_PAYLOAD,
            headers={"Authorization": "Bearer token-a"},
        )
        docket_id = created.json()["id"]
        deleted = client.delete(
            f"/api/v1/dockets/{docket_id}",
            headers={"Authorization": "Bearer token-a"},
        )
        listed = client.get(
            "/api/v1/dockets",
            headers={"Authorization": "Bearer token-a"},
        )
    finally:
        get_settings.cache_clear()
    assert deleted.status_code == 204
    assert listed.json()["dockets"] == []
