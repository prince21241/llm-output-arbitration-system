"""Deterministic claim extraction.

Phase 1 splits answers into sentences and tags them with simple
heuristics. A later LLM-backed extractor can replace this class as
long as it keeps the ``extract`` method signature.
"""

from __future__ import annotations

import re

from app.schemas.claim import Claim, ClaimType

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_YEAR = re.compile(r"\b(?:1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b")
_MONTH = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d")
_ONLY_PUNCTUATION = re.compile(r"^[.!?…\s]+$")


class ClaimExtractor:
    """Split an answer into basic factual claims without calling an LLM."""

    async def extract(self, answer: str) -> list[Claim]:
        """Return ordered claims with stable IDs such as ``claim_1``."""
        sentences = self._split_sentences(answer)
        claims: list[Claim] = []
        for index, sentence in enumerate(sentences, start=1):
            claims.append(
                Claim(
                    id=f"claim_{index}",
                    text=sentence,
                    type=self._classify(sentence),
                )
            )
        return claims

    def _split_sentences(self, answer: str) -> list[str]:
        normalized = " ".join(answer.split()).strip()
        if not normalized:
            return []

        parts = _SENTENCE_SPLIT.split(normalized)
        sentences: list[str] = []
        for part in parts:
            text = part.strip()
            if not text or _ONLY_PUNCTUATION.fullmatch(text):
                continue
            sentences.append(text)
        return sentences

    def _classify(self, text: str) -> ClaimType:
        if _YEAR.search(text) or _MONTH.search(text):
            return "date"
        if _NUMBER.search(text):
            return "numerical"
        words = re.findall(r"[A-Za-z]+", text)
        if len(words) >= 3:
            return "factual"
        return "unknown"
