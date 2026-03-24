"""Run the full offline TrustSphere detection pipeline."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models.risk_engine import UEBARiskEngine
from src.models.train_anomaly_model import run_training

try:
    from src.models.config import PROCESSED_DATA_DIR
except ImportError:
    PROCESSED_DATA_DIR = Path("data/processed")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    artifacts = run_training()
    risk_engine = UEBARiskEngine()
    scored = risk_engine.evaluate_dataframe(artifacts.scores_df)
    output_path = PROCESSED_DATA_DIR / "ueba_scores.parquet"
    risk_engine.save_scores(scored, output_path)
    print(
        json.dumps(
            {
                "rows_scored": len(scored),
                "output": str(output_path),
                "thresholds": artifacts.thresholds,
                "risk_level_counts": scored["risk_level"].value_counts().to_dict(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
