"""End-to-end evaluate API and judge-router tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.judges.base import BaseJudge
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.main import build_default_evaluator
from conftest import make_test_client
from app.pipeline.judge_router import JudgeRouter
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult

IPHONE_PAYLOAD = {
    "question": "When was the first iPhone released?",
    "answer": "The first iPhone was released in 2005.",
}


class FailingJudge(BaseJudge):
    def __init__(self) -> None:
        super().__init__(name="failing_judge")

    async def evaluate_claim(self, question: str, claim: Claim) -> JudgeResult:
        raise RuntimeError("simulated judge outage")


def test_empty_inputs_are_rejected(client: TestClient) -> None:
    missing = client.post("/api/v1/evaluate", json={})
    assert missing.status_code == 422

    blank_question = client.post(
        "/api/v1/evaluate",
        json={"question": "   ", "answer": "Some answer."},
    )
    assert blank_question.status_code == 422

    blank_answer = client.post(
        "/api/v1/evaluate",
        json={"question": "A question?", "answer": ""},
    )
    assert blank_answer.status_code == 422

    missing_answer = client.post(
        "/api/v1/evaluate",
        json={"question": "A question?"},
    )
    assert missing_answer.status_code == 422


def test_evaluate_returns_structured_json(client: TestClient) -> None:
    response = client.post("/api/v1/evaluate", json=IPHONE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()

    assert body["question"] == IPHONE_PAYLOAD["question"]
    assert body["answer"] == IPHONE_PAYLOAD["answer"]
    assert isinstance(body["claims"], list) and body["claims"]
    assert isinstance(body["judge_results"], list) and body["judge_results"]
    assert isinstance(body["claim_consensus"], list) and body["claim_consensus"]
    assert set(body["consensus"]) == {
        "agreement_score",
        "support_score",
        "disagreement_score",
    }
    assert "final_confidence" in body
    assert body["verdict"] in {"supported", "incorrect", "uncertain"}

    claim = body["claims"][0]
    assert claim["id"] == "claim_1"
    assert "2005" in claim["text"]
    assert claim["type"] in {"factual", "numerical", "date", "unknown"}

    for result in body["judge_results"]:
        assert set(result) == {"judge", "claim_id", "verdict", "confidence", "reason"}
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["verdict"] in {"supported", "incorrect", "uncertain"}


def test_iphone_2005_is_incorrect_with_low_confidence(client: TestClient) -> None:
    response = client.post("/api/v1/evaluate", json=IPHONE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "incorrect"
    assert body["final_confidence"] <= 0.35
    assert body["consensus"]["support_score"] <= 0.35
    assert body["consensus"]["agreement_score"] == 1.0


@pytest.mark.asyncio
async def test_mock_judges_are_deterministic() -> None:
    claim = Claim(
        id="claim_1",
        text="The first iPhone was released in 2005.",
        type="date",
    )
    result_a = await MockJudgeA().evaluate_claim("When was the first iPhone released?", claim)
    result_b = await MockJudgeB().evaluate_claim("When was the first iPhone released?", claim)

    assert result_a.verdict == "incorrect"
    assert result_a.confidence == 0.95
    assert "2007" in result_a.reason
    assert result_b.verdict == "incorrect"
    assert result_b.confidence == 0.92
    assert result_a.confidence != result_b.confidence

    again_a = await MockJudgeA().evaluate_claim("When was the first iPhone released?", claim)
    assert again_a.model_dump() == result_a.model_dump()


@pytest.mark.asyncio
async def test_multiple_judges_execute_successfully() -> None:
    claim = Claim(id="claim_1", text="The sky is blue.", type="factual")
    router = JudgeRouter(judges=[MockJudgeA(), MockJudgeB()])
    results = await router.evaluate_claims("What color is the sky?", [claim])
    judges = {item.judge for item in results}
    assert judges == {"mock_judge_a", "mock_judge_b"}
    assert len(results) == 2


@pytest.mark.asyncio
async def test_judge_failure_does_not_crash_pipeline() -> None:
    claim = Claim(
        id="claim_1",
        text="The first iPhone was released in 2005.",
        type="date",
    )
    router = JudgeRouter(judges=[MockJudgeA(), FailingJudge(), MockJudgeB()])
    results = await router.evaluate_claims("When was the first iPhone released?", [claim])
    assert {item.judge for item in results} == {"mock_judge_a", "mock_judge_b"}
    assert all(item.verdict == "incorrect" for item in results)


def test_evaluate_survives_one_failed_judge(tmp_path) -> None:
    evaluator = build_default_evaluator(
        judges=[MockJudgeA(), FailingJudge(), MockJudgeB()],
    )
    client = make_test_client(tmp_path, evaluator=evaluator)
    response = client.post("/api/v1/evaluate", json=IPHONE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "incorrect"
    judges = {item["judge"] for item in body["judge_results"]}
    assert "failing_judge" not in judges
    assert "mock_judge_a" in judges
    assert "mock_judge_b" in judges
