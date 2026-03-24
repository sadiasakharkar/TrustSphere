"""Offline AI SOC analyst orchestrator for TrustSphere."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    from .context_builder import SOCContextBuilder
    from .incident_generator import IncidentReportGenerator
    from .ollama_client import LocalLLM, write_install_notes
    from .playbook_generator import PlaybookGenerator
    from .report_exporter import ReportExporter
except ImportError:
    from context_builder import SOCContextBuilder
    from incident_generator import IncidentReportGenerator
    from ollama_client import LocalLLM, write_install_notes
    from playbook_generator import PlaybookGenerator
    from report_exporter import ReportExporter

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BASE_DIR / "outputs"


class TrustSphereSOCAgent:
    """End-to-end offline SOC reasoning pipeline backed by a local LLM."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else BASE_DIR
        self.outputs_dir = self.base_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self._configure_logging()
        self.logger = logging.getLogger(__name__)
        self.llm = LocalLLM()
        self.context_builder = SOCContextBuilder(self.outputs_dir)
        self.incident_generator = IncidentReportGenerator(self.llm, self.outputs_dir)
        self.playbook_generator = PlaybookGenerator(self.llm, self.outputs_dir)
        self.report_exporter = ReportExporter(self.outputs_dir)
        write_install_notes(self.outputs_dir / "ollama_setup.txt")

    def run(self) -> dict[str, Path]:
        context = self.context_builder.build_context()
        incident = self.incident_generator.generate(context)
        playbook = self.playbook_generator.generate(context)
        exports = self.report_exporter.export(incident, playbook, context)
        self.logger.info("Incident report saved to %s", exports["incident_report"])
        self.logger.info("Response playbook saved to %s", exports["response_playbook"])
        self.logger.info("Incident summary saved to %s", exports["incident_summary"])
        self.logger.info("SOC dashboard JSON saved to %s", exports["soc_dashboard"])
        return exports

    def _configure_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.FileHandler(self.outputs_dir / "soc_agent.log"),
                logging.StreamHandler(),
            ],
        )


if __name__ == "__main__":
    agent = TrustSphereSOCAgent()
    outputs = agent.run()
    print(f"Incident report: {outputs['incident_report']}")
    print(f"Response playbook: {outputs['response_playbook']}")
    print(f"Incident summary: {outputs['incident_summary']}")
    print(f"SOC dashboard: {outputs['soc_dashboard']}")
