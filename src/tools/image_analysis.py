"""Privacy-preserving image analysis adapter with deterministic demo fallback."""

from __future__ import annotations

import base64
import json

from src.config import get_settings
from src.schemas import VisualAnalysis, VisualFinding
from src.tools.sample_incidents import SAMPLE_INCIDENTS


SCENARIO_SIGNAL_MAP: dict[str, list[str]] = {
    key: list(value["visual_signals"]) for key, value in SAMPLE_INCIDENTS.items()
}

TEXT_HINTS: dict[str, list[str]] = {
    "flood": ["floodwater", "fast_water"],
    "wire": ["possible_electrical_hazard", "fallen_wire"],
    "electric": ["possible_electrical_hazard"],
    "smoke": ["smoke"],
    "fire": ["smoke", "fire"],
    "crash": ["crash", "blocked_road"],
    "accident": ["crash", "blocked_road"],
    "injured": ["injured_person_possible"],
    "robbery": ["personal_safety_threat"],
    "threat": ["personal_safety_threat"],
    "algae": ["polluted_water", "algae_bloom"],
    "dead fish": ["polluted_water", "dead_fish"],
    "benthic": ["benthic_observation"],
    "lichen": ["lichen_observation"],
}


def _dedupe(signals: list[str]) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for signal in signals:
        if signal not in seen:
            clean.append(signal)
            seen.add(signal)
    return clean


def _fallback_visual_analysis(
    text: str,
    image_filename: str | None,
    sample_scenario: str | None,
    image_present: bool,
) -> VisualAnalysis:
    signals: list[str] = []
    if sample_scenario and sample_scenario in SCENARIO_SIGNAL_MAP:
        signals.extend(SCENARIO_SIGNAL_MAP[sample_scenario])

    combined = f"{text} {image_filename or ''}".lower()
    for hint, mapped_signals in TEXT_HINTS.items():
        if hint in combined:
            signals.extend(mapped_signals)

    signals = _dedupe(signals)
    findings = [
        VisualFinding(
            label=signal,
            confidence=0.74 if sample_scenario else 0.58,
            evidence="Demo fallback inferred hazard label; no identity or plate analysis performed.",
        )
        for signal in signals
    ]
    limitations = [
        "Demo fallback is deterministic and does not identify faces, people, license plates, suspects, or private individuals."
    ]
    if not image_present:
        limitations.append("No image was provided; visual signals came from text/sample context only.")
    return VisualAnalysis(image_used=image_present, visual_signals=signals, findings=findings, limitations=limitations)


def _azure_vision_analysis(image_bytes: bytes) -> VisualAnalysis:
    settings = get_settings()
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential

    client = ImageAnalysisClient(
        endpoint=settings.azure_vision_endpoint,
        credential=AzureKeyCredential(settings.azure_vision_key),
    )
    result = client.analyze(
        image_data=image_bytes,
        visual_features=[VisualFeatures.TAGS, VisualFeatures.CAPTION, VisualFeatures.READ],
    )

    signals: list[str] = []
    evidence_parts: list[str] = []
    if getattr(result, "caption", None) and result.caption.text:
        evidence_parts.append(result.caption.text)
    for tag in getattr(result, "tags", []) or []:
        tag_name = getattr(tag, "name", "").lower()
        evidence_parts.append(tag_name)
        for hint, mapped in TEXT_HINTS.items():
            if hint in tag_name:
                signals.extend(mapped)

    signals = _dedupe(signals)
    findings = [
        VisualFinding(
            label=signal,
            confidence=0.8,
            evidence="Azure Vision hazard tag mapped to MaydaIQ safety label; identity analysis disabled.",
        )
        for signal in signals
    ]
    return VisualAnalysis(
        image_used=True,
        visual_signals=signals,
        findings=findings,
        limitations=[
            "Azure Vision output is used only for hazard labels; MaydaIQ does not identify people, faces, suspects, or plates.",
            "Raw image bytes are not stored by the community memory agent.",
        ],
    )


def _map_text_to_signals(text: str) -> list[str]:
    lowered = text.lower()
    signals: list[str] = []
    for hint, mapped_signals in TEXT_HINTS.items():
        if hint in lowered:
            signals.extend(mapped_signals)
    return _dedupe(signals)


def _azure_openai_vision_analysis(image_bytes: bytes, text: str) -> VisualAnalysis:
    settings = get_settings()
    from openai import AzureOpenAI

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    response = client.chat.completions.create(
        model=settings.azure_openai_vision_deployment,
        temperature=0,
        max_tokens=350,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a privacy-preserving crisis image analyst. Return JSON only. "
                    "Identify hazard labels, not people. Never identify faces, license plates, suspects, or private individuals. "
                    "Allowed hazard labels include floodwater, smoke, fire, crash, blocked_road, fallen_wire, "
                    "injured_person_possible, structural_damage, polluted_water, algae_bloom, dead_fish, "
                    "lichen_observation, signage_text, possible_electrical_hazard."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Report context: {text}. Return JSON with visual_signals and limitations."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
        raw_signals = parsed.get("visual_signals", [])
        limitations = parsed.get("limitations", [])
    except json.JSONDecodeError:
        raw_signals = _map_text_to_signals(content)
        limitations = ["Vision model returned non-JSON text; MaydaIQ mapped hazard words conservatively."]

    signals = _dedupe([str(signal).strip() for signal in raw_signals if str(signal).strip()])
    findings = [
        VisualFinding(
            label=signal,
            confidence=0.78,
            evidence="Azure OpenAI vision model mapped image content to privacy-safe hazard label.",
        )
        for signal in signals
    ]
    return VisualAnalysis(
        image_used=True,
        visual_signals=signals,
        findings=findings,
        limitations=list(limitations)
        or ["Azure OpenAI vision output is limited to hazard labels; no identity analysis is performed."],
    )


def analyze_image(
    text: str,
    image_bytes: bytes | None = None,
    image_filename: str | None = None,
    sample_scenario: str | None = None,
) -> VisualAnalysis:
    settings = get_settings()
    image_present = bool(image_bytes or image_filename or sample_scenario)

    if image_bytes and settings.azure_vision_configured and not settings.demo_mode:
        try:
            return _azure_vision_analysis(image_bytes)
        except Exception:
            pass

    if image_bytes and settings.azure_openai_vision_configured and not settings.demo_mode:
        try:
            return _azure_openai_vision_analysis(image_bytes, text)
        except Exception:
            pass

    return _fallback_visual_analysis(text, image_filename, sample_scenario, image_present)
