"""Safety critic agent for conservative revisions and guardrail enforcement."""

from __future__ import annotations

from src.agents.action_planner_agent import escalation_text
from src.schemas import ActionPlan, RiskAssessment, SafetyReview, VisualAnalysis


class SafetyCriticAgent:
    name = "SafetyCriticAgent"

    def run(
        self,
        plan: ActionPlan,
        risk: RiskAssessment,
        visual_analysis: VisualAnalysis,
    ) -> tuple[ActionPlan, SafetyReview]:
        issues: list[str] = []
        revisions: list[str] = []
        human_escalation_required = risk.human_escalation_required

        call_or_escalate = list(plan.call_or_escalate)
        avoid = self._clean_unsafe_positive_instructions(plan.avoid)
        do_now = self._clean_unsafe_positive_instructions(plan.do_now)
        next_steps = self._clean_unsafe_positive_instructions(plan.next_steps)

        if len(avoid) != len(plan.avoid) or len(do_now) != len(plan.do_now):
            issues.append("Removed unsafe positive instructions.")
            revisions.append("Stripped confrontation, pursuit, or unsafe-entry guidance.")

        if risk.risk_level in {"HIGH", "CRITICAL"} and not self._contains_emergency_escalation(call_or_escalate):
            call_or_escalate.append(escalation_text())
            human_escalation_required = True
            issues.append("High severity required explicit emergency escalation.")
            revisions.append("Added local emergency services escalation.")

        if risk.confidence == "LOW":
            human_escalation_required = True
            revisions.append("Flagged low-confidence case for human review.")

        if risk.incident_type == "personal_safety_robbery":
            if not any("do not confront" in item.lower() for item in avoid):
                avoid.insert(0, "Do not confront, pursue, or try to detain anyone.")
                revisions.append("Added anti-confrontation guardrail.")

        if risk.incident_type in {"flood", "electrical_hazard"}:
            phrase = "Avoid floodwater, downed wires, submerged outlets, and anything touching them."
            if not any("wire" in item.lower() or "electrical" in item.lower() for item in avoid):
                avoid.insert(0, phrase)
                revisions.append("Added water and wire avoidance guardrail.")

        if risk.incident_type == "fire_smoke":
            if not any("evacuat" in item.lower() for item in do_now):
                do_now.insert(0, "Evacuate away from smoke and heat.")
                revisions.append("Added evacuation guidance.")

        revised_plan = plan.model_copy(
            update={
                "do_now": do_now,
                "avoid": avoid,
                "call_or_escalate": call_or_escalate,
                "next_steps": next_steps,
                "unknowns": list(dict.fromkeys(plan.unknowns + risk.uncertainty_notes)),
            }
        )
        status = "REVISE" if revisions else "PASS"
        return revised_plan, SafetyReview(
            status=status,
            issues=issues,
            revisions_applied=revisions,
            human_escalation_required=human_escalation_required,
            uncertainty_notes=revised_plan.unknowns,
        )

    @staticmethod
    def _contains_emergency_escalation(items: list[str]) -> bool:
        return any("emergency services" in item.lower() or "911" in item.lower() for item in items)

    @staticmethod
    def _clean_unsafe_positive_instructions(items: list[str]) -> list[str]:
        unsafe_words = ("confront", "pursue", "chase", "detain", "re-enter", "reenter")
        safe_negations = ("do not", "don't", "never", "avoid")
        cleaned: list[str] = []
        for item in items:
            lower = item.lower()
            unsafe = any(word in lower for word in unsafe_words)
            negated = any(negation in lower for negation in safe_negations)
            if unsafe and not negated:
                continue
            cleaned.append(item)
        return cleaned
