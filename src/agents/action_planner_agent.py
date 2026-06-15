"""Action planner agent for Alert and Calm modes."""

from __future__ import annotations

from src.config import get_settings
from src.schemas import ActionPlan, IncidentInput, RetrievedPlaybook, RiskAssessment, VisualAnalysis


def escalation_text() -> str:
    contact = get_settings().emergency_contact_text
    return (
        f"Contact {contact} now if there is life risk, fire, injury, violence, floodwater, electricity, "
        "or any immediate danger."
    )


GENERIC_ESCALATION = escalation_text()


PLAYBOOK_COPY: dict[str, dict[str, list[str] | str]] = {
    "flood": {
        "summary": "Flooding may hide fast water, debris, open drains, or energized wires.",
        "do_now": ["Move people to higher ground away from floodwater.", "Keep back from wires, poles, and submerged outlets."],
        "avoid": ["Do not walk or drive through floodwater or touch anything electrical."],
        "next": ["Mark the unsafe area from a distance.", "Record water depth, blocked routes, and visible utilities if safe."],
        "prevention": ["Map repeat flood points.", "Pre-stage sandbags, detour signs, and utility contact lists."],
    },
    "fire_smoke": {
        "summary": "Smoke or fire near a building can change quickly and may indicate trapped occupants.",
        "do_now": ["Evacuate away from smoke and heat.", "Warn nearby people only if you can do it while leaving."],
        "avoid": ["Do not re-enter, open hot doors, or move toward smoke."],
        "next": ["Account for people from a safe location.", "Share building access details with responders."],
        "prevention": ["Check evacuation routes.", "Keep alarms, extinguishers, and assembly points maintained."],
    },
    "traffic_accident": {
        "summary": "A crash with possible injury and blocked traffic needs scene safety first.",
        "do_now": ["Move to a safe area away from traffic if possible.", "Keep the injured person still unless there is immediate danger."],
        "avoid": ["Do not stand in traffic lanes or provide invasive medical care."],
        "next": ["Set a safe perimeter if trained.", "Note vehicle count, blocked lanes, and visible hazards."],
        "prevention": ["Review dangerous intersections.", "Improve signage, lighting, and detour plans."],
    },
    "personal_safety_robbery": {
        "summary": "A personal safety threat should prioritize distance, escape, and official help.",
        "do_now": ["Move to a safe, public, well-lit place.", "Stay with trusted people and preserve distance."],
        "avoid": ["Do not confront, pursue, or try to detain anyone."],
        "next": ["Write down only non-identifying incident details when safe.", "Preserve evidence without sharing private identities."],
        "prevention": ["Improve lighting and buddy systems.", "Plan safe reporting channels with local authorities."],
    },
    "electrical_hazard": {
        "summary": "Electrical hazards can energize water, fences, vehicles, or nearby ground.",
        "do_now": ["Stay far away from downed wires and anything touching them.", "Warn others from a distance."],
        "avoid": ["Do not touch wires, poles, flooded areas, or affected vehicles."],
        "next": ["Keep a wide perimeter.", "Report utility asset details only from a safe distance."],
        "prevention": ["Keep utility emergency contacts ready.", "Train volunteers on wire and floodwater exclusion zones."],
    },
    "environmental_water_quality": {
        "summary": "Water observations can screen for possible pollution, but they are not a definitive diagnosis.",
        "do_now": ["Avoid contact with suspicious water.", "Document location, odor, color, weather, and visible organisms from a safe distance."],
        "avoid": ["Do not claim a cause or exact contaminant without lab or agency confirmation."],
        "next": ["Compare upstream and downstream observations.", "Submit a structured report to the relevant environmental agency."],
        "prevention": ["Create repeat sampling routes.", "Train volunteers on benthic macroinvertebrate observation protocols."],
    },
    "environmental_air_quality": {
        "summary": "Lichen observations can support air-quality screening, but they cannot prove exact pollutant levels.",
        "do_now": ["Record lichen type, abundance, distance from road, weather, and photo context.", "Compare with a cleaner reference site."],
        "avoid": ["Do not overclaim exact air quality or diagnose health impacts from lichen alone."],
        "next": ["Repeat observations over time.", "Pair findings with official air monitoring where possible."],
        "prevention": ["Build a citizen-science map.", "Share trends with local environmental health teams."],
    },
    "general_safety": {
        "summary": "The report needs more detail before MaydaIQ can classify the incident confidently.",
        "do_now": ["Move away from any immediate hazard.", "Share only safe, non-private details."],
        "avoid": ["Do not enter unsafe areas to gather more information."],
        "next": ["Clarify what happened, where, and whether anyone is in immediate danger."],
        "prevention": ["Create a local emergency contact list.", "Practice reporting using structured fields."],
    },
}


