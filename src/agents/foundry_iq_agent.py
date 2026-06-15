"""Foundry IQ retrieval agent."""

from __future__ import annotations

from src.schemas import RetrievedPlaybook
from src.tools.foundry_iq_retrieval import retrieve_from_foundry_iq


class FoundryIQAgent:
    name = "FoundryIQAgent"

    def run(
        self,
        query: str,
        incident_type: str,
        max_results: int = 5,
        target_language: str = "English",
        location_text: str | None = None,
        response_entities: list[str] | None = None,
        response_contacts: list[str] | None = None,
    ) -> list[RetrievedPlaybook]:
        return retrieve_from_foundry_iq(
            query=query,
            incident_type=incident_type,
            max_results=max_results,
            target_language=target_language,
            location_text=location_text,
            response_entities=response_entities,
            response_contacts=response_contacts,
        )
