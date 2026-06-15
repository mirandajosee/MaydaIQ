"""Responder packet agent for structured simulated incident payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.schemas import ActionPlan, IncidentInput, ResponderPacket, RiskAssessment, SafetyReview, VisualAnalysis
from src.tools.privacy import redact_private_details


RESOURCE_MAP: dict[str, list[str]] = {
    "flood": ["rescue", "utility crew", "road crew", "local emergency management"],
    "fire_smoke": ["fire service", "medical", "building management", "local emergency management"],
    "traffic_accident": ["medical", "traffic control", "road crew", "law enforcement"],
    "personal_safety_robbery": ["law enforcement", "victim support", "nearby safe site"],
    "electrical_hazard": ["utility crew", "fire service", "road crew"],
    "environmental_water_quality": ["environmental agency", "public works", "community science coordinator"],
    "environmental_air_quality": ["environmental health", "air quality agency", "community science coordinator"],
    "general_safety": ["local emergency management", "human reviewer"],
}


class ResponderPacketAgent:
    name = "ResponderPacketAgent"

    def run(
        self,
        incident: IncidentInput,
        risk: RiskAssessment,
        visual_analysis: VisualAnalysis,
        plan: ActionPlan,
        safety_review: SafetyReview,
    ) -> ResponderPacket:
        redacted_report, redactions = redact_private_details(incident.text)
        hazards = sorted(set(visual_analysis.visual_signals + risk.urgency_signals))
        resources = RESOURCE_MAP.get(risk.incident_type, RESOURCE_MAP["general_safety"])
        incident_id = f"maydaiq-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8]}"

        return ResponderPacket(
            incident_id=incident_id,
            timestamp_utc=datetime.now(timezone.utc),
            incident_type=risk.incident_type,
            risk_level=risk.risk_level,
            confidence=risk.confidence,
            location_text=incident.location_text,
            visual_signals=visual_analysis.visual_signals,
            user_report=redacted_report,
            immediate_actions=plan.do_now + plan.call_or_escalate,
            hazards=hazards,
            unknowns=plan.unknowns,
            recommended_resources=resources,
            human_escalation_required=safety_review.human_escalation_required,
            privacy_redactions=redactions,
            simulated_only=True,
        )

