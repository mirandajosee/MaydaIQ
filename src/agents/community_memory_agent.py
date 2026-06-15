"""Anonymized community memory writer."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src.config import REPORTS_PATH
from src.schemas import IncidentInput, ResponderPacket


class CommunityMemoryAgent:
    name = "CommunityMemoryAgent"

    def run(self, incident: IncidentInput, packet: ResponderPacket) -> dict[str, object]:
        REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "incident_id": packet.incident_id,
            "incident_type": packet.incident_type,
            "risk_level": packet.risk_level,
            "approximate_location_text": incident.location_text,
            "hazard_labels": packet.hazards,
            "privacy_redactions": packet.privacy_redactions,
            "simulated_only": True,
            "raw_image_stored": False,
        }
        with REPORTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"stored": True, "path": str(REPORTS_PATH), "raw_image_stored": False}

