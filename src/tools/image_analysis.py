"""Privacy-preserving image analysis adapter with deterministic demo fallback."""

from __future__ import annotations

import base64
from io import BytesIO
import json
import re

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
    "robbed": ["personal_safety_threat"],
    "mugging": ["personal_safety_threat"],
    "theft": ["personal_safety_threat"],
    "weapon": ["personal_safety_threat"],
    "gun": ["personal_safety_threat"],
    "handgun": ["personal_safety_threat"],
    "pistol": ["personal_safety_threat"],
    "revolver": ["personal_safety_threat"],
    "firearm": ["personal_safety_threat"],
    "armed": ["personal_safety_threat"],
    "pointing a gun": ["personal_safety_threat"],
    "pointing gun": ["personal_safety_threat"],
    "knife": ["personal_safety_threat"],
    "masked": ["personal_safety_threat"],
    "threat": ["personal_safety_threat"],
    "threatening me": ["personal_safety_threat"],
    "threating me": ["personal_safety_threat"],
    "algae": ["polluted_water", "algae_bloom"],
    "dead fish": ["polluted_water", "dead_fish"],
    "benthic": ["benthic_observation"],
    "lichen": ["lichen_observation"],
}

SIGNAL_ALIASES: dict[str, str] = {
    "apparent_weapon": "personal_safety_threat",
    "weapon_visible": "personal_safety_threat",
    "possible_robbery": "personal_safety_threat",
    "possible_robbery_threat": "personal_safety_threat",
    "robbery": "personal_safety_threat",
    "robbery_threat": "personal_safety_threat",
    "assault": "personal_safety_threat",
    "person_with_weapon": "personal_safety_threat",
    "flames": "fire",
    "burning": "fire",
}

ALLOWED_SIGNALS: set[str] = {
    "floodwater",
    "fast_water",
    "smoke",
    "fire",
    "crash",
    "blocked_road",
    "fallen_wire",
    "possible_electrical_hazard",
    "injured_person_possible",
    "structural_damage",
    "polluted_water",
    "algae_bloom",
    "dead_fish",
    "benthic_observation",
    "lichen_observation",
    "signage_text",
    "personal_safety_threat",
}

FIRE_EVIDENCE_TERMS = ("visible fire", "flame", "flames", "burning", "on fire", "active fire")
SMOKE_EVIDENCE_TERMS = (
    "smoke plume",
    "smoke rising",
    "thick smoke",
    "heavy smoke",
    "black smoke",
    "gray smoke",
    "grey smoke",
    "dense smoke",
)


def _dedupe(signals: list[str]) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for signal in signals:
        signal = SIGNAL_ALIASES.get(signal.strip().lower(), signal.strip().lower())
        if signal not in ALLOWED_SIGNALS:
            continue
        if signal not in seen:
            clean.append(signal)
            seen.add(signal)
    return clean


def _context_hint_signals(text: str, sample_scenario: str | None) -> list[str]:
    signals: list[str] = []
    if sample_scenario and sample_scenario in SCENARIO_SIGNAL_MAP:
        signals.extend(SCENARIO_SIGNAL_MAP[sample_scenario])

    combined = text.lower()
    for hint, mapped_signals in TEXT_HINTS.items():
        if hint in combined:
            signals.extend(mapped_signals)
    return _dedupe(signals)


def _fallback_visual_analysis(
    text: str,
    sample_scenario: str | None,
    image_present: bool,
    image_bytes: bytes | None = None,
) -> VisualAnalysis:
    signals: list[str] = _context_hint_signals(text, sample_scenario)

    if image_bytes:
        signals.extend(_heuristic_image_signals(image_bytes))

    signals = _dedupe(signals)
    scene_summary = _fallback_scene_summary(signals, image_present)
    findings = [
        VisualFinding(
            label=signal,
            confidence=0.74 if sample_scenario else 0.64,
            evidence="Privacy-safe fallback inferred hazard label; no identity or plate analysis performed.",
        )
        for signal in signals
    ]
    limitations = [
        "Demo fallback is deterministic and does not identify faces, people, license plates, suspects, or private individuals."
    ]
    if not image_present:
        limitations.append("No image was provided; visual signals came from text/sample context only.")
    return VisualAnalysis(
        image_used=image_present,
        scene_summary=scene_summary,
        visual_signals=signals,
        findings=findings,
        limitations=limitations,
    )


