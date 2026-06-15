"""Vision agent that returns privacy-safe visual hazard labels."""

from __future__ import annotations

from src.schemas import IncidentInput, VisualAnalysis
from src.tools.image_analysis import analyze_image


class VisionAgent:
    name = "VisionAgent"

    def run(self, incident: IncidentInput, image_bytes: bytes | None = None) -> VisualAnalysis:
        return analyze_image(
            text=incident.text,
            image_bytes=image_bytes,
            image_filename=incident.image_filename,
            sample_scenario=incident.sample_scenario,
        )

