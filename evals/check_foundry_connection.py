"""Smoke-test the live Foundry adapter without printing secrets."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.tools.foundry_iq_retrieval import retrieve_from_foundry_iq
from src.tools.runtime_status import get_runtime_status


def main() -> None:
    status = get_runtime_status()
    print(f"runtime_mode={status['mode']}")
    print(f"auth_mode={status['auth_mode']}")
    print(f"endpoint_present={status['endpoint_present']}")
    print(f"agent_id_present={status['agent_id_present']}")
    print(f"agent_name_present={status['agent_name_present']}")
    if status["missing_for_live"]:
        print("missing_for_live=" + ",".join(status["missing_for_live"]))

    playbooks = retrieve_from_foundry_iq(
        query="Flooded street near a utility pole with possible wire hazard. Return cited safety playbook guidance.",
        incident_type="flood",
        max_results=2,
    )
    for index, playbook in enumerate(playbooks, start=1):
        snippet = " ".join(playbook.snippet.split())[:240]
        print(f"playbook_{index}_source={playbook.source_id}")
        print(f"playbook_{index}_title={playbook.title}")
        print(f"playbook_{index}_snippet={snippet}")


if __name__ == "__main__":
    main()

