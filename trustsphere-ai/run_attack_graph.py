"""Run the TrustSphere attack graph intelligence pipeline."""

from __future__ import annotations

from src.attack_graph.attack_pipeline import AttackGraphPipeline, _configure_logging


def main() -> None:
    _configure_logging()
    summary = AttackGraphPipeline().run()
    print(summary)


if __name__ == "__main__":
    main()
