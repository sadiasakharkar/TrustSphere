from __future__ import annotations

import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)

LIVE_MODE = "LIVE_MODE"
SIMULATION_MODE = "SIMULATION_MODE"
HYBRID_MODE = "HYBRID_MODE"


@dataclass
class ExecutionReadiness:
    ml_runtime: bool
    ollama: bool
    elasticsearch: bool


def select_execution_mode(readiness: ExecutionReadiness) -> str:
    if readiness.ml_runtime and readiness.ollama and readiness.elasticsearch:
        mode = LIVE_MODE
    elif not readiness.ml_runtime and not readiness.ollama:
        mode = SIMULATION_MODE
    else:
        mode = HYBRID_MODE
    LOGGER.info("[PIPELINE] execution_mode=%s ml_runtime=%s ollama=%s elasticsearch=%s", mode, readiness.ml_runtime, readiness.ollama, readiness.elasticsearch)
    return mode
