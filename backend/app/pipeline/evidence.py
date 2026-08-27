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
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*|\d+(?:\.\d+)?")
_YEAR = re.compile(r"^(?:1[0-9]{3}|20[0-9]{2}|21[0-9]{2})$")
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "from",
        "by",
        "as",
        "with",
        "that",
        "this",
        "it",
        "its",
        "their",
        "his",
        "her",
        "has",
        "had",
        "have",
        "not",
        "no",
        "yes",
        "than",
        "then",
        "into",
        "over",
        "after",
        "before",
    }
)


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
    """Search Wikipedia and keep the best overlapping extracts per claim."""

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
        query = wikipedia_query(claim.text)
        if not query:
            return []
        try:
            payload = await self._search(query)
        except Exception:
            logger.exception("Wikipedia search failed for %s", claim.id)
            return []
        evidence = self._parse_payload(payload, claim)
        return _rank_evidence(evidence, self._limit)

    async def _search(self, query: str) -> dict[str, object]:
        fetch = max(self._limit, 5)
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query[:300],
            "gsrlimit": str(fetch),
            "prop": "extracts|info",
            "exintro": "1",
            "explaintext": "1",
            "exsentences": "4",
            "inprop": "url",
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

    def _parse_payload(self, payload: dict[str, object], claim: Claim) -> list[Evidence]:
        query = payload.get("query")
        if not isinstance(query, dict):
            return []
        pages = query.get("pages")
        if isinstance(pages, dict):
            return self._from_pages(pages, claim)
        hits = query.get("search")
        if isinstance(hits, list):
            return self._from_search(hits, claim)
        return []

    def _from_pages(self, pages: dict[str, object], claim: Claim) -> list[Evidence]:
        ordered = sorted(
            (
                page
                for page in pages.values()
                if isinstance(page, dict)
            ),
            key=lambda page: int(page.get("index") or 0),
        )
        evidence: list[Evidence] = []
        for page in ordered:
            title = str(page.get("title", "")).strip()
            snippet = _clean_snippet(str(page.get("extract") or page.get("snippet") or ""))
            if not title or not snippet:
                continue
            raw_url = str(page.get("fullurl") or "").strip()
            url = raw_url or self._page_url(title)
            evidence.append(
                Evidence(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="wikipedia",
                    overlap=token_overlap(claim.text, f"{snippet} {title}"),
                )
            )
        return evidence

    def _from_search(self, hits: list[object], claim: Claim) -> list[Evidence]:
        evidence: list[Evidence] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            title = str(hit.get("title", "")).strip()
            snippet = _clean_snippet(str(hit.get("snippet", "")))
            if not title or not snippet:
                continue
            evidence.append(
                Evidence(
                    title=title,
                    url=self._page_url(title),
                    snippet=snippet,
                    source="wikipedia",
                    overlap=token_overlap(claim.text, f"{snippet} {title}"),
                )
            )
        return evidence

    def _page_url(self, title: str) -> str:
        return self._page_base + quote(title.replace(" ", "_"), safe="_()'")


def wikipedia_query(text: str) -> str:
    """Build a tighter Wikipedia search string from a claim."""
    tokens = _WORD_RE.findall(text.strip())
    kept: list[str] = []
    for index, token in enumerate(tokens):
        lower = token.lower()
        if lower in _STOPWORDS and not (index > 0 and token[:1].isupper()):
            continue
        if (
            token[:1].isupper()
            or _YEAR.fullmatch(token)
            or any(char.isdigit() for char in token)
            or (len(lower) > 3 and lower not in _STOPWORDS)
        ):
            kept.append(token)
    query = " ".join(kept).strip()
    if len(query) >= 8:
        return query[:300]
    return text.strip()[:300]


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


def _rank_evidence(evidence: list[Evidence], limit: int) -> list[Evidence]:
    unique: list[Evidence] = []
    seen: set[str] = set()
    for item in sorted(evidence, key=lambda row: row.overlap, reverse=True):
        key = item.title.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    meaningful = [item for item in unique if item.overlap > 0]
    return meaningful[: max(0, limit)]


def _clean_snippet(raw: str) -> str:
    text = unescape(_TAG_RE.sub("", raw))
    return " ".join(text.split()).strip()
