"""MaydaIQ multi-agent orchestration."""

from __future__ import annotations

from src.agents.action_planner_agent import ActionPlannerAgent
from src.agents.community_memory_agent import CommunityMemoryAgent
from src.agents.foundry_iq_agent import FoundryIQAgent
from src.agents.intake_agent import IntakeAgent
from src.agents.responder_packet_agent import ResponderPacketAgent
from src.agents.risk_triage_agent import RiskTriageAgent
from src.agents.safety_critic_agent import SafetyCriticAgent
from src.agents.translation_agent import TranslationAgent
from src.agents.vision_agent import VisionAgent
from src.schemas import AgentTraceStep, IncidentInput, MaydaIQResult
from src.tools.response_resources import contact_guidance, recommended_entities
from src.tools.report_payload import simulate_emergency_report


DISCLAIMER = (
    "MaydaIQ is not an emergency service and does not contact real authorities. "
    "For life risk, fire, injury, violence, floodwater, electricity, or immediate danger, "
    "contact local emergency services and follow official instructions."
)


class MaydaIQOrchestrator:
    def __init__(self) -> None:
        self.intake_agent = IntakeAgent()
        self.vision_agent = VisionAgent()
        self.risk_triage_agent = RiskTriageAgent()
        self.foundry_iq_agent = FoundryIQAgent()
        self.action_planner_agent = ActionPlannerAgent()
        self.safety_critic_agent = SafetyCriticAgent()
        self.responder_packet_agent = ResponderPacketAgent()
        self.community_memory_agent = CommunityMemoryAgent()
        self.translation_agent = TranslationAgent()

    def run(
        self,
        incident: IncidentInput,
        image_bytes: bytes | None = None,
        persist_memory: bool = True,
    ) -> MaydaIQResult:
        trace: list[AgentTraceStep] = []

        intake = self.intake_agent.run(incident)
        trace.append(
            AgentTraceStep(
                agent="Intake",
                summary=(
                    f"Normalized report; candidates={intake['incident_type_candidates']} "
                    f"image_needed={intake['image_analysis_needed']}."
                )[:150],
            )
        )

        visual = self.vision_agent.run(incident, image_bytes=image_bytes)
        trace.append(
            AgentTraceStep(
                agent="Vision",
                summary=(
                    f"Returned privacy-safe hazard labels: {visual.visual_signals or ['none']}."
                    + (f" Scene: {visual.scene_summary[:70]}" if visual.scene_summary else "")
                )[:170],
            )
        )

        risk = self.risk_triage_agent.run(incident, visual)
        trace.append(
            AgentTraceStep(
                agent="Triage",
                summary=f"Scored {risk.risk_score}/100 as {risk.risk_level}; selected {risk.selected_mode}.",
            )
        )

        response_entities = recommended_entities(risk.incident_type)
        response_contacts = contact_guidance(risk.incident_type, incident.location_text)
        query = " ".join(
            [
                incident.text,
                visual.scene_summary,
                " ".join(visual.visual_signals),
                incident.location_text or "",
            ]
        )
        playbooks = self.foundry_iq_agent.run(
            query=query,
            incident_type=risk.incident_type,
            target_language=incident.language,
            location_text=incident.location_text,
            response_entities=response_entities,
            response_contacts=response_contacts,
        )
        trace.append(
            AgentTraceStep(
                agent="Foundry IQ Retrieval",
                summary=f"Retrieved {len(playbooks)} grounded playbook snippets.",
            )
        )

        plan = self.action_planner_agent.run(incident, risk, visual, playbooks)
        trace.append(
            AgentTraceStep(
                agent="Planner",
                summary=f"Built {plan.selected_mode} plan with {len(plan.do_now)} do-now actions.",
            )
        )

        revised_plan, safety_review = self.safety_critic_agent.run(plan, risk, visual)
        trace.append(
            AgentTraceStep(
                agent="Safety Critic",
                summary=f"{safety_review.status}; revisions={len(safety_review.revisions_applied)}.",
            )
        )

        packet = self.responder_packet_agent.run(incident, risk, visual, revised_plan, safety_review)
        trace.append(
            AgentTraceStep(
                agent="Responder Packet",
                summary=f"Created simulated packet {packet.incident_id}; no dispatch performed.",
            )
        )

        simulate_emergency_report(packet)

        if persist_memory:
            memory = self.community_memory_agent.run(incident, packet)
            trace.append(
                AgentTraceStep(
                    agent="Community Memory",
                    summary=f"Stored anonymized hazard labels; raw_image_stored={memory['raw_image_stored']}.",
                )
            )

        result = MaydaIQResult(
            incident_input=incident,
            visual_analysis=visual,
            risk_assessment=risk,
            retrieved_playbooks=playbooks,
            action_plan=revised_plan,
            safety_review=safety_review,
            responder_packet=packet,
            agent_trace=trace,
            disclaimer=DISCLAIMER,
        )
        return self.translation_agent.run(result, incident.language)


def run_incident(
    incident: IncidentInput,
    image_bytes: bytes | None = None,
    persist_memory: bool = True,
) -> MaydaIQResult:
    return MaydaIQOrchestrator().run(incident, image_bytes=image_bytes, persist_memory=persist_memory)
