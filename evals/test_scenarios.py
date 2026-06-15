from __future__ import annotations

import os
from io import BytesIO
from types import SimpleNamespace

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
        [plan.ai_brief, plan.situation_summary, plan.report_summary]
        + plan.do_now
        + plan.avoid
        + plan.call_or_escalate
        + plan.contact_recommendations
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


def test_vague_text_with_fire_image_routes_to_fire_response() -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (220, 160), (35, 35, 35))
    draw = ImageDraw.Draw(image)
    draw.rectangle((55, 55, 165, 145), fill=(230, 83, 28))
    draw.polygon([(75, 145), (112, 25), (150, 145)], fill=(255, 182, 44))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")

    result = run_incident(
        IncidentInput(text="Help!", mode="Auto", image_bytes_present=True),
        image_bytes=buffer.getvalue(),
        persist_memory=False,
    )

    assert result.visual_analysis.image_used is True
    assert "fire" in result.visual_analysis.visual_signals
    assert result.risk_assessment.incident_type == "fire_smoke"
    assert result.risk_assessment.selected_mode == "ALERT"


def test_contextual_contacts_appear_in_first_immediate_action() -> None:
    result = run_incident(
        IncidentInput(
            text="A car crash has an injured person and blocked traffic.",
            mode="Auto",
            language="Spanish",
            location_text="Cordoba, cerca del Buen Pastor",
        ),
        persist_memory=False,
    )

    first_action = result.action_plan.do_now[0]
    assert "911" in first_action
    assert "107" in first_action
    assert result.action_plan.contact_recommendations
    assert result.risk_assessment.incident_type == "traffic_accident"


def test_live_vision_scene_summary_routes_personal_safety_without_filename(monkeypatch) -> None:
    from PIL import Image

    from src.schemas import VisualAnalysis
    from src.tools import image_analysis

    image = Image.new("RGB", (80, 80), (210, 210, 210))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")

    monkeypatch.setattr(
        image_analysis,
        "get_settings",
        lambda: SimpleNamespace(
            live_foundry_enabled=True,
            azure_foundry_model_deployment="gpt-4o",
            demo_mode=False,
            azure_openai_vision_configured=False,
            azure_vision_configured=False,
        ),
    )
    monkeypatch.setattr(
        image_analysis,
        "_foundry_multimodal_analysis",
        lambda *_args, **_kwargs: VisualAnalysis(
            image_used=True,
            scene_summary="The image shows an apparent robbery or mugging threat.",
            visual_signals=[],
            limitations=[],
        ),
    )

    result = image_analysis.analyze_image(
        text="This is happening! I do not know what to do!",
        image_bytes=buffer.getvalue(),
    )

    assert "personal_safety_threat" in result.visual_signals


def test_live_vision_does_not_classify_without_ai_scene_context(monkeypatch) -> None:
    from PIL import Image

    from src.schemas import VisualAnalysis
    from src.tools import image_analysis

    image = Image.new("RGB", (80, 80), (210, 210, 210))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")

    monkeypatch.setattr(
        image_analysis,
        "get_settings",
        lambda: SimpleNamespace(
            live_foundry_enabled=True,
            azure_foundry_model_deployment="gpt-4o",
            demo_mode=False,
            azure_openai_vision_configured=False,
            azure_vision_configured=False,
        ),
    )
    monkeypatch.setattr(
        image_analysis,
        "_foundry_multimodal_analysis",
        lambda *_args, **_kwargs: VisualAnalysis(image_used=True, visual_signals=[], limitations=[]),
    )

    result = image_analysis.analyze_image(
        text="What can I do?",
        image_bytes=buffer.getvalue(),
    )

    assert "personal_safety_threat" not in result.visual_signals


def test_visual_filter_removes_unsubstantiated_fire_smoke_from_robbery_scene(monkeypatch) -> None:
    from PIL import Image

    from src.schemas import VisualAnalysis
    from src.tools import image_analysis

    image = Image.new("RGB", (100, 100), (205, 205, 205))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")

    monkeypatch.setattr(
        image_analysis,
        "get_settings",
        lambda: SimpleNamespace(
            live_foundry_enabled=True,
            azure_foundry_model_deployment="gpt-4o",
            demo_mode=False,
            azure_openai_vision_configured=False,
            azure_vision_configured=False,
        ),
    )
    monkeypatch.setattr(
        image_analysis,
        "_foundry_multimodal_analysis",
        lambda *_args, **_kwargs: VisualAnalysis(
            image_used=True,
            scene_summary="The image shows an apparent armed robbery on a motorcycle and mentions nearby smoke.",
            visual_signals=["personal_safety_threat", "fire", "smoke"],
            limitations=[],
        ),
    )

    visual = image_analysis.analyze_image(
        text="What should I do?",
        image_bytes=buffer.getvalue(),
    )
    result = run_incident(
        IncidentInput(
            text="What should I do? he is threating me!!!",
            mode="Auto",
            location_text="Denver, Colorado. Im on vacation",
            image_bytes_present=True,
        ),
        image_bytes=buffer.getvalue(),
        persist_memory=False,
    )

    assert visual.visual_signals == ["personal_safety_threat"]
    assert result.risk_assessment.incident_type == "personal_safety_robbery"
    assert result.risk_assessment.selected_mode == "ALERT"
    assert result.action_plan.do_now[0].startswith("Call/contact now: Police / emergency services: 911")
    assert "law enforcement" in result.responder_packet.recommended_resources
    assert "fire service" not in result.responder_packet.recommended_resources
    assert "fire" not in result.action_plan.ai_brief.lower()
    assert "smoke" not in result.action_plan.ai_brief.lower()


def test_model_string_limitations_do_not_become_character_unknowns() -> None:
    from src.tools.image_analysis import _json_from_model_text

    _signals, _summary, limitations, _findings = _json_from_model_text(
        '{"visual_signals": "personal_safety_threat", "limitations": "Treat this as one limitation."}'
    )

    assert limitations == ["Treat this as one limitation."]
