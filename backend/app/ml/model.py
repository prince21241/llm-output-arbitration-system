"""ML confidence scorer with the same contract as RuleBasedScorer."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import joblib
import numpy as np

from app.ml.features import FEATURE_NAMES, extract_features
from app.ml.paths import ARTIFACT_PATH
from app.schemas.claim import Claim
from app.schemas.judge import JudgeResult
from app.utils.scoring import RuleBasedScorer, clamp

_RULE = RuleBasedScorer()


class MLConfidenceModel:
    """Predict P(supported) from vote features, with a rule-based fallback."""

    def __init__(self, bundle: dict[str, object]) -> None:
        self._bundle = bundle
        self._model = bundle["model"]
        names = bundle.get("feature_names", list(FEATURE_NAMES))
        if list(names) != list(FEATURE_NAMES):
            raise ValueError("Saved feature schema does not match this code.")

    @classmethod
    def load(cls, path: Path | None = None) -> MLConfidenceModel | None:
        target = path or ARTIFACT_PATH
        if not target.is_file():
            return None
        bundle = joblib.load(target)
        if not isinstance(bundle, dict) or "model" not in bundle:
            return None
        return cls(bundle)

    @property
    def algorithm(self) -> str:
        return str(self._bundle.get("algorithm", "ml"))

    @property
    def calibration(self) -> str:
        return str(self._bundle.get("calibration", "sigmoid"))

    def support_probability(
        self,
        results: Sequence[JudgeResult],
        claim: Claim | None = None,
    ) -> float:
        if not results:
            return 0.5
        try:
            vector = np.asarray([extract_features(results, claim)], dtype=float)
            proba = self._model.predict_proba(vector)[0]
            by_index = {
                int(cls): float(score)
                for cls, score in zip(self._model.classes_, proba, strict=True)
            }
            # 0 = incorrect, 1 = uncertain, 2 = supported
            supported = by_index.get(2, 0.0)
            uncertain = by_index.get(1, 0.0)
            score = supported + 0.5 * uncertain
            return round(clamp(score), 4)
        except Exception:
            return _RULE.support_probability(results)
