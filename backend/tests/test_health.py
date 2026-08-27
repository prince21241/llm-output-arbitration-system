"""Health endpoint tests."""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "llm-output-arbitrator",
        "mode": "mock",
        "judges": ["mock_judge_a", "mock_judge_b"],
        "scorer": "rule",
        "evidence": False,
        "auth": False,
        "storage": "sqlite",
    }


def test_cors_allows_local_frontend(client: TestClient) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