def _enrich_visual_analysis(
    analysis: VisualAnalysis,
    text: str,
    sample_scenario: str | None,
    image_bytes: bytes | None,
) -> VisualAnalysis:
    hint_signals = _dedupe(_map_text_to_signals(analysis.scene_summary) + _context_hint_signals(text, sample_scenario))
    if image_bytes:
        hint_signals.extend(_heuristic_image_signals(image_bytes))

    merged_signals = _dedupe(analysis.visual_signals + hint_signals)
    filtered_signals, dropped_signals = _filter_model_signals(
        merged_signals,
        analysis.scene_summary,
        list(analysis.findings),
        image_bytes,
    )
    if filtered_signals == analysis.visual_signals and not dropped_signals:
        return analysis

    existing = {finding.label for finding in analysis.findings}
    added = [signal for signal in filtered_signals if signal not in existing]
    findings = [finding for finding in analysis.findings if finding.label in filtered_signals]
    findings.extend(
        VisualFinding(
            label=signal,
            confidence=0.72,
            evidence="MaydaIQ enriched the visual result with privacy-safe text/image safety hints.",
        )
        for signal in added
    )
    limitations = list(analysis.limitations)
    limitations.append("Visual model output was enriched with privacy-safe report/image hazard hints.")
    if dropped_signals:
        limitations.append(
            "Removed unsubstantiated fire/smoke labels because the image evidence did not clearly support them."
        )
    return analysis.model_copy(
        update={
            "visual_signals": filtered_signals,
            "findings": findings,
            "scene_summary": analysis.scene_summary or _fallback_scene_summary(filtered_signals, bool(image_bytes)),
            "limitations": list(dict.fromkeys(limitations)),
        }
    )


def _fallback_scene_summary(signals: list[str], image_present: bool) -> str:
    if not image_present:
        return ""
    if "personal_safety_threat" in signals:
        return "The visual context indicates a possible personal safety threat."
    if "fire" in signals or "smoke" in signals:
        return "The visual context indicates possible fire or smoke."
    if "crash" in signals or "blocked_road" in signals:
        return "The visual context indicates a possible traffic incident."
    if "floodwater" in signals or "fast_water" in signals:
        return "The visual context indicates possible flooding."
    return ""


def _heuristic_image_signals(image_bytes: bytes) -> list[str]:
    """Small offline safety net for obvious fire/smoke images.

    This is not a general vision model. It only catches high-confidence visual
    color patterns so vague prompts with an attached emergency image still route
    to a safer plan if cloud vision is unavailable.
    """

    try:
        from PIL import Image, ImageStat

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((220, 220))
        pixel_source = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
        pixels = list(pixel_source)
        total = max(len(pixels), 1)
        fire_pixels = 0
        dark_smoke_pixels = 0
        gray_smoke_pixels = 0
        for red, green, blue in pixels:
            if red > 165 and green > 45 and green < 190 and blue < 125 and red > green + 25:
                fire_pixels += 1
            if red < 85 and green < 85 and blue < 85:
                dark_smoke_pixels += 1
            if abs(red - green) < 24 and abs(green - blue) < 24 and 80 <= red <= 185:
                gray_smoke_pixels += 1

        fire_ratio = fire_pixels / total
        dark_ratio = dark_smoke_pixels / total
        gray_ratio = gray_smoke_pixels / total
        brightness = sum(ImageStat.Stat(image).mean) / 3

        signals: list[str] = []
        if fire_ratio >= 0.012 or (fire_pixels >= 85 and brightness > 45):
            signals.extend(["fire", "smoke"])
        elif dark_ratio >= 0.18 and gray_ratio >= 0.08:
            signals.append("smoke")
        return signals
    except Exception:
        return []


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
        scene_summary=". ".join(evidence_parts[:3]),
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


def _coerce_text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]
    if isinstance(value, dict):
        return [str(value)]
    try:
        return [str(item).strip() for item in value if str(item).strip()]  # type: ignore[operator]
    except TypeError:
        return [str(value).strip()] if str(value).strip() else []


