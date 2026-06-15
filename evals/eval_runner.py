"""Simple eval runner for MaydaIQ."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["DEMO_MODE"] = "true"

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.orchestrator import run_incident
from src.schemas import IncidentInput
from src.tools.sample_incidents import list_sample_incidents


def run_all() -> None:
    for key, label in list_sample_incidents():
        result = run_incident(
            IncidentInput(text=label, mode="Auto", sample_scenario=key),
            persist_memory=False,
        )
        packet = result.responder_packet
        print(
            f"{key}: risk={packet.risk_level} mode={result.risk_assessment.selected_mode} "
            f"confidence={packet.confidence} escalation={packet.human_escalation_required}"
        )


if __name__ == "__main__":
    run_all()
