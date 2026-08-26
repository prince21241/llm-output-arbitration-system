"""Feature vectors for the confidence model."""

from __future__ import annotations

from collections.abc import Sequence
from statistics import pstdev

from app.pipeline.evidence import max_evidence_overlap, mean_evidence_overlap
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult
from app.utils.scoring import RuleBasedScorer, signed_contribution

FEATURE_NAMES: tuple[str, ...] = (
    "n_judges",
    "frac_supported",
    "frac_incorrect",
    "frac_uncertain",
    "mean_confidence",
    "std_confidence",
    "mean_signed",
    "agreement",
    "disagreement",
    "rule_based",
    "n_evidence",
    "max_overlap",
    "mean_overlap",
)

_RULE = RuleBasedScorer()
_LABELS = ("incorrect", "uncertain", "supported")


def label_index(verdict: str) -> int:
    try:
        return _LABELS.index(verdict)
    except ValueError as exc:
        raise ValueError(f"Unsupported gold label: {verdict}") from exc


def extract_features(
    results: Sequence[JudgeResult],
    claim: Claim | None = None,
) -> list[float]:
    """Turn judge votes and optional evidence into a fixed-length vector."""
    total = len(results)
    if total == 0:
        return [0.0] * len(FEATURE_NAMES)

    supporting = sum(1 for item in results if item.verdict == "supported")
    incorrect = sum(1 for item in results if item.verdict == "incorrect")
    uncertain = sum(1 for item in results if item.verdict == "uncertain")
    confidences = [item.confidence for item in results]
    mean_conf = sum(confidences) / total
    std_conf = pstdev(confidences) if total > 1 else 0.0
    mean_signed = sum(signed_contribution(item.verdict, item.confidence) for item in results) / total
    agreement = max(supporting, incorrect, uncertain) / total
    decisive = supporting + incorrect
    disagreement = 0.0 if decisive == 0 else 1.0 - (abs(supporting - incorrect) / decisive)
    evidence = claim.evidence if claim is not None else []

    return [
        float(total),
        supporting / total,
        incorrect / total,
        uncertain / total,
        mean_conf,
        std_conf,
        mean_signed,
        agreement,
        disagreement,
        _RULE.support_probability(results),
        float(len(evidence)),
        max_evidence_overlap(evidence),
        mean_evidence_overlap(evidence),
    ]
