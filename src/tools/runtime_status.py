"""Runtime status helpers that never expose secret values."""

from __future__ import annotations

from src.config import get_settings


def get_runtime_status() -> dict[str, object]:
    settings = get_settings()
    missing_for_live: list[str] = []
    if not settings.azure_foundry_project_endpoint:
        missing_for_live.append("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    if not settings.azure_foundry_agent_id and not settings.azure_foundry_agent_name:
        missing_for_live.append("AZURE_FOUNDRY_AGENT_ID or AZURE_FOUNDRY_AGENT_NAME")
    if settings.live_foundry_enabled and settings.foundry_uses_entra and not settings.service_principal_configured:
        missing_for_live.append("Entra credential: run az login or set service-principal variables")

    if settings.foundry_uses_api_key:
        auth_mode = "api_key"
    elif settings.service_principal_configured:
        auth_mode = "service_principal"
    else:
        auth_mode = "default_azure_credential"
    if settings.demo_mode:
        mode = "LOCAL_DEMO"
    elif settings.foundry_agent_configured:
        mode = "FOUNDRY_LIVE_READY"
    else:
        mode = "LOCAL_FALLBACK_MISSING_CONFIG"

    return {
        "mode": mode,
        "demo_mode": settings.demo_mode,
        "foundry_agent_configured": settings.foundry_agent_configured,
        "auth_mode": auth_mode,
        "missing_for_live": missing_for_live,
        "endpoint_present": bool(settings.azure_foundry_project_endpoint),
        "agent_id_present": bool(settings.azure_foundry_agent_id),
        "agent_name_present": bool(settings.azure_foundry_agent_name),
        "model_deployment_present": bool(settings.azure_foundry_model_deployment),
        "api_key_present": settings.foundry_api_key_configured,
        "auth_mode_setting": settings.azure_foundry_auth_mode,
        "foundry_iq_knowledge_base_id_present": bool(settings.foundry_iq_knowledge_base_id),
        "azure_vision_configured": settings.azure_vision_configured,
        "azure_openai_vision_configured": settings.azure_openai_vision_configured,
    }
