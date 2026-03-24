"""URL phishing classifiers and export helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except Exception:
    XGBClassifier = None
    XGBOOST_AVAILABLE = False


@dataclass(slots=True)
class URLModelBundle:
    model: Any
    model_type: str
    metadata: dict[str, Any]


class URLPhishingModel:
    """Wrapper that prefers XGBoost and falls back to Gradient Boosting."""

    def __init__(self, params: dict[str, Any] | None = None, random_state: int = 42) -> None:
        params = params or {}
        if XGBOOST_AVAILABLE:
            self.model = XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=random_state,
                max_depth=params.get("max_depth", 4),
                learning_rate=params.get("learning_rate", 0.1),
                n_estimators=params.get("n_estimators", 200),
                subsample=0.9,
                colsample_bytree=0.9,
            )
            self.model_type = "xgboost"
        else:
            self.model = GradientBoostingClassifier(
                random_state=random_state,
                learning_rate=params.get("learning_rate", 0.1),
                n_estimators=params.get("n_estimators", 200),
                max_depth=params.get("max_depth", 3),
            )
            self.model_type = "gradient_boosting_fallback"

    def fit(self, x_train, y_train) -> None:
        self.model.fit(x_train, y_train)

    def predict_proba(self, x_values) -> np.ndarray:
        return self.model.predict_proba(x_values)

    def save(self, output_path: str | Path, metadata: dict[str, Any]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.model_type == "xgboost" and hasattr(self.model, "save_model"):
            self.model.save_model(path)
        else:
            manifest = {
                "model_type": self.model_type,
                "metadata": metadata,
                "joblib_path": str(path.with_suffix(".joblib")),
            }
            path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            joblib.dump(self.model, path.with_suffix(".joblib"))
        return path
