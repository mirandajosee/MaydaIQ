"""Risk triage agent for deterministic severity and mode selection."""

from __future__ import annotations

from src.schemas import IncidentInput, RiskAssessment, VisualAnalysis
from src.tools.risk_scoring import choose_mode, risk_level_for_score, score_risk


class RiskTriageAgent:
    name = "RiskTriageAgent"

    def run(self, incident: IncidentInput, visual_analysis: VisualAnalysis) -> RiskAssessment:
        score, incident_type, urgency_signals, confidence = score_risk(
            incident.text,
            visual_analysis,
            incident.mode,
        )
        risk_level = risk_level_for_score(score)
        selected_mode = choose_mode(incident.mode, score, urgency_signals)
        human_escalation_required = risk_level in {"HIGH", "CRITICAL"} or confidence == "LOW"

        uncertainty_notes = [
            "MaydaIQ cannot verify the scene, number of people affected, or exact hazard boundaries.",
            "Use local official guidance and trained responders for final decisions.",
        ]
        if confidence == "LOW":
            uncertainty_notes.append("The report has limited detail, so a human should review it.")

        return RiskAssessment(
            incident_type=incident_type,
            risk_score=score,
            risk_level=risk_level,
            selected_mode=selected_mode,
            confidence=confidence,
            human_escalation_required=human_escalation_required,
            urgency_signals=urgency_signals,
            uncertainty_notes=uncertainty_notes,
        )

