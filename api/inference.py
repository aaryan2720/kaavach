from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class KaavachPredictor:
    def __init__(self, models_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.models_dir = models_dir or (base_dir / "models")

        metadata_path = self.models_dir / "model_metadata.json"
        model_path = self.models_dir / "selected_model.joblib"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Model metadata not found: {metadata_path}")
        if not model_path.exists():
            raise FileNotFoundError(f"Selected model artifact not found: {model_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.model = joblib.load(model_path)
        self.numeric_features: list[str] = self.metadata.get("numeric_features", [])
        self.categorical_features: list[str] = self.metadata.get("categorical_features", [])
        self.model_name: str = self.metadata.get("selected_model_name", "unknown")
        self.threshold: float = float(self.metadata.get("selected_threshold", 0.5))

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}

        for col in self.numeric_features:
            value = record.get(col, 0)
            try:
                normalized[col] = float(value)
            except (TypeError, ValueError):
                normalized[col] = 0.0

        for col in self.categorical_features:
            value = record.get(col, "missing")
            normalized[col] = "missing" if value is None else str(value)

        return normalized

    def predict_one(self, record: dict[str, Any]) -> dict[str, Any]:
        row = self._normalize_record(record)
        X = pd.DataFrame([row])
        proba = float(self.model.predict_proba(X)[:, 1][0])
        pred = int(proba >= self.threshold)

        return {
            "prediction": pred,
            "decision": "attack" if pred == 1 else "normal",
            "confidence": round(proba, 6),
            "threshold": self.threshold,
            "model_name": self.model_name,
        }

    def predict_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []

        rows = [self._normalize_record(r) for r in records]
        X = pd.DataFrame(rows)
        probas = self.model.predict_proba(X)[:, 1]

        output: list[dict[str, Any]] = []
        for proba in np.asarray(probas):
            p = float(proba)
            pred = int(p >= self.threshold)
            output.append(
                {
                    "prediction": pred,
                    "decision": "attack" if pred == 1 else "normal",
                    "confidence": round(p, 6),
                    "threshold": self.threshold,
                    "model_name": self.model_name,
                }
            )

        return output
