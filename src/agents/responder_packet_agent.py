"""Responder packet agent for structured simulated incident payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.schemas import ActionPlan, IncidentInput, ResponderPacket, RiskAssessment, SafetyReview, VisualAnalysis
from src.tools.privacy import redact_private_details
from src.tools.response_resources import recommended_entities


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
        resources = recommended_entities(risk.incident_type)
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
