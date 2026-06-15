"""Deterministic risk scoring for MaydaIQ demo reliability."""

from __future__ import annotations

from collections import Counter

from src.schemas import Confidence, RiskLevel, SelectedMode, VisualAnalysis


BASE_SCORES: dict[str, int] = {
    "fire_smoke": 80,
    "flood": 75,
    "traffic_accident": 70,
    "personal_safety_robbery": 75,
    "electrical_hazard": 85,
    "environmental_water_quality": 45,
    "environmental_air_quality": 35,
    "general_safety": 30,
}

INCIDENT_KEYWORDS: dict[str, set[str]] = {
    "fire_smoke": {"fire", "smoke", "burning", "flames", "evacuate", "inside building"},
    "flood": {"flood", "flooded", "water rising", "fast water", "storm surge", "standing water"},
    "traffic_accident": {"crash", "collision", "accident", "vehicle", "car", "road blocked", "injured"},
    "personal_safety_robbery": {"robbery", "robbed", "threat", "weapon", "violence", "assault", "unsafe person"},
    "electrical_hazard": {"wire", "downed line", "electricity", "electrical", "utility pole", "spark"},
    "environmental_water_quality": {
        "polluted",
        "algae",
        "dead fish",
        "benthic",
        "macroinvertebrate",
        "creek",
        "water quality",
    },
    "environmental_air_quality": {"lichen", "air quality", "particulate", "pollution near road", "bioindicator"},
}

VISUAL_TO_INCIDENT: dict[str, str] = {
    "smoke": "fire_smoke",
    "fire": "fire_smoke",
    "floodwater": "flood",
    "fast_water": "flood",
    "crash": "traffic_accident",
    "blocked_road": "traffic_accident",
    "injured_person_possible": "traffic_accident",
    "personal_safety_threat": "personal_safety_robbery",
    "fallen_wire": "electrical_hazard",
    "possible_electrical_hazard": "electrical_hazard",
    "polluted_water": "environmental_water_quality",
    "algae_bloom": "environmental_water_quality",
    "dead_fish": "environmental_water_quality",
    "benthic_observation": "environmental_water_quality",
    "lichen_observation": "environmental_air_quality",
}

URGENCY_KEYWORDS: set[str] = {
    "trapped",
    "injured",
    "children",
    "elderly",
    "night",
    "electricity",
    "electrical",
    "fast water",
    "inside building",
    "can't leave",
    "cant leave",
    "cannot leave",
    "weapon",
    "fire",
    "smoke",
    "wire",
}

PREPAREDNESS_KEYWORDS: set[str] = {
    "prepare",
    "preparedness",
    "plan",
    "planning",
    "drill",
    "training",
    "after",
    "post-incident",
    "mitigation",
    "prevention",
}


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def detect_incident_type(text: str, visual_signals: list[str] | None = None) -> str:
    normalized = normalize_text(text)
    visual_signals = visual_signals or []
    scores: Counter[str] = Counter()

    for signal in visual_signals:
        incident = VISUAL_TO_INCIDENT.get(signal)
        if incident:
            scores[incident] += 3

    for incident, keywords in INCIDENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                scores[incident] += 1

    if not scores:
        return "general_safety"

    if scores["flood"] > 0 and scores["electrical_hazard"] > 0:
        return "flood"

    return scores.most_common(1)[0][0]


def detect_urgency_signals(text: str, visual_signals: list[str] | None = None) -> list[str]:
    normalized = normalize_text(text)
    signals = {keyword for keyword in URGENCY_KEYWORDS if keyword in normalized}
    for visual_signal in visual_signals or []:
        if visual_signal in {"fallen_wire", "possible_electrical_hazard"}:
            signals.add("electricity")
        if visual_signal in {"injured_person_possible"}:
            signals.add("injured")
        if visual_signal in {"fast_water"}:
            signals.add("fast water")
        if visual_signal in {"smoke", "fire"}:
            signals.add(visual_signal)
        if visual_signal == "inside_building":
            signals.add("inside building")
    return sorted(signals)


def is_preparedness_context(text: str) -> bool:
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in PREPAREDNESS_KEYWORDS)


def risk_level_for_score(score: int) -> RiskLevel:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MODERATE"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"


def choose_mode(requested_mode: str, score: int, urgency_signals: list[str]) -> SelectedMode:
    if requested_mode == "Alert":
        return "ALERT"
    if requested_mode == "Calm":
        return "CALM"
    if score >= 61 or urgency_signals:
        return "ALERT"
    return "CALM"


def confidence_for(text: str, incident_type: str, visual_analysis: VisualAnalysis, urgency_signals: list[str]) -> Confidence:
    if incident_type == "general_safety":
        return "LOW"
    if visual_analysis.visual_signals or len(urgency_signals) >= 2 or len(text.split()) >= 12:
        return "HIGH"
    return "MEDIUM"


def score_risk(text: str, visual_analysis: VisualAnalysis, requested_mode: str) -> tuple[int, str, list[str], Confidence]:
    incident_type = detect_incident_type(text, visual_analysis.visual_signals)
    base = BASE_SCORES.get(incident_type, BASE_SCORES["general_safety"])
    urgency_signals = detect_urgency_signals(text, visual_analysis.visual_signals)

    score = base + 10 * len(urgency_signals)
    if is_preparedness_context(text) and not urgency_signals and requested_mode != "Alert":
        score = max(20, score - 25)

    score = min(score, 100)
    confidence = confidence_for(text, incident_type, visual_analysis, urgency_signals)
    return score, incident_type, urgency_signals, confidence

