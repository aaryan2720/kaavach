from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import threading


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

        # Load model with mmap to reduce memory pressure when possible
        try:
            self._model_path = model_path
            # protect reloads
            self._lock = threading.Lock()
            try:
                self.model = joblib.load(model_path, mmap_mode="r")
            except TypeError:
                self.model = joblib.load(model_path)
        except TypeError:
            # Older joblib versions may not support mmap_mode
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

    def _apply_rules(self, record: dict[str, Any]) -> dict | None:
        """Apply simple rule-based overrides. Return a dict with override
        decision info or None if no rule matched.
        Current rules:
        - If `state` == 'REQ_RST' and `spkts` > 30 => force attack.
        """
        state = record.get("state")
        try:
            spkts = float(record.get("spkts", 0))
        except (TypeError, ValueError):
            spkts = 0.0

        if isinstance(state, str) and state.upper() == "REQ_RST" and spkts > 30:
            return {
                "prediction": 1,
                "decision": "attack",
                "confidence": 0.99,
                "threshold": self.threshold,
                "model_name": self.model_name,
                "rule": "REQ_RST_spkts_gt_30",
            }
        return None

    def predict_one(self, record: dict[str, Any]) -> dict[str, Any]:
        row = self._normalize_record(record)
        # rule-based override
        rule_res = self._apply_rules(row)
        if rule_res is not None:
            return rule_res
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

        output: list[dict[str, Any]] = []
        # First apply rule-based overrides and collect indices needing model prediction
        model_indices: list[int] = []
        model_rows: list[dict[str, Any]] = []
        for idx, row in enumerate(rows):
            rule_res = self._apply_rules(row)
            if rule_res is not None:
                output.append(rule_res)
            else:
                # placeholder to keep ordering
                output.append({})
                model_indices.append(idx)
                model_rows.append(row)

        if model_rows:
            X = pd.DataFrame(model_rows)
            probas = self.model.predict_proba(X)[:, 1]
            p_iter = iter(np.asarray(probas))
            for mi in model_indices:
                p = float(next(p_iter))
                pred = int(p >= self.threshold)
                output[mi] = {
                    "prediction": pred,
                    "decision": "attack" if pred == 1 else "normal",
                    "confidence": round(p, 6),
                    "threshold": self.threshold,
                    "model_name": self.model_name,
                }

        return output

    def reload(self) -> dict[str, Any]:
        """Reload model artifact and metadata from disk without restarting the server.

        Returns a status dict with keys: success, message.
        """
        try:
            with self._lock:
                metadata_path = self.models_dir / "model_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                # reload model artifact
                try:
                    new_model = joblib.load(self._model_path, mmap_mode="r")
                except TypeError:
                    new_model = joblib.load(self._model_path)
                self.model = new_model
                self.numeric_features = self.metadata.get("numeric_features", [])
                self.categorical_features = self.metadata.get("categorical_features", [])
                self.model_name = str(self.metadata.get("selected_model_name", self.model_name))
                self.threshold = float(self.metadata.get("selected_threshold", self.threshold))
        except Exception as exc:
            return {"success": False, "message": f"reload failed: {exc}"}
        return {"success": True, "message": "model reloaded"}
