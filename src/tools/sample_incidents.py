"""Deterministic sample incidents for the Streamlit demo and evals."""

from __future__ import annotations

SAMPLE_INCIDENTS: dict[str, dict[str, object]] = {
    "flood_electrical": {
        "label": "Flooded street with possible electrical hazard",
        "incident_type": "flood",
        "text": (
            "A street is flooded after heavy rain. Water is moving fast near a utility pole "
            "and people are unsure whether a wire is down."
        ),
        "visual_signals": ["floodwater", "fast_water", "possible_electrical_hazard", "fallen_wire"],
    },
    "fire_smoke": {
        "label": "Smoke/fire near building",
        "incident_type": "fire_smoke",
        "text": "There is thick smoke coming from the side of an apartment building and people may still be inside.",
        "visual_signals": ["smoke", "fire", "inside_building"],
    },
    "traffic_injury": {
        "label": "Traffic accident with injured person",
        "incident_type": "traffic_accident",
        "text": "Two cars crashed at an intersection. One person may be injured and traffic is blocked.",
        "visual_signals": ["crash", "injured_person_possible", "blocked_road"],
    },
    "robbery_threat": {
        "label": "Robbery / personal safety threat",
        "incident_type": "personal_safety_robbery",
        "text": "Someone nearby says they were robbed and the person who threatened them may still be close.",
        "visual_signals": ["personal_safety_threat"],
    },
    "water_pollution": {
        "label": "Suspicious water pollution / benthic bioindicator report",
        "incident_type": "environmental_water_quality",
        "text": (
            "Volunteers found cloudy water, possible algae, and very few benthic macroinvertebrates "
            "in a neighborhood creek."
        ),
        "visual_signals": ["polluted_water", "algae_bloom", "benthic_observation"],
    },
    "air_quality_lichen": {
        "label": "Air quality / lichen citizen science report",
        "incident_type": "environmental_air_quality",
        "text": (
            "A citizen science group is comparing lichen growth near a busy road and a park "
            "to screen for possible air quality differences."
        ),
        "visual_signals": ["lichen_observation"],
    },
}


def list_sample_incidents() -> list[tuple[str, str]]:
    return [(key, str(value["label"])) for key, value in SAMPLE_INCIDENTS.items()]


def get_sample_incident(key: str) -> dict[str, object]:
    return SAMPLE_INCIDENTS[key]

