"""Simulated responder reporting tool.

MaydaIQ never calls, texts, emails, or dispatches real emergency services.
"""

from __future__ import annotations

from src.schemas import ResponderPacket


def simulate_emergency_report(packet: ResponderPacket) -> dict[str, object]:
    return {
        "status": "simulated_only_not_sent",
        "incident_id": packet.incident_id,
        "simulated_only": True,
        "human_escalation_required": packet.human_escalation_required,
        "note": "No real phone call, SMS, email, police report, or dispatch was made.",
    }

