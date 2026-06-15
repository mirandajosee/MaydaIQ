"""Microsoft Foundry / Foundry IQ adapter with deterministic local fallback.

The preferred live path calls an existing Foundry agent that already has the
knowledge documents attached. That means MaydaIQ does not need to know the
internal knowledge-base id at runtime; the agent owns retrieval.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from src.config import get_settings
from src.schemas import RetrievedPlaybook
from src.tools.local_retrieval import retrieve_local_playbooks


logging.getLogger("azure.identity").setLevel(logging.CRITICAL)


def _build_credential(settings):
    if settings.service_principal_configured:
        from azure.identity import ClientSecretCredential

        return ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential(
        exclude_environment_credential=True,
        exclude_interactive_browser_credential=not settings.azure_foundry_allow_interactive_login,
    )


def _live_prompt(
    query: str,
    incident_type: str,
    max_results: int,
    target_language: str = "English",
    location_text: str | None = None,
    response_entities: list[str] | None = None,
    response_contacts: list[str] | None = None,
) -> str:
    settings = get_settings()
    location = location_text or "not provided"
    entities = ", ".join(response_entities or []) or "relevant local emergency, public works, utility, health, or environmental agencies"
    contacts = ", ".join(response_contacts or []) or settings.emergency_contact_text
    return (
        "You are the MaydaIQ Foundry grounding agent. Use only your configured knowledge documents "
        "and attached retrieval tools for crisis response grounding. Do not reveal chain-of-thought. "
        "Do not identify people, faces, suspects, or license plates. Do not claim to contact authorities. "
        "Return a concise responder-ready answer in the target language. Include: a 1-2 sentence AI brief, "
        "immediate safe actions, avoid-list guidance, uncertainty notes, and source labels when available. "
        "If location/context is provided, include explicit contact to the local police, fire, or medical services if the situation seems life-threatening, time-sensitive or necessary. If not"
        "explicitly in the escalation/contact guidance, just having the location should be enough. If location or context is not clear enough, say to use local emergency services "
        "and the relevant public agency. Never invent exact phone numbers or agency names not present in context, but always try to provide it if possible.\n\n"
        f"Target language: {target_language}\n"
        f"Incident type: {incident_type}\n"
        f"Max snippets: {max_results}\n"
        f"Approximate location/context: {location}\n"
        f"Verified/configured emergency contacts for this context: {contacts}\n"
        f"Potential collaborator entities: {entities}\n"
        f"Report and visual hazard query: {query}"
    )


def _project_openai_base_url(project_endpoint: str) -> str:
    return project_endpoint.rstrip("/") + "/openai/v1/"


def _extract_text_from_message(message: object) -> str:
    parts: list[str] = []
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, Iterable):
        for item in content:
            text_obj = getattr(item, "text", None)
            if isinstance(item, dict):
                text_obj = item.get("text") or item.get("content")
            if isinstance(text_obj, str):
                parts.append(text_obj)
            elif text_obj is not None:
                value = getattr(text_obj, "value", None)
                if value:
                    parts.append(str(value))
                else:
                    parts.append(str(text_obj))
    if not parts and content:
        parts.append(str(content))
    return "\n".join(part for part in parts if part).strip()


def _extract_citations_from_text(text: str, settings) -> list[str]:
    citations: list[str] = []
    for marker in ("local:", "foundry:", "source:", "doc:"):
        for token in text.replace(",", " ").replace("]", " ").replace("[", " ").split():
            if token.lower().startswith(marker):
                citations.append(token.rstrip(".;:"))
    if settings.foundry_iq_knowledge_base_id:
        citations.append(f"foundry-iq:{settings.foundry_iq_knowledge_base_id}")
    if settings.azure_foundry_agent_id:
        citations.append(f"foundry-agent:{settings.azure_foundry_agent_id}")
    elif settings.azure_foundry_agent_name:
        citations.append(f"foundry-agent:{settings.azure_foundry_agent_name}")
    return sorted(set(citations))


def _as_playbook(text: str, incident_type: str, settings) -> list[RetrievedPlaybook]:
    text = text.strip() or "Foundry agent returned no text content."
    citations = _extract_citations_from_text(text, settings)
    return [
        RetrievedPlaybook(
            source_id=citations[0] if citations else "foundry-agent:live",
            title="Microsoft Foundry grounded response playbook",
            snippet=text[:1200],
            relevance=0.92,
            citations=citations or ["foundry-agent:live"],
        )
    ]


def _resolve_agent_name(project_client, settings) -> str:
    if settings.azure_foundry_agent_name:
        return settings.azure_foundry_agent_name

    configured = settings.azure_foundry_agent_id
    try:
        for agent in project_client.agents.list(limit=100):
            agent_id = str(getattr(agent, "id", "") or "")
            agent_name = str(getattr(agent, "name", "") or "")
            if configured in {agent_id, agent_name}:
                return agent_name or configured
    except Exception:
        pass
    return configured


def _agent_reference(settings, project_client=None) -> dict[str, str]:
    name = settings.azure_foundry_agent_name or settings.azure_foundry_agent_id
    if project_client is not None and not settings.azure_foundry_agent_name:
        name = _resolve_agent_name(project_client, settings)

    reference = {
        "name": name,
        "type": "agent_reference",
    }
    if settings.azure_foundry_agent_version:
        reference["version"] = settings.azure_foundry_agent_version
    return reference


def _response_model(settings) -> str:
    if not settings.azure_foundry_model_deployment:
        raise RuntimeError("Missing AZURE_FOUNDRY_MODEL_DEPLOYMENT; Foundry Responses API requires model deployment.")
    return settings.azure_foundry_model_deployment


def _retrieve_with_classic_agent_id(
    query: str,
    incident_type: str,
    max_results: int,
    target_language: str,
    location_text: str | None,
    response_entities: list[str] | None,
    response_contacts: list[str] | None,
) -> list[RetrievedPlaybook]:
    settings = get_settings()
    from azure.ai.projects import AIProjectClient

    prompt = _live_prompt(
        query,
        incident_type,
        max_results,
        target_language,
        location_text,
        response_entities,
        response_contacts,
    )
    messages = []
    credential = _build_credential(settings)
    try:
        with AIProjectClient(endpoint=settings.azure_foundry_project_endpoint, credential=credential) as project_client:
            agents_ops = project_client.agents
            if not hasattr(agents_ops, "get_agent") or not hasattr(agents_ops, "threads"):
                raise AttributeError("Installed SDK exposes the new agent API, not classic threads/get_agent.")

            # From your Foundry agent setup: AZURE_FOUNDRY_AGENT_ID
            agent = agents_ops.get_agent(settings.azure_foundry_agent_id)
            thread = agents_ops.threads.create()
            agents_ops.messages.create(thread_id=thread.id, role="user", content=prompt)
            run = agents_ops.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
            if getattr(run, "status", None) == "failed":
                raise RuntimeError(f"Foundry agent run failed: {getattr(run, 'last_error', 'unknown')}")
            messages = list(agents_ops.messages.list(thread_id=thread.id))
    finally:
        if hasattr(credential, "close"):
            credential.close()

    assistant_text = ""
    for message in messages:
        role = getattr(message, "role", "")
        if role == "assistant":
            assistant_text = _extract_text_from_message(message)
            if assistant_text:
                break
    if not assistant_text:
        assistant_text = "\n".join(_extract_text_from_message(message) for message in messages[:3])
    return _as_playbook(assistant_text, incident_type, settings)[:max_results]


def _retrieve_with_agent_name_responses(
    query: str,
    incident_type: str,
    max_results: int,
    target_language: str,
    location_text: str | None,
    response_entities: list[str] | None,
    response_contacts: list[str] | None,
) -> list[RetrievedPlaybook]:
    settings = get_settings()
    from azure.ai.projects import AIProjectClient
    from azure.identity import get_bearer_token_provider
    from openai import OpenAI

    prompt = _live_prompt(
        query,
        incident_type,
        max_results,
        target_language,
        location_text,
        response_entities,
        response_contacts,
    )

    if settings.foundry_uses_api_key:
        return _retrieve_with_agent_name_api_key(
            query,
            incident_type,
            max_results,
            target_language,
            location_text,
            response_entities,
            response_contacts,
        )

    credential = _build_credential(settings)
    try:
        with AIProjectClient(endpoint=settings.azure_foundry_project_endpoint, credential=credential) as project_client:
            token_provider = get_bearer_token_provider(
                credential,
                settings.azure_foundry_token_scope,
            )
            openai_client = OpenAI(
                base_url=_project_openai_base_url(settings.azure_foundry_project_endpoint),
                api_key=token_provider,
            )
            response = openai_client.responses.create(
                model=_response_model(settings),
                input=[{"role": "user", "content": prompt}],
                extra_body={"agent_reference": _agent_reference(settings, project_client)},
            )
    finally:
        if hasattr(credential, "close"):
            credential.close()

    return _as_playbook(getattr(response, "output_text", ""), incident_type, settings)[:max_results]


def _retrieve_with_agent_name_api_key(
    query: str,
    incident_type: str,
    max_results: int,
    target_language: str,
    location_text: str | None,
    response_entities: list[str] | None,
    response_contacts: list[str] | None,
) -> list[RetrievedPlaybook]:
    settings = get_settings()
    from openai import OpenAI

    prompt = _live_prompt(
        query,
        incident_type,
        max_results,
        target_language,
        location_text,
        response_entities,
        response_contacts,
    )
    client = OpenAI(
        base_url=_project_openai_base_url(settings.azure_foundry_project_endpoint),
        api_key=settings.azure_foundry_api_key,
    )
    response = client.responses.create(
        model=_response_model(settings),
        input=[{"role": "user", "content": prompt}],
        extra_body={"agent_reference": _agent_reference(settings)},
    )
    return _as_playbook(getattr(response, "output_text", ""), incident_type, settings)[:max_results]


def _retrieve_live_with_foundry_agent(
    query: str,
    incident_type: str,
    max_results: int,
    target_language: str,
    location_text: str | None,
    response_entities: list[str] | None,
    response_contacts: list[str] | None,
) -> list[RetrievedPlaybook]:
    settings = get_settings()
    errors: list[str] = []

    if settings.azure_foundry_agent_id.startswith("asst") and settings.foundry_uses_entra:
        try:
            return _retrieve_with_classic_agent_id(
                query,
                incident_type,
                max_results,
                target_language,
                location_text,
                response_entities,
                response_contacts,
            )
        except Exception as exc:
            errors.append(f"classic_agent_id_path={type(exc).__name__}:{str(exc)[:180]}")

    if settings.azure_foundry_agent_name or settings.azure_foundry_agent_id:
        try:
            return _retrieve_with_agent_name_responses(
                query,
                incident_type,
                max_results,
                target_language,
                location_text,
                response_entities,
                response_contacts,
            )
        except Exception as exc:
            errors.append(f"responses_agent_reference_path={type(exc).__name__}:{str(exc)[:180]}")

    raise RuntimeError("; ".join(errors) or "No Foundry agent id/name configured.")


def _foundry_config_hint(settings) -> RetrievedPlaybook:
    missing = []
    if settings.demo_mode:
        missing.append("DEMO_MODE=false")
    if not settings.azure_foundry_project_endpoint:
        missing.append("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    if not settings.azure_foundry_agent_id and not settings.azure_foundry_agent_name:
        missing.append("AZURE_FOUNDRY_AGENT_ID or AZURE_FOUNDRY_AGENT_NAME")
    hint = (
        "Live Foundry retrieval is not active. Set "
        + ", ".join(missing)
        + ". Falling back to local demo knowledge."
    )
    return RetrievedPlaybook(
        source_id="runtime:local-fallback",
        title="Runtime fallback notice",
        snippet=hint,
        relevance=0.3,
        citations=["runtime:local-fallback"],
    )


def retrieve_from_foundry_iq(
    query: str,
    incident_type: str,
    max_results: int = 5,
    target_language: str = "English",
    location_text: str | None = None,
    response_entities: list[str] | None = None,
    response_contacts: list[str] | None = None,
) -> list[RetrievedPlaybook]:
    """Retrieve grounded playbooks from Foundry IQ or local Markdown.

    In demo mode, or when credentials/SDKs are unavailable, this function uses
    local knowledge files so the hackathon demo is deterministic.
    """

    settings = get_settings()
    if settings.live_foundry_enabled:
        try:
            print("FOUNDRY_AGENT_LIVE")
            return _retrieve_live_with_foundry_agent(
                query,
                incident_type,
                max_results,
                target_language,
                location_text,
                response_entities,
                response_contacts,
            )
        except Exception as exc:
            hint = ""
            message = str(exc)
            if "OBO auth" in message and "API key" in message:
                hint = " hint=Set AZURE_FOUNDRY_AUTH_MODE=entra and use Azure CLI login or service principal."
            elif "DefaultAzureCredential failed" in message or "ClientAuthenticationError" in message:
                hint = (
                    " hint=Install Azure CLI in this process PATH and run az login, set "
                    "AZURE_TENANT_ID/AZURE_CLIENT_ID/AZURE_CLIENT_SECRET, or set "
                    "AZURE_FOUNDRY_ALLOW_INTERACTIVE_LOGIN=true for local-only testing."
                )
            print(f"LOCAL_DEMO_RETRIEVAL live_adapter_failed={type(exc).__name__}:{message[:220]}{hint}")
            return retrieve_local_playbooks(query, incident_type, max_results)

    print("LOCAL_DEMO_RETRIEVAL")
    playbooks = retrieve_local_playbooks(query, incident_type, max_results)
    if not settings.demo_mode and not settings.foundry_agent_configured:
        return [_foundry_config_hint(settings)] + playbooks[: max_results - 1]
    return playbooks
