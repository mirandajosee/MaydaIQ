"""Local Markdown retrieval fallback for demo mode."""

from __future__ import annotations

from pathlib import Path

from src.config import KNOWLEDGE_DIR
from src.schemas import RetrievedPlaybook
from src.tools.risk_scoring import normalize_text


INCIDENT_TO_FILES: dict[str, list[str]] = {
    "flood": ["emergency_flood.md", "electrical_hazards.md", "community_reporting_schema.md", "safety_policy.md"],
    "fire_smoke": ["emergency_fire_smoke.md", "community_reporting_schema.md", "safety_policy.md"],
    "traffic_accident": ["emergency_traffic_accident.md", "community_reporting_schema.md", "safety_policy.md"],
    "personal_safety_robbery": ["personal_safety_robbery.md", "community_reporting_schema.md", "safety_policy.md"],
    "electrical_hazard": ["electrical_hazards.md", "emergency_flood.md", "community_reporting_schema.md", "safety_policy.md"],
    "environmental_water_quality": [
        "environmental_water_quality_benthic.md",
        "community_reporting_schema.md",
        "safety_policy.md",
    ],
    "environmental_air_quality": [
        "environmental_air_quality_lichen.md",
        "community_reporting_schema.md",
        "safety_policy.md",
    ],
    "general_safety": ["safety_policy.md", "community_reporting_schema.md"],
}


def _extract_source_id(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.lower().startswith("source_id:"):
            return line.split(":", 1)[1].strip()
    return fallback


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ").replace(".md", "").title()


def _extract_snippet(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    useful: list[str] = []
    capture = False
    for line in lines:
        lower = line.lower()
        if lower.startswith("## immediate_actions") or lower.startswith("## calm_mode_guidance"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("- "):
            useful.append(line[2:])
        if len(useful) >= 2:
            break
    if useful:
        return " ".join(useful)
    return " ".join(lines[:4])[:360]


def _rank(content: str, query: str, filename: str, incident_type: str) -> float:
    normalized_content = normalize_text(content)
    normalized_query = normalize_text(query)
    terms = {term for term in normalized_query.split() if len(term) > 3}
    hits = sum(1 for term in terms if term in normalized_content)
    direct = 4 if incident_type.replace("_", " ") in normalized_content or incident_type in filename else 0
    return min(1.0, (hits + direct) / 12)


def retrieve_local_playbooks(query: str, incident_type: str, max_results: int = 5) -> list[RetrievedPlaybook]:
    candidates = INCIDENT_TO_FILES.get(incident_type, INCIDENT_TO_FILES["general_safety"])
    ranked: list[tuple[float, Path, str]] = []
    for filename in candidates:
        path = KNOWLEDGE_DIR / filename
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        ranked.append((_rank(content, query, filename, incident_type), path, content))

    ranked.sort(key=lambda item: item[0], reverse=True)
    playbooks: list[RetrievedPlaybook] = []
    for relevance, path, content in ranked[:max_results]:
        source_id = _extract_source_id(content, path.stem)
        playbooks.append(
            RetrievedPlaybook(
                source_id=source_id,
                title=_extract_title(content, path.name),
                snippet=_extract_snippet(content),
                relevance=max(relevance, 0.35),
                citations=[source_id],
            )
        )
    return playbooks

