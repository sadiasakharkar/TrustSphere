from __future__ import annotations

import os
from pathlib import Path
import unittest

from src.pipeline.pipeline_config import UnifiedPipelineConfig
from src.pipeline.unified_intelligence_pipeline import UnifiedIntelligencePipeline


class UnifiedPipelineIntegrationTests(unittest.TestCase):
    def test_unified_pipeline_runs_end_to_end_in_development_mode(self) -> None:
        previous_env = os.environ.get("TRUSTSPHERE_ENV")
        os.environ["TRUSTSPHERE_ENV"] = "development"
        try:
            pipeline = UnifiedIntelligencePipeline(
                base_dir=Path(__file__).resolve().parents[1],
                config=UnifiedPipelineConfig.from_env(),
            )
            result = pipeline.run()
        finally:
            if previous_env is None:
                os.environ.pop("TRUSTSPHERE_ENV", None)
            else:
                os.environ["TRUSTSPHERE_ENV"] = previous_env

        self.assertEqual(result.schema_version, "unified_output.v1")
        self.assertGreaterEqual(len(result.normalized_events), 1)
        self.assertGreaterEqual(len(result.anomaly_results), 1)
        self.assertIsNotNone(result.incident_report.incident_id)
        self.assertIn(result.execution_mode, {"development", "production"})


if __name__ == "__main__":
    unittest.main()
