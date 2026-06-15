"""Intake agent for normalizing reports and identifying urgency hints."""

from __future__ import annotations

from src.schemas import IncidentInput
from src.tools.risk_scoring import detect_incident_type, detect_urgency_signals


class IntakeAgent:
    name = "IntakeAgent"

    def run(self, incident: IncidentInput) -> dict[str, object]:
        normalized_text = " ".join(incident.text.strip().split())
        urgency_signals = detect_urgency_signals(normalized_text, [])
        return {
            "normalized_text": normalized_text,
            "incident_type_candidates": [detect_incident_type(normalized_text, [])],
            "urgency_keywords": urgency_signals,
            "detected_language": self._detect_language(normalized_text, incident.language),
            "image_analysis_needed": bool(incident.image_bytes_present or incident.image_filename or incident.sample_scenario),
        }

    @staticmethod
    def _detect_language(text: str, selected_language: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["calle", "humo", "inundacion", "herido", "robo"]):
            return "Spanish"
        return selected_language or "English"

