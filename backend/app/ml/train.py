"""Train, calibrate, and keep the best confidence model (Phase 7)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.dataset import iter_seed_rows
from app.ml.features import FEATURE_NAMES
from app.ml.paths import ARTIFACT_PATH

LABELS = ("incorrect", "uncertain", "supported")
_HOLDOUT = 0.25
_LOGISTIC_MARGIN = 0.01


def load_xy() -> tuple[np.ndarray, np.ndarray]:
    rows = list(iter_seed_rows())
    features = np.asarray([row[0] for row in rows], dtype=float)
    labels = np.asarray([row[1] for row in rows], dtype=int)
    if len(features) < 20:
        raise RuntimeError("Seed dataset is too small to train.")
    if features.shape[1] != len(FEATURE_NAMES):
        raise RuntimeError("Feature width does not match FEATURE_NAMES.")
    return features, labels


def _logistic() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=400,
                    C=1.0,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )


def _boosting() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_depth=3,
        learning_rate=0.08,
        max_iter=160,
        l2_regularization=0.1,
        class_weight="balanced",
        random_state=7,
    )


def _factories() -> dict[str, Callable[[], Any]]:
    return {
        "logistic_regression": _logistic,
        "hist_gradient_boosting": _boosting,
    }


def _multiclass_brier(y_true: np.ndarray, proba: np.ndarray, n_classes: int = 3) -> float:
    one_hot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((proba - one_hot) ** 2, axis=1)))


def _support_scores(proba: np.ndarray, classes: np.ndarray) -> np.ndarray:
    by_class = {int(label): proba[:, index] for index, label in enumerate(classes)}
    supported = by_class.get(2, np.zeros(len(proba)))
    uncertain = by_class.get(1, np.zeros(len(proba)))
    return supported + 0.5 * uncertain


def _holdout_metrics(model: Any, x_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
    proba = model.predict_proba(x_test)
    predicted = model.predict(x_test)
    support = _support_scores(proba, model.classes_)
    gold_support = y_test.astype(float) / 2.0
    return {
        "holdout_log_loss": float(log_loss(y_test, proba, labels=[0, 1, 2])),
        "holdout_brier": _multiclass_brier(y_test, proba),
        "holdout_accuracy": float(accuracy_score(y_test, predicted)),
        "holdout_support_brier": float(np.mean((support - gold_support) ** 2)),
    }


def _fit_calibrated(estimator: Any, method: str, x: np.ndarray, y: np.ndarray) -> Any:
    calibrated = CalibratedClassifierCV(estimator, method=method, cv=3)
    calibrated.fit(x, y)
    return calibrated


def train(path: Path | None = None) -> dict[str, float | str]:
    """Fit candidates, score a holdout set, calibrate, and save the winner."""
    x, y = load_xy()
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=_HOLDOUT,
        stratify=y,
        random_state=7,
    )
    folds = StratifiedKFold(n_splits=4, shuffle=True, random_state=7)
    factories = _factories()
    cv_losses: dict[str, float] = {}
    for name, factory in factories.items():
        cv_losses[name] = float(
            -cross_val_score(factory(), x_train, y_train, cv=folds, scoring="neg_log_loss").mean()
        )

    candidates: list[dict[str, Any]] = []
    for algo_name, factory in factories.items():
        for method in ("sigmoid", "isotonic"):
            try:
                fitted = _fit_calibrated(factory(), method, x_train, y_train)
            except ValueError:
                continue
            metrics = _holdout_metrics(fitted, x_test, y_test)
            candidates.append(
                {
                    "algorithm": algo_name,
                    "calibration": method,
                    "cv_log_loss": cv_losses[algo_name],
                    **metrics,
                    "model": fitted,
                }
            )
    if not candidates:
        raise RuntimeError("No calibrated candidate could be fit.")

    def sort_key(item: dict[str, Any]) -> tuple[float, int, float]:
        prefer_logistic = 0 if item["algorithm"] == "logistic_regression" else 1
        prefer_sigmoid = 0 if item["calibration"] == "sigmoid" else 1
        return (
            round(float(item["holdout_log_loss"]) + (0.0 if prefer_logistic == 0 else _LOGISTIC_MARGIN), 6),
            prefer_sigmoid,
            float(item["holdout_support_brier"]),
        )

    winner = min(candidates, key=sort_key)
    final_model = _fit_calibrated(
        clone(factories[str(winner["algorithm"])]()),
        str(winner["calibration"]),
        x,
        y,
    )
    destination = path or ARTIFACT_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "feature_names": list(FEATURE_NAMES),
            "labels": list(LABELS),
            "algorithm": winner["algorithm"],
            "calibration": winner["calibration"],
            "cv_log_loss": winner["cv_log_loss"],
            "holdout_log_loss": winner["holdout_log_loss"],
            "holdout_brier": winner["holdout_brier"],
            "holdout_accuracy": winner["holdout_accuracy"],
            "holdout_support_brier": winner["holdout_support_brier"],
            "logistic_cv_log_loss": cv_losses["logistic_regression"],
            "boosting_cv_log_loss": cv_losses["hist_gradient_boosting"],
            "n_rows": int(len(y)),
        },
        destination,
    )
    return {
        "algorithm": str(winner["algorithm"]),
        "calibration": str(winner["calibration"]),
        "cv_log_loss": round(float(winner["cv_log_loss"]), 4),
        "holdout_log_loss": round(float(winner["holdout_log_loss"]), 4),
        "holdout_brier": round(float(winner["holdout_brier"]), 4),
        "holdout_accuracy": round(float(winner["holdout_accuracy"]), 4),
        "holdout_support_brier": round(float(winner["holdout_support_brier"]), 4),
        "logistic_cv_log_loss": round(cv_losses["logistic_regression"], 4),
        "boosting_cv_log_loss": round(cv_losses["hist_gradient_boosting"], 4),
        "path": str(destination),
        "n_rows": float(len(y)),
    }


def main() -> None:
    summary = train()
    print(
        "Trained {algorithm} + {calibration} on {n_rows:.0f} rows "
        "(cv log loss {cv_log_loss}, holdout log loss {holdout_log_loss}, "
        "brier {holdout_brier}, accuracy {holdout_accuracy}, "
        "support brier {holdout_support_brier}; "
        "logistic {logistic_cv_log_loss}, boosting {boosting_cv_log_loss}) -> {path}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
