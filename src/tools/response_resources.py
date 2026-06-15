"""Emergency contact and collaborator recommendations."""

from __future__ import annotations

from dataclasses import dataclass
import re

from src.config import get_settings


RESOURCE_MAP: dict[str, list[str]] = {
    "flood": ["emergency management", "utility crew", "road crew", "rescue"],
    "fire_smoke": ["fire service", "medical responders", "building management", "emergency management"],
    "traffic_accident": ["medical responders", "traffic control", "road crew", "law enforcement"],
    "personal_safety_robbery": ["law enforcement", "victim support", "nearby safe site"],
    "electrical_hazard": ["utility emergency crew", "fire service", "road crew", "emergency management"],
    "environmental_water_quality": ["environmental agency", "public works", "community science coordinator"],
    "environmental_air_quality": ["environmental health", "air quality agency", "community science coordinator"],
    "general_safety": ["emergency management", "human reviewer"],
}


@dataclass(frozen=True)
class ResponseContact:
    service: str
    phone: str
    resources: tuple[str, ...]
    locations: tuple[str, ...]
    source: str = "configured"
    priority: int = 50

    def display(self) -> str:
        return f"{self.service}: {self.phone}"


ARGENTINA_CONTACTS: tuple[ResponseContact, ...] = (
    ResponseContact(
        service="Emergencias generales",
        phone="911",
        resources=("law enforcement", "medical responders", "fire service", "rescue", "traffic control", "emergency management"),
        locations=("argentina", "cordoba", "córdoba", "buen pastor", "nueva cordoba", "nueva córdoba", "cba"),
        source="Argentina public emergency short code",
        priority=1,
    ),
    ResponseContact(
        service="Bomberos",
        phone="100",
        resources=("fire service", "rescue", "emergency management"),
        locations=("argentina", "cordoba", "córdoba", "buen pastor", "nueva cordoba", "nueva córdoba", "cba"),
        source="Argentina public emergency short code",
        priority=2,
    ),
    ResponseContact(
        service="Emergencias medicas",
        phone="107",
        resources=("medical responders",),
        locations=("argentina", "cordoba", "córdoba", "buen pastor", "nueva cordoba", "nueva córdoba", "cba"),
        source="Argentina public emergency short code",
        priority=2,
    ),
    ResponseContact(
        service="Policia",
        phone="101",
        resources=("law enforcement", "traffic control"),
        locations=("argentina", "cordoba", "córdoba", "buen pastor", "nueva cordoba", "nueva córdoba", "cba"),
        source="Argentina public emergency short code",
        priority=3,
    ),
    ResponseContact(
        service="Defensa Civil",
        phone="103",
        resources=("emergency management", "road crew", "utility emergency crew", "utility crew", "public works"),
        locations=("argentina", "cordoba", "córdoba", "buen pastor", "nueva cordoba", "nueva córdoba", "cba"),
        source="Argentina public emergency short code",
        priority=4,
    ),
)

UNITED_STATES_CONTACTS: tuple[ResponseContact, ...] = (
    ResponseContact(
        service="Police / emergency services",
        phone="911",
        resources=("law enforcement", "medical responders", "fire service", "rescue", "traffic control", "emergency management"),
        locations=("united states", "usa", "u.s.", "us", "denver", "colorado", "co"),
        source="United States emergency short code",
        priority=1,
    ),
)


def configured_response_entities() -> list[str]:
    raw = get_settings().public_response_entities
    if not raw:
        return []
    return [item.strip() for item in re.split(r"[;,]", raw) if item.strip()]


def recommended_entities(incident_type: str) -> list[str]:
    entities = configured_response_entities() + RESOURCE_MAP.get(incident_type, RESOURCE_MAP["general_safety"])
    return list(dict.fromkeys(entities))


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _configured_contacts() -> list[ResponseContact]:
    raw = get_settings().public_response_contacts
    contacts: list[ResponseContact] = []
    if not raw:
        return contacts

    for chunk in re.split(r"[;\n]", raw):
        item = chunk.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split("|")]
        service = parts[0] if parts else ""
        phone = parts[1] if len(parts) > 1 else ""
        resource_text = parts[2] if len(parts) > 2 else ""
        location_text = parts[3] if len(parts) > 3 else ""
        if not service or not phone:
            continue
        contacts.append(
            ResponseContact(
                service=service,
                phone=phone,
                resources=tuple(part.strip().lower() for part in re.split(r"[,/]", resource_text) if part.strip())
                or ("general_safety",),
                locations=tuple(part.strip().lower() for part in re.split(r"[,/]", location_text) if part.strip())
                or ("*",),
                source="configured public response contact",
                priority=0,
            )
        )
    return contacts


def _location_matches(contact: ResponseContact, location_text: str | None) -> bool:
    if "*" in contact.locations:
        return True
    normalized_location = _normalize(location_text)
    if not normalized_location:
        return False
    if "spain" in normalized_location or "españa" in normalized_location:
        return False
    return any(location in normalized_location for location in contact.locations)


def _resource_matches(contact: ResponseContact, resources: list[str]) -> bool:
    normalized_resources = {_normalize(resource) for resource in resources}
    return bool(normalized_resources.intersection(set(contact.resources)))


def recommended_contacts(incident_type: str, location_text: str | None = None, max_contacts: int = 3) -> list[ResponseContact]:
    if not location_text:
        return []

    resources = recommended_entities(incident_type)
    contacts = _configured_contacts() + list(ARGENTINA_CONTACTS) + list(UNITED_STATES_CONTACTS)
    ranked = [
        contact
        for contact in contacts
        if _location_matches(contact, location_text) and _resource_matches(contact, resources)
    ]
    ranked.sort(key=lambda contact: contact.priority)

    deduped: list[ResponseContact] = []
    seen: set[tuple[str, str]] = set()
    for contact in ranked:
        key = (contact.service.lower(), contact.phone)
        if key in seen:
            continue
        deduped.append(contact)
        seen.add(key)
        if len(deduped) >= max_contacts:
            break
    return deduped


def contact_guidance(incident_type: str, location_text: str | None = None) -> list[str]:
    return [contact.display() for contact in recommended_contacts(incident_type, location_text)]


def escalation_text(incident_type: str = "general_safety", location_text: str | None = None) -> str:
    contact = get_settings().emergency_contact_text
    contacts = contact_guidance(incident_type, location_text)
    context = f" for {location_text}" if location_text else ""
    entities = ", ".join(recommended_entities(incident_type)[:4])
    if contacts:
        return f"Contact {', '.join(contacts)}{context} now for immediate danger. Coordinate with {entities}."
    return f"Contact {contact}{context} now for immediate danger. Coordinate with {entities}."
