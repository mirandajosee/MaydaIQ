"""Deterministic translation stub for demo-safe multilingual labels."""

from __future__ import annotations

from src.schemas import AgentTraceStep, MaydaIQResult


SPANISH_DISCLAIMER = (
    "MaydaIQ no es un servicio de emergencia y no contacta autoridades reales. "
    "Use servicios locales de emergencia si hay peligro inmediato."
)


class TranslationAgent:
    name = "TranslationAgent"

    def run(self, result: MaydaIQResult, target_language: str) -> MaydaIQResult:
        if target_language == "English":
            return result

        trace = list(result.agent_trace)
        if target_language == "Spanish":
            trace.append(
                AgentTraceStep(
                    agent=self.name,
                    summary="Spanish safety disclaimer applied; grounded plan remains citation-stable.",
                )
            )
            return result.model_copy(update={"disclaimer": SPANISH_DISCLAIMER, "agent_trace": trace})

        trace.append(
            AgentTraceStep(
                agent=self.name,
                summary=f"{target_language} translation unavailable in demo; English safety output retained.",
                status="fallback",
            )
        )
        return result.model_copy(update={"agent_trace": trace})