def _json_from_model_text(content: str) -> tuple[list[str], str, list[str], list[VisualFinding]]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                return (
                    _map_text_to_signals(content),
                    "",
                    ["Vision model returned non-JSON text; MaydaIQ mapped hazard words conservatively."],
                    [],
                )
        else:
            return (
                _map_text_to_signals(content),
                "",
                ["Vision model returned non-JSON text; MaydaIQ mapped hazard words conservatively."],
                [],
            )

    raw_signals = _coerce_text_list(parsed.get("visual_signals", []))
    scene_summary = str(parsed.get("scene_summary", "")).strip()
    limitations = _coerce_text_list(parsed.get("limitations", []))
    signals = _dedupe([str(signal).strip() for signal in raw_signals if str(signal).strip()])
    findings: list[VisualFinding] = []
    for raw_finding in parsed.get("findings", []) or []:
        if not isinstance(raw_finding, dict):
            continue
        label = SIGNAL_ALIASES.get(str(raw_finding.get("label", "")).strip().lower(), str(raw_finding.get("label", "")).strip().lower())
        if label not in ALLOWED_SIGNALS:
            continue
        evidence = str(raw_finding.get("evidence", "")).strip()
        try:
            confidence = float(raw_finding.get("confidence", 0.78))
        except (TypeError, ValueError):
            confidence = 0.78
        findings.append(
            VisualFinding(
                label=label,
                confidence=max(0.0, min(confidence, 1.0)),
                evidence=evidence or "Vision model reported this privacy-safe hazard label.",
            )
        )
        signals.append(label)
    return _dedupe(signals), scene_summary, limitations, findings


def _evidence_text(label: str, scene_summary: str, findings: list[VisualFinding]) -> str:
    pieces = [scene_summary]
    pieces.extend(finding.evidence for finding in findings if finding.label == label)
    return " ".join(pieces).lower()


def _filter_model_signals(
    signals: list[str],
    scene_summary: str,
    findings: list[VisualFinding],
    image_bytes: bytes | None,
) -> tuple[list[str], list[str]]:
    heuristic_signals = set(_heuristic_image_signals(image_bytes)) if image_bytes else set()
    filtered: list[str] = []
    dropped: list[str] = []
    has_personal_threat = "personal_safety_threat" in _dedupe(signals)

    for signal in _dedupe(signals):
        evidence = _evidence_text(signal, scene_summary, findings)
        if signal == "fire":
            has_direct_evidence = any(term in evidence for term in FIRE_EVIDENCE_TERMS) or "fire" in heuristic_signals
            if has_personal_threat and not any(term in evidence for term in ("flame", "flames", "active fire", "on fire")):
                has_direct_evidence = False
            if not has_direct_evidence:
                dropped.append(signal)
                continue
        if signal == "smoke":
            has_direct_evidence = any(term in evidence for term in SMOKE_EVIDENCE_TERMS) or "smoke" in heuristic_signals
            if has_personal_threat and not any(
                term in evidence for term in ("smoke plume", "thick smoke", "heavy smoke", "black smoke", "dense smoke")
            ):
                has_direct_evidence = False
            if not has_direct_evidence:
                dropped.append(signal)
                continue
        filtered.append(signal)

    return filtered, dropped


def _visual_analysis_from_signals(
    signals: list[str],
    scene_summary: str,
    limitations: list[str],
    evidence: str,
    model_findings: list[VisualFinding] | None = None,
    image_bytes: bytes | None = None,
) -> VisualAnalysis:
    model_findings = model_findings or []
    candidate_signals = _dedupe(signals + [finding.label for finding in model_findings] or _map_text_to_signals(scene_summary))
    clean_signals, dropped_signals = _filter_model_signals(candidate_signals, scene_summary, model_findings, image_bytes)
    finding_labels = {finding.label for finding in model_findings}
    findings = [finding for finding in model_findings if finding.label in clean_signals]
    findings.extend(
        VisualFinding(
            label=signal,
            confidence=0.82,
            evidence=evidence,
        )
        for signal in clean_signals
        if signal not in finding_labels
    )
    output_limitations = list(limitations)
    if dropped_signals:
        output_limitations.append(
            "Removed unsubstantiated fire/smoke labels because the image evidence did not clearly support them."
        )
    return VisualAnalysis(
        image_used=True,
        scene_summary=scene_summary or _fallback_scene_summary(clean_signals, True),
        visual_signals=clean_signals,
        findings=findings,
        limitations=output_limitations
        or ["Vision output is limited to hazard labels; no identity analysis is performed."],
    )


def _vision_prompt(text: str) -> list[dict[str, object]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a privacy-preserving crisis image analyst. Return JSON only. "
                "Identify hazards and scene conditions, not people. Never identify faces, license plates, suspects, or private individuals. "
                "Analyze only the attached image and current report; do not carry over hazards from previous turns. "
                "Do not include speculative hazards. Only include fire or smoke when flames, a smoke plume, thick smoke, or active burning is directly visible. "
                "Allowed visual_signals include floodwater, fast_water, smoke, fire, crash, blocked_road, fallen_wire, "
                "possible_electrical_hazard, injured_person_possible, structural_damage, polluted_water, algae_bloom, "
                "dead_fish, benthic_observation, lichen_observation, signage_text, personal_safety_threat. "
                "Use personal_safety_threat for apparent robbery, mugging, threatening posture, or visible weapon risk, "
                "without identifying any person. "
                "If the user text is vague, infer the crisis type from the image hazards. "
                "Return JSON with keys: scene_summary, visual_signals, findings, limitations. "
                "Each finding must include label, confidence, and visual evidence."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Report context: {text}. Return JSON with scene_summary, visual_signals, findings, and limitations."},
            ],
        },
    ]


