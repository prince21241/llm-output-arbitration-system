"""Retrieve short sources for a claim. Phase 3 uses Wikipedia only."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from html import unescape
from typing import Protocol
from urllib.parse import quote

import httpx

from app.schemas.claim import Claim, Evidence

logger = logging.getLogger(__name__)

WIKIPEDIA_USER_AGENT = (
    "LLMOutputArbitrator/0.3 "
    "(https://github.com/prince21241/llm-output-arbitration-system; "
    "Wikipedia search for claim evidence)"
)
_TAG_RE = re.compile(r"<[^>]+>")
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


class EvidenceRetriever(Protocol):
    """Look up sources for one claim without coupling the evaluator to Wikipedia."""

    async def retrieve(self, claim: Claim) -> list[Evidence]:
        """Return up to a few evidence records, or an empty list on failure."""


class NullEvidenceRetriever:
    """No-op retriever used in tests and when evidence is disabled."""

    async def retrieve(self, claim: Claim) -> list[Evidence]:
        del claim
        return []


class WikipediaEvidenceRetriever:
    """Search the Wikipedia API and keep a lightweight snippet per hit."""

    def __init__(
        self,
        *,
        timeout: float = 8.0,
        limit: int = 3,
        client: httpx.AsyncClient | None = None,
        language: str = "en",
    ) -> None:
        self._timeout = timeout
        self._limit = limit
        self._client = client
        self._api = f"https://{language}.wikipedia.org/w/api.php"
        self._page_base = f"https://{language}.wikipedia.org/wiki/"

    async def retrieve(self, claim: Claim) -> list[Evidence]:
        query = claim.text.strip()
        if not query:
            return []
        try:
            payload = await self._search(query)
        except Exception:
            logger.exception("Wikipedia search failed for %s", claim.id)
            return []
        hits = payload.get("query", {}).get("search", [])
        if not isinstance(hits, list):
            return []
        evidence: list[Evidence] = []
        for hit in hits[: self._limit]:
            if not isinstance(hit, dict):
                continue
            title = str(hit.get("title", "")).strip()
            snippet = _clean_snippet(str(hit.get("snippet", "")))
            if not title or not snippet:
                continue
            url = self._page_base + quote(title.replace(" ", "_"), safe="_()'")
            evidence.append(
                Evidence(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="wikipedia",
                    overlap=token_overlap(claim.text, snippet + " " + title),
                )
            )
        return evidence

    async def _search(self, query: str) -> dict[str, object]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query[:300],
            "srlimit": str(self._limit),
            "srprop": "snippet",
            "format": "json",
            "utf8": "1",
        }
        headers = {
            "User-Agent": WIKIPEDIA_USER_AGENT,
            "Api-User-Agent": WIKIPEDIA_USER_AGENT,
            "Accept": "application/json",
        }
        timeout = httpx.Timeout(self._timeout, connect=min(4.0, self._timeout))
        if self._client is not None:
            response = await self._client.get(
                self._api, params=params, headers=headers, timeout=timeout
            )
        else:
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                response = await client.get(self._api, params=params, headers=headers)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            return {}
        return body


def token_overlap(left: str, right: str) -> float:
    """Jaccard overlap of alphanumeric tokens of length 3+."""
    a = set(_TOKEN_RE.findall(left.lower()))
    b = set(_TOKEN_RE.findall(right.lower()))
    if not a or not b:
        return 0.0
    return round(len(a & b) / len(a | b), 4)


def max_evidence_overlap(evidence: Sequence[Evidence]) -> float:
    if not evidence:
        return 0.0
    return max(item.overlap for item in evidence)


def mean_evidence_overlap(evidence: Sequence[Evidence]) -> float:
    if not evidence:
        return 0.0
    return round(sum(item.overlap for item in evidence) / len(evidence), 4)


def _clean_snippet(raw: str) -> str:
    text = unescape(_TAG_RE.sub("", raw))
    return " ".join(text.split()).strip()
