"""Deterministic claim extraction.

Splits answers into checkable statements and tags them with simple
heuristics. A later LLM-backed extractor can replace this class as
long as it keeps the ``extract`` method signature.
"""

from __future__ import annotations

import re

from app.schemas.claim import Claim, ClaimType

MAX_CLAIMS = 12
_YEAR = re.compile(r"\b(?:1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b")
_MONTH = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d")
_ONLY_PUNCTUATION = re.compile(r"^[.!?…\s]+$")
_QUESTION_START = re.compile(
    r"^(?:who|what|when|where|why|how|is|are|was|were|do|does|did|can|could|"
    r"should|would)\b",
    re.IGNORECASE,
)
_ABBREVIATIONS = re.compile(
    r"\b(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|vs|etc|Inc|Ltd|St|No|Fig|approx|al)\.",
    re.IGNORECASE,
)
_DOTTED_ABBREV = re.compile(r"\b(?:e\.g|i\.e|U\.S|U\.K|U\.N)\.", re.IGNORECASE)
_DECIMAL = re.compile(r"\b\d+\.\d+\b")
_SPLIT = re.compile(r"(?<=[.!?])\s+|\s*;\s+|\n+")
_HOLDER = re.compile(r"\x00(\d+)\x00")


class ClaimExtractor:
    """Split an answer into basic factual claims without calling an LLM."""

    async def extract(self, answer: str) -> list[Claim]:
        """Return ordered claims with stable IDs such as ``claim_1``."""
        statements = self._split_statements(answer)
        claims: list[Claim] = []
        for index, sentence in enumerate(statements[:MAX_CLAIMS], start=1):
            claims.append(
                Claim(
                    id=f"claim_{index}",
                    text=sentence,
                    type=self._classify(sentence),
                )
            )
        return claims

    def _split_statements(self, answer: str) -> list[str]:
        blocks = [block.strip() for block in re.split(r"\n+", answer) if block.strip()]
        sentences: list[str] = []
        for block in blocks or [answer]:
            normalized = " ".join(block.split()).strip()
            if not normalized:
                continue
            protected, holders = _protect(normalized)
            for part in _SPLIT.split(protected):
                text = _restore(part, holders).strip().strip("\"'")
                if not text or _ONLY_PUNCTUATION.fullmatch(text):
                    continue
                if _is_question(text):
                    continue
                sentences.extend(_split_contrast_clauses(text))
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


def _protect(text: str) -> tuple[str, list[str]]:
    holders: list[str] = []

    def stash(match: re.Match[str]) -> str:
        holders.append(match.group(0))
        return f"\x00{len(holders) - 1}\x00"

    protected = _DECIMAL.sub(stash, text)
    protected = _DOTTED_ABBREV.sub(stash, protected)
    protected = _ABBREVIATIONS.sub(stash, protected)
    return protected, holders


def _restore(text: str, holders: list[str]) -> str:
    return _HOLDER.sub(lambda match: holders[int(match.group(1))], text)


def _is_question(text: str) -> bool:
    stripped = text.strip()
    if stripped.endswith("?") and _QUESTION_START.match(stripped):
        return True
    return False


def _split_contrast_clauses(sentence: str) -> list[str]:
    lower = sentence.lower()
    marker = " but "
    index = lower.find(marker)
    if index < 0:
        return [_ensure_period(sentence)]
    left = sentence[:index].strip(" ,")
    right = sentence[index + len(marker) :].strip()
    if len(left.split()) < 5 or len(right.split()) < 5:
        return [_ensure_period(sentence)]
    if right and right[0].islower():
        right = right[0].upper() + right[1:]
    return [_ensure_period(left), _ensure_period(right)]


def _ensure_period(text: str) -> str:
    stripped = text.strip()
    if stripped.endswith((".", "!", "?")):
        return stripped
    return f"{stripped}."
