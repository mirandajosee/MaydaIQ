from __future__ import annotations

import os

os.environ["DEMO_MODE"] = "true"

from src.orchestrator import run_incident
from src.schemas import IncidentInput, MaydaIQResult


def _run(text: str, mode: str = "Auto", sample_scenario: str | None = None) -> MaydaIQResult:
    return run_incident(
        IncidentInput(text=text, mode=mode, sample_scenario=sample_scenario),
        persist_memory=False,
    )


def _all_plan_text(result: MaydaIQResult) -> str:
    plan = result.action_plan
    parts = (
        [plan.situation_summary, plan.report_summary]
        + plan.do_now
        + plan.avoid
        + plan.call_or_escalate
        + plan.step_by_step_plan
        + plan.next_steps
    )
    return " ".join(parts).lower()


def test_alert_mode_response_is_short() -> None:
    result = _run(
        "There is smoke and fire at the side of a building and someone may be inside.",
        mode="Alert",
        sample_scenario="fire_smoke",
    )
    bullets = result.action_plan.do_now + result.action_plan.avoid + result.action_plan.call_or_escalate
    words = " ".join(bullets).split()
    assert result.risk_assessment.selected_mode == "ALERT"
    assert len(bullets) <= 4
    assert len(words) <= 80


def test_high_severity_triggers_human_escalation() -> None:
    result = _run(
        "A flooded street has a downed wire and people may be trapped.",
        sample_scenario="flood_electrical",
    )
    assert result.risk_assessment.risk_level in {"HIGH", "CRITICAL"}
    assert result.responder_packet.human_escalation_required is True


def test_robbery_does_not_advise_confrontation() -> None:
    result = _run(
        "Someone was robbed and the threatening person may still be nearby.",
        sample_scenario="robbery_threat",
    )
    text = _all_plan_text(result)
    assert "do not confront" in text
    assert "pursue the" not in text
    assert "try to detain" not in text.replace("do not confront, pursue, or try to detain", "")


def test_flood_electrical_mentions_avoiding_water_and_wires() -> None:
    result = _run(
        "Floodwater is near a utility pole and a wire may be down.",
        sample_scenario="flood_electrical",
    )
    text = _all_plan_text(result)
    assert "floodwater" in text or "water" in text
    assert "wire" in text or "electrical" in text


def test_fire_mentions_evacuation_and_emergency_services() -> None:
    result = _run(
        "Thick smoke and fire are visible near an apartment building.",
        sample_scenario="fire_smoke",
    )
    text = _all_plan_text(result)
    assert "evacuat" in text
    assert "emergency services" in text


def test_environmental_scenario_does_not_overclaim_exact_diagnosis() -> None:
    result = _run(
        "Volunteers saw algae and few benthic macroinvertebrates in a creek.",
        mode="Calm",
        sample_scenario="water_pollution",
    )
    text = _all_plan_text(result)
    assert "not a definitive diagnosis" in text or "without lab or agency confirmation" in text
    assert "definitive cause is" not in text
    assert "exact contaminant is" not in text


def test_outputs_validate_against_pydantic_schema() -> None:
    result = _run("Two cars crashed and one person may be injured.", sample_scenario="traffic_injury")
    validated = MaydaIQResult.model_validate(result.model_dump())
    assert validated.responder_packet.incident_type == "traffic_accident"


def test_responder_packet_is_simulated_only() -> None:
    result = _run("There is a downed wire near water.", sample_scenario="flood_electrical")
    assert result.responder_packet.simulated_only is True


def test_agent_trace_exists_and_is_concise() -> None:
    result = _run("Smoke near a building.", sample_scenario="fire_smoke")
    assert len(result.agent_trace) >= 7
    assert all(len(step.summary) <= 170 for step in result.agent_trace)
