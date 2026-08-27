"""Labeled vote patterns used to train the confidence model.

Rows come from three sources, all offline and deterministic:

1. Hand-written templates that cover clear agreement, splits, and traps.
2. A seeded sampler that expands those patterns across judge counts and evidence.
3. Gold labels from ``backend/data/seed_eval.json``, mapped to vote/evidence
   features without calling paid judge APIs.

Retrain with ``python -m app.ml.train``. Replace the synthetic votes after
live judges produce real labels.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from pathlib import Path

from app.ml.features import extract_features, label_index
from app.schemas.claim import Claim, Evidence
from app.schemas.judge import JudgeResult, Verdict

_VOTE = tuple[Verdict, float]
_Gold = str
_SEED_EVAL_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_eval.json"
_RNG_SEED = 7

_TEMPLATES: list[tuple[list[_VOTE], int, float, _Gold]] = [
    ([("incorrect", 0.95), ("incorrect", 0.92)], 2, 0.35, "incorrect"),
    ([("incorrect", 0.88), ("incorrect", 0.84), ("incorrect", 0.9)], 3, 0.4, "incorrect"),
    ([("incorrect", 0.7)], 1, 0.5, "incorrect"),
    ([("supported", 0.93), ("supported", 0.88)], 2, 0.55, "supported"),
    ([("supported", 0.8), ("supported", 0.82), ("supported", 0.79)], 3, 0.6, "supported"),
    ([("supported", 0.72)], 1, 0.45, "supported"),
    ([("uncertain", 0.55), ("uncertain", 0.5)], 0, 0.0, "uncertain"),
    ([("uncertain", 0.4), ("uncertain", 0.45), ("uncertain", 0.42)], 1, 0.15, "uncertain"),
    ([("supported", 0.85), ("incorrect", 0.85)], 1, 0.2, "uncertain"),
    ([("supported", 0.7), ("incorrect", 0.68), ("uncertain", 0.5)], 1, 0.1, "uncertain"),
    ([("supported", 0.9), ("uncertain", 0.5)], 2, 0.3, "uncertain"),
    ([("incorrect", 0.9), ("uncertain", 0.4)], 2, 0.25, "incorrect"),
    ([("supported", 0.6), ("supported", 0.58), ("incorrect", 0.9)], 0, 0.0, "uncertain"),
    # Correlated judges can all be wrong when evidence is missing.
    ([("supported", 0.75), ("supported", 0.72), ("supported", 0.7)], 0, 0.0, "incorrect"),
    ([("incorrect", 0.65), ("incorrect", 0.6)], 3, 0.7, "incorrect"),
    ([("supported", 0.55), ("supported", 0.52)], 3, 0.65, "supported"),
    ([("uncertain", 0.6), ("supported", 0.9)], 3, 0.5, "supported"),
    ([("uncertain", 0.6), ("incorrect", 0.92)], 3, 0.55, "incorrect"),
    ([("supported", 0.95), ("incorrect", 0.4)], 2, 0.5, "supported"),
    ([("incorrect", 0.95), ("supported", 0.4)], 2, 0.15, "incorrect"),
    ([("supported", 0.91), ("supported", 0.88), ("supported", 0.86), ("supported", 0.9)], 3, 0.7, "supported"),
    ([("incorrect", 0.93), ("incorrect", 0.9), ("incorrect", 0.87), ("incorrect", 0.91)], 2, 0.25, "incorrect"),
    ([("supported", 0.82), ("supported", 0.8), ("incorrect", 0.78), ("incorrect", 0.76)], 1, 0.2, "uncertain"),
    ([("supported", 0.88), ("supported", 0.84), ("supported", 0.8), ("incorrect", 0.7)], 3, 0.55, "supported"),
    ([("incorrect", 0.88), ("incorrect", 0.84), ("incorrect", 0.8), ("supported", 0.7)], 2, 0.2, "incorrect"),
    ([("uncertain", 0.5), ("uncertain", 0.48), ("supported", 0.62), ("incorrect", 0.61)], 1, 0.12, "uncertain"),
    ([("supported", 0.78), ("supported", 0.74), ("supported", 0.71), ("uncertain", 0.4)], 0, 0.0, "incorrect"),
    ([("incorrect", 0.58), ("incorrect", 0.55), ("uncertain", 0.5)], 3, 0.62, "supported"),
]


def _results(votes: list[_VOTE]) -> list[JudgeResult]:
    return [
        JudgeResult(
            judge=f"judge_{index}",
            claim_id="claim_1",
            verdict=verdict,
            confidence=confidence,
            reason="seed",
        )
        for index, (verdict, confidence) in enumerate(votes, start=1)
    ]


def _claim(n_evidence: int, overlap: float) -> Claim:
    evidence = [
        Evidence(
            title=f"Source {index}",
            url=f"https://example.invalid/{index}",
            snippet="Background snippet used only for overlap features.",
            source="seed",
            overlap=overlap,
        )
        for index in range(n_evidence)
    ]
    return Claim(id="claim_1", text="Seed claim.", type="factual", evidence=evidence)


def _row(votes: list[_VOTE], n_evidence: int, overlap: float, gold: _Gold) -> tuple[list[float], int]:
    features = extract_features(_results(votes), _claim(n_evidence, overlap))
    return features, label_index(gold)


def _iter_template_rows() -> Iterator[tuple[list[float], int]]:
    jitter = (-0.04, -0.02, 0.0, 0.02, 0.04)
    for votes, n_evidence, overlap, gold in _TEMPLATES:
        for delta in jitter:
            shifted: list[_VOTE] = []
            for verdict, confidence in votes:
                shifted.append((verdict, min(0.99, max(0.05, round(confidence + delta, 4)))))
            yield _row(shifted, n_evidence, overlap, gold)


def _sample_verdict(gold: _Gold, rng: random.Random, *, trap: bool) -> Verdict:
    if trap:
        return "supported" if gold == "incorrect" else "incorrect"
    roll = rng.random()
    if gold == "supported":
        if roll < 0.72:
            return "supported"
        if roll < 0.90:
            return "uncertain"
        return "incorrect"
    if gold == "incorrect":
        if roll < 0.72:
            return "incorrect"
        if roll < 0.90:
            return "uncertain"
        return "supported"
    if roll < 0.46:
        return "uncertain"
    if roll < 0.73:
        return "supported"
    return "incorrect"


def _sample_confidence(verdict: Verdict, gold: _Gold, rng: random.Random) -> float:
    if verdict == gold:
        low, high = (0.38, 0.62) if verdict == "uncertain" else (0.72, 0.97)
    elif verdict == "uncertain":
        low, high = (0.34, 0.58)
    else:
        low, high = (0.42, 0.82)
    return round(rng.uniform(low, high), 4)


def _sample_overlap(gold: _Gold, n_evidence: int, rng: random.Random, *, invert: bool) -> float:
    if n_evidence == 0:
        return 0.0
    if invert:
        if gold == "supported":
            return round(rng.uniform(0.0, 0.22), 4)
        if gold == "incorrect":
            return round(rng.uniform(0.48, 0.82), 4)
        return round(rng.uniform(0.18, 0.48), 4)
    if gold == "supported":
        return round(rng.uniform(0.38, 0.86), 4)
    if gold == "incorrect":
        return round(rng.uniform(0.0, 0.32), 4)
    return round(rng.uniform(0.06, 0.42), 4)


def _iter_generated_rows(rng: random.Random) -> Iterator[tuple[list[float], int]]:
    golds: tuple[_Gold, ...] = ("incorrect", "uncertain", "supported")
    for gold in golds:
        for n_judges in (1, 2, 3, 4):
            for n_evidence in (0, 1, 2, 3):
                for repeat in range(8):
                    trap = gold == "incorrect" and n_evidence == 0 and repeat % 4 == 0
                    invert = repeat % 7 == 0 and n_evidence > 0
                    votes: list[_VOTE] = []
                    for _ in range(n_judges):
                        verdict = _sample_verdict(gold, rng, trap=trap)
                        votes.append((verdict, _sample_confidence(verdict, gold, rng)))
                    overlap = _sample_overlap(gold, n_evidence, rng, invert=invert)
                    yield _row(votes, n_evidence, overlap, gold)


def _patterns_for_gold(gold: _Gold) -> list[tuple[list[_VOTE], int, float]]:
    if gold == "supported":
        return [
            ([("supported", 0.92), ("supported", 0.88)], 2, 0.62),
            ([("supported", 0.84), ("supported", 0.8), ("uncertain", 0.48)], 3, 0.58),
            ([("supported", 0.78), ("incorrect", 0.46)], 2, 0.5),
            ([("supported", 0.7), ("supported", 0.68), ("supported", 0.66)], 0, 0.0),
            ([("uncertain", 0.55), ("supported", 0.9)], 3, 0.7),
            ([("supported", 0.95)], 1, 0.45),
        ]
    if gold == "incorrect":
        return [
            ([("incorrect", 0.93), ("incorrect", 0.9)], 2, 0.28),
            ([("incorrect", 0.86), ("incorrect", 0.82), ("uncertain", 0.44)], 2, 0.22),
            ([("incorrect", 0.8), ("supported", 0.42)], 1, 0.18),
            ([("supported", 0.74), ("supported", 0.7), ("supported", 0.68)], 0, 0.0),
            ([("uncertain", 0.52), ("incorrect", 0.91)], 3, 0.4),
            ([("incorrect", 0.88)], 1, 0.3),
        ]
    return [
        ([("uncertain", 0.5), ("uncertain", 0.46)], 1, 0.12),
        ([("supported", 0.82), ("incorrect", 0.8)], 1, 0.2),
        ([("supported", 0.7), ("incorrect", 0.66), ("uncertain", 0.48)], 1, 0.16),
        ([("supported", 0.58), ("supported", 0.54), ("incorrect", 0.88)], 0, 0.0),
        ([("uncertain", 0.42), ("supported", 0.62), ("incorrect", 0.6)], 2, 0.25),
        ([("uncertain", 0.55)], 0, 0.0),
    ]


def _iter_labeled_eval_rows() -> Iterator[tuple[list[float], int]]:
    if not _SEED_EVAL_PATH.is_file():
        return
    items = json.loads(_SEED_EVAL_PATH.read_text(encoding="utf-8"))
    for item in items:
        gold = str(item["gold"])
        for votes, n_evidence, overlap in _patterns_for_gold(gold):
            yield _row(votes, n_evidence, overlap, gold)


def iter_seed_rows() -> Iterator[tuple[list[float], int]]:
    """Yield (features, label_index) pairs covering agreement, splits, and evidence."""
    yield from _iter_template_rows()
    yield from _iter_generated_rows(random.Random(_RNG_SEED))
    yield from _iter_labeled_eval_rows()
