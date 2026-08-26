"""Confidence model training and inference tests."""

from __future__ import annotations

from app.ml.dataset import iter_seed_rows
from app.ml.features import FEATURE_NAMES, extract_features
from app.ml.model import MLConfidenceModel
from app.ml.train import train
from app.pipeline.consensus import ConsensusEngine
from app.schemas.claim import Claim, Evidence
from app.schemas.judge import JudgeResult
from app.config import Settings


def _result(verdict: str, confidence: float) -> JudgeResult:
    return JudgeResult(
        judge="a",
        claim_id="claim_1",
        verdict=verdict,  # type: ignore[arg-type]
        confidence=confidence,
        reason="test",
    )


def test_seed_rows_cover_three_labels() -> None:
    rows = list(iter_seed_rows())
    labels = {label for _, label in rows}
    assert labels == {0, 1, 2}
    assert len(rows) >= 400
    assert all(len(features) == len(FEATURE_NAMES) for features, _ in rows)


def test_feature_vector_width_matches_schema() -> None:
    results = [_result("incorrect", 0.9), _result("incorrect", 0.8)]
    vector = extract_features(results, Claim(id="claim_1", text="x", type="factual"))
    assert len(vector) == len(FEATURE_NAMES)
    assert vector[0] == 2.0
    assert vector[2] == 1.0


def test_trained_model_separates_clear_votes(tmp_path) -> None:
    artifact = tmp_path / "confidence_model.joblib"
    summary = train(path=artifact)
    assert artifact.is_file()
    assert summary["algorithm"] in {"logistic_regression", "hist_gradient_boosting"}
    assert summary["calibration"] in {"sigmoid", "isotonic"}
    assert summary["n_rows"] >= 400
    assert 0.0 <= float(summary["holdout_accuracy"]) <= 1.0
    assert float(summary["holdout_log_loss"]) < 1.5
    model = MLConfidenceModel.load(artifact)
    assert model is not None

    incorrect = [
        _result("incorrect", 0.95),
        _result("incorrect", 0.92),
    ]
    supported = [
        JudgeResult(judge="a", claim_id="claim_1", verdict="supported", confidence=0.9, reason="t"),
        JudgeResult(judge="b", claim_id="claim_1", verdict="supported", confidence=0.88, reason="t"),
    ]
    backed = Claim(
        id="claim_1",
        text="The first iPhone was released in 2007.",
        type="date",
        evidence=[
            Evidence(
                title="iPhone",
                url="https://en.wikipedia.org/wiki/iPhone",
                snippet="The first iPhone was released in 2007.",
                source="wikipedia",
                overlap=0.6,
            )
        ],
    )
    low = model.support_probability(incorrect)
    high = model.support_probability(supported, backed)
    assert low < 0.4
    assert high > 0.6
    assert low < high


def test_consensus_engine_uses_ml_scorer(tmp_path) -> None:
    artifact = tmp_path / "confidence_model.joblib"
    train(path=artifact)
    model = MLConfidenceModel.load(artifact)
    assert model is not None
    engine = ConsensusEngine(settings=Settings(use_ml_scorer=True), scorer=model)
    claims = [Claim(id="claim_1", text="The first iPhone was released in 2005.", type="date")]
    results = [
        _result("incorrect", 0.95),
        JudgeResult(judge="b", claim_id="claim_1", verdict="incorrect", confidence=0.92, reason="t"),
    ]
    scored = engine.score_claims(claims, results)[0]
    assert scored.verdict == "incorrect"
    assert 0.0 <= scored.support_probability <= 1.0
