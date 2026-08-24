"""Consensus and scoring tests."""

from app.config import Settings
from app.pipeline.consensus import ConsensusEngine
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult
from app.utils.scoring import RuleBasedScorer, signed_contribution, verdict_from_confidence


def _claim(claim_id: str = "claim_1") -> Claim:
    return Claim(id=claim_id, text="Example claim.", type="factual")


def _result(
    judge: str,
    verdict: str,
    confidence: float,
    claim_id: str = "claim_1",
) -> JudgeResult:
    return JudgeResult(
        judge=judge,
        claim_id=claim_id,
        verdict=verdict,  # type: ignore[arg-type]
        confidence=confidence,
        reason="test",
    )


def test_signed_contribution_rules() -> None:
    assert signed_contribution("supported", 0.8) == 0.8
    assert signed_contribution("incorrect", 0.8) == -0.8
    assert signed_contribution("uncertain", 0.8) == 0.0


def test_verdict_thresholds_come_from_settings() -> None:
    settings = Settings(supported_threshold=0.75, incorrect_threshold=0.35)
    assert verdict_from_confidence(0.75, settings.supported_threshold, settings.incorrect_threshold) == "supported"
    assert verdict_from_confidence(0.35, settings.supported_threshold, settings.incorrect_threshold) == "incorrect"
    assert verdict_from_confidence(0.50, settings.supported_threshold, settings.incorrect_threshold) == "uncertain"


def test_unanimous_incorrect_votes_yield_low_support() -> None:
    scorer = RuleBasedScorer()
    results = [
        _result("mock_judge_a", "incorrect", 0.95),
        _result("mock_judge_b", "incorrect", 0.92),
    ]
    score = scorer.support_probability(results)
    assert score == 0.0325
    assert score <= 0.35


def test_unanimous_supported_votes_yield_high_support() -> None:
    scorer = RuleBasedScorer()
    results = [
        _result("a", "supported", 0.9),
        _result("b", "supported", 0.8),
    ]
    assert scorer.support_probability(results) == 0.925


def test_split_votes_yield_mid_support_and_disagreement() -> None:
    engine = ConsensusEngine(settings=Settings())
    claims = [_claim()]
    results = [
        _result("a", "supported", 0.9),
        _result("b", "incorrect", 0.9),
    ]
    scored = engine.score_claims(claims, results)[0]
    assert scored.supporting_votes == 1
    assert scored.incorrect_votes == 1
    assert scored.support_probability == 0.5
    assert scored.agreement_score == 0.5
    assert scored.disagreement_score == 1.0
    assert scored.verdict == "uncertain"


def test_agreement_is_one_when_judges_unanimous() -> None:
    engine = ConsensusEngine(settings=Settings())
    claims = [_claim()]
    results = [
        _result("a", "incorrect", 0.95),
        _result("b", "incorrect", 0.92),
    ]
    scored = engine.score_claims(claims, results)[0]
    assert scored.agreement_score == 1.0
    assert scored.disagreement_score == 0.0
    assert scored.incorrect_votes == 2
    assert scored.average_confidence == 0.935


def test_overall_score_is_confidence_weighted_average() -> None:
    engine = ConsensusEngine(settings=Settings())
    claims = [_claim("claim_1"), _claim("claim_2")]
    results = [
        _result("a", "incorrect", 1.0, "claim_1"),
        _result("b", "incorrect", 1.0, "claim_1"),
        _result("a", "supported", 0.5, "claim_2"),
        _result("b", "supported", 0.5, "claim_2"),
    ]
    claim_scores = engine.score_claims(claims, results)
    overall = engine.aggregate(claim_scores)
    # claim_1 support=0.0 weight=1.0; claim_2 support=0.75 weight=0.5
    expected = (0.0 * 1.0 + 0.75 * 0.5) / 1.5
    assert overall.support_score == round(expected, 4)
