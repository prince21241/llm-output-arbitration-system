"""Wikipedia evidence retrieval tests. HTTP is mocked; no live Wikipedia calls."""

from __future__ import annotations

import httpx
import pytest

from app.config import Settings
from app.judges.llm import user_prompt
from app.judges.mock_judge_a import MockJudgeA
from app.judges.mock_judge_b import MockJudgeB
from app.main import build_default_evaluator
from app.pipeline.evidence import (
    WikipediaEvidenceRetriever,
    token_overlap,
    wikipedia_query,
)
from app.schemas.claim import Claim, Evidence
from conftest import make_test_client

WIKI_BODY = {
    "query": {
        "search": [
            {
                "title": "iPhone",
                "snippet": "The <span class=\"searchmatch\">iPhone</span> is a line of smartphones. The first was released in 2007.",
            }
        ]
    }
}


def test_token_overlap_is_jaccard() -> None:
    assert token_overlap("first iphone released 2005", "first iphone released 2007") > 0.4
    assert token_overlap("alpha", "zzz") == 0.0


def test_wikipedia_query_drops_stopwords() -> None:
    assert wikipedia_query("The first iPhone was released in 2005.") == (
        "first iPhone released 2005"
    )


@pytest.mark.asyncio
async def test_wikipedia_retriever_parses_search_hits() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "wikipedia.org" in str(request.url)
        return httpx.Response(200, json=WIKI_BODY)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        retriever = WikipediaEvidenceRetriever(client=client)
        claim = Claim(id="claim_1", text="The first iPhone was released in 2005.", type="date")
        evidence = await retriever.retrieve(claim)

    assert len(evidence) == 1
    assert evidence[0].title == "iPhone"
    assert evidence[0].source == "wikipedia"
    assert "2007" in evidence[0].snippet
    assert "<span" not in evidence[0].snippet
    assert evidence[0].url.startswith("https://en.wikipedia.org/wiki/")
    assert evidence[0].overlap > 0


@pytest.mark.asyncio
async def test_wikipedia_retriever_uses_extracts_and_ranks_by_overlap() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("gsrsearch") == "first iPhone released 2005"
        assert request.url.params.get("generator") == "search"
        return httpx.Response(
            200,
            json={
                "query": {
                    "pages": {
                        "1": {
                            "pageid": 1,
                            "index": 2,
                            "title": "Unrelated page",
                            "extract": "Totally unrelated astronomy notes.",
                            "fullurl": "https://en.wikipedia.org/wiki/Unrelated_page",
                        },
                        "2": {
                            "pageid": 2,
                            "index": 1,
                            "title": "iPhone",
                            "extract": "The first iPhone was released by Apple in 2007.",
                            "fullurl": "https://en.wikipedia.org/wiki/iPhone",
                        },
                    }
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        retriever = WikipediaEvidenceRetriever(client=client)
        claim = Claim(
            id="claim_1",
            text="The first iPhone was released in 2005.",
            type="date",
        )
        evidence = await retriever.retrieve(claim)

    assert [item.title for item in evidence] == ["iPhone"]
    assert evidence[0].snippet.startswith("The first iPhone")
    assert "2007" in evidence[0].snippet
    assert evidence[0].url == "https://en.wikipedia.org/wiki/iPhone"


@pytest.mark.asyncio
async def test_wikipedia_http_error_returns_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(503, json={"error": "down"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        retriever = WikipediaEvidenceRetriever(client=client)
        claim = Claim(id="claim_1", text="The sky is blue.", type="factual")
        evidence = await retriever.retrieve(claim)

    assert evidence == []


def test_evaluate_attaches_mocked_evidence(tmp_path) -> None:
    class StubRetriever:
        async def retrieve(self, claim: Claim) -> list[Evidence]:
            return [
                Evidence(
                    title="iPhone",
                    url="https://en.wikipedia.org/wiki/iPhone",
                    snippet="The first iPhone launched in 2007.",
                    source="wikipedia",
                    overlap=0.4,
                )
            ]

    evaluator = build_default_evaluator(
        judges=[MockJudgeA(), MockJudgeB()],
        evidence_retriever=StubRetriever(),
        settings=Settings(enable_evidence=True, use_ml_scorer=False),
    )
    client = make_test_client(tmp_path, evaluator=evaluator)
    response = client.post(
        "/api/v1/evaluate",
        json={
            "question": "When was the first iPhone released?",
            "answer": "The first iPhone was released in 2005.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    evidence = body["claims"][0]["evidence"]
    assert evidence[0]["title"] == "iPhone"
    assert "2007" in evidence[0]["snippet"]
    assert body["scorer"] == "rule"


def test_user_prompt_includes_evidence() -> None:
    claim = Claim(
        id="claim_1",
        text="The first iPhone was released in 2005.",
        type="date",
        evidence=[
            Evidence(
                title="iPhone",
                url="https://en.wikipedia.org/wiki/iPhone",
                snippet="Released in 2007.",
                source="wikipedia",
                overlap=0.3,
            )
        ],
    )
    prompt = user_prompt("When was the first iPhone released?", claim)
    assert "Evidence:" in prompt
    assert "Released in 2007." in prompt
    assert "wikipedia.org" in prompt
