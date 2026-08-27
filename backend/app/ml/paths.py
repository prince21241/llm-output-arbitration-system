"""On-disk location for the trained confidence model."""

from pathlib import Path

ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "confidence_model.joblib"