class ActionPlannerAgent:
    name = "ActionPlannerAgent"

    def run(
        self,
        incident: IncidentInput,
        risk: RiskAssessment,
        visual_analysis: VisualAnalysis,
        playbooks: list[RetrievedPlaybook],
    ) -> ActionPlan:
        copy = PLAYBOOK_COPY.get(risk.incident_type, PLAYBOOK_COPY["general_safety"])
        citations = [source_id for playbook in playbooks for source_id in playbook.citations]
        evidence = [f"{playbook.source_id}: {playbook.snippet}" for playbook in playbooks]
        unknowns = list(risk.uncertainty_notes)
        if visual_analysis.limitations:
            unknowns.extend(visual_analysis.limitations[:2])

        if risk.selected_mode == "ALERT":
            return ActionPlan(
                selected_mode="ALERT",
                situation_summary=str(copy["summary"]),
                do_now=list(copy["do_now"])[:2],
                avoid=list(copy["avoid"])[:1],
                call_or_escalate=[escalation_text()],
                report_summary=self._alert_report_summary(incident, risk, visual_analysis),
                step_by_step_plan=[],
                evidence=evidence[:2],
                unknowns=unknowns,
                prevention_suggestions=[],
                confidence=risk.confidence,
                citations=citations,
                next_steps=list(copy["next"])[:1],
            )

        step_by_step_plan = [
            f"1. Stabilize safety first: {list(copy['do_now'])[0]}",
            f"2. Keep people away from risky actions: {list(copy['avoid'])[0]}",
            "3. Capture responder-ready facts: time, approximate location, visible hazards, affected access routes, and what is still unknown.",
            "4. Use the cited playbooks to decide which local agency or community team should review the report.",
        ]

        return ActionPlan(
            selected_mode="CALM",
            situation_summary=str(copy["summary"]),
            do_now=list(copy["do_now"]),
            avoid=list(copy["avoid"]),
            call_or_escalate=[escalation_text()] if risk.risk_level in {"HIGH", "CRITICAL"} else [],
            report_summary=self._calm_report_summary(incident, risk),
            step_by_step_plan=step_by_step_plan,
            evidence=evidence,
            unknowns=unknowns,
            prevention_suggestions=list(copy["prevention"]),
            confidence=risk.confidence,
            citations=citations,
            next_steps=list(copy["next"]),
        )

    @staticmethod
    def _alert_report_summary(incident: IncidentInput, risk: RiskAssessment, visual_analysis: VisualAnalysis) -> str:
        signals = ", ".join(visual_analysis.visual_signals[:4]) or "no image signals"
        location = incident.location_text or "location not provided"
        return f"{risk.incident_type} at {location}; risk {risk.risk_level}; signals: {signals}."

    @staticmethod
    def _calm_report_summary(incident: IncidentInput, risk: RiskAssessment) -> str:
        location = incident.location_text or "location not provided"
        return f"Structured {risk.incident_type} planning report for {location}; risk score {risk.risk_score}/100."