def _image_data_url(image_bytes: bytes) -> str:
    mime = "image/jpeg"
    try:
        from PIL import Image

        image = Image.open(BytesIO(image_bytes))
        fmt = (image.format or "").lower()
        if fmt == "png":
            mime = "image/png"
        elif fmt == "webp":
            mime = "image/webp"
        elif fmt in {"jpg", "jpeg"}:
            mime = "image/jpeg"
    except Exception:
        pass
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{image_b64}"


def _foundry_multimodal_analysis(image_bytes: bytes, text: str) -> VisualAnalysis:
    settings = get_settings()
    from openai import OpenAI

    messages = _vision_prompt(text)
    messages[1]["content"].append(  # type: ignore[index, union-attr]
        {
            "type": "image_url",
            "image_url": {"url": _image_data_url(image_bytes)},
        }
    )

    if settings.foundry_uses_api_key:
        api_key = settings.azure_foundry_api_key
        credential = None
    else:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        credential = DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_interactive_browser_credential=not settings.azure_foundry_allow_interactive_login,
        )
        api_key = get_bearer_token_provider(credential, settings.azure_foundry_token_scope)

    try:
        client = OpenAI(
            base_url=settings.azure_foundry_project_endpoint.rstrip("/") + "/openai/v1/",
            api_key=api_key,
        )
        response = client.chat.completions.create(
            model=settings.azure_foundry_model_deployment,
            temperature=0,
            max_tokens=300,
            messages=messages,
        )
    finally:
        if credential is not None and hasattr(credential, "close"):
            credential.close()

    content = response.choices[0].message.content or "{}"
    signals, scene_summary, limitations, findings = _json_from_model_text(content)
    return _visual_analysis_from_signals(
        signals,
        scene_summary,
        limitations,
        "Foundry multimodal GPT model mapped image content to privacy-safe hazard labels.",
        model_findings=findings,
        image_bytes=image_bytes,
    )


def _azure_openai_vision_analysis(image_bytes: bytes, text: str) -> VisualAnalysis:
    settings = get_settings()
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    messages = _vision_prompt(text)
    messages[1]["content"].append(  # type: ignore[index, union-attr]
        {
            "type": "image_url",
            "image_url": {"url": _image_data_url(image_bytes)},
        }
    )
    response = client.chat.completions.create(
        model=settings.azure_openai_vision_deployment,
        temperature=0,
        max_tokens=350,
        messages=messages,
    )
    content = response.choices[0].message.content or "{}"
    signals, scene_summary, limitations, findings = _json_from_model_text(content)
    return _visual_analysis_from_signals(
        signals,
        scene_summary,
        limitations,
        "Azure OpenAI vision model mapped image content to privacy-safe hazard label.",
        model_findings=findings,
        image_bytes=image_bytes,
    )


def analyze_image(
    text: str,
    image_bytes: bytes | None = None,
    sample_scenario: str | None = None,
) -> VisualAnalysis:
    settings = get_settings()
    image_present = bool(image_bytes or sample_scenario)

    if (
        image_bytes
        and settings.live_foundry_enabled
        and settings.azure_foundry_model_deployment
        and not settings.demo_mode
    ):
        try:
            return _enrich_visual_analysis(
                _foundry_multimodal_analysis(image_bytes, text),
                text,
                sample_scenario,
                image_bytes,
            )
        except Exception:
            pass

    if image_bytes and settings.azure_openai_vision_configured and not settings.demo_mode:
        try:
            return _enrich_visual_analysis(
                _azure_openai_vision_analysis(image_bytes, text),
                text,
                sample_scenario,
                image_bytes,
            )
        except Exception:
            pass

    if image_bytes and settings.azure_vision_configured and not settings.demo_mode:
        try:
            return _enrich_visual_analysis(
                _azure_vision_analysis(image_bytes),
                text,
                sample_scenario,
                image_bytes,
            )
        except Exception:
            pass

    return _fallback_visual_analysis(text, sample_scenario, image_present, image_bytes)
