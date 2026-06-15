"""Application configuration for MaydaIQ.

No secrets or endpoints are hardcoded. Values come from environment variables or
an optional local .env file that is intentionally gitignored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # python-dotenv is included for local runs, but configuration should still
    # be importable if a deployment environment injects variables directly.
    pass


ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "MaydaIQ.png"
DATA_DIR = ROOT_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_pack"
REPORTS_PATH = DATA_DIR / "sample_reports.jsonl"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    # From your Microsoft Foundry project: AZURE_FOUNDRY_PROJECT_ENDPOINT
    azure_foundry_project_endpoint: str = os.getenv(
        "AZURE_FOUNDRY_PROJECT_ENDPOINT",
        os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
    )
    azure_foundry_model_deployment: str = os.getenv(
        "AZURE_FOUNDRY_MODEL_DEPLOYMENT",
        os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", ""),
    )
    azure_foundry_api_key: str = os.getenv("AZURE_FOUNDRY_API_KEY", os.getenv("AZURE_AI_PROJECT_API_KEY", ""))
    azure_foundry_auth_mode: str = os.getenv("AZURE_FOUNDRY_AUTH_MODE", "entra").strip().lower()

    # From your Foundry agent setup: AZURE_FOUNDRY_AGENT_ID
    azure_foundry_agent_id: str = os.getenv("AZURE_FOUNDRY_AGENT_ID", os.getenv("AZURE_AI_AGENT_ID", ""))
    azure_foundry_agent_name: str = os.getenv("AZURE_FOUNDRY_AGENT_NAME", "")

    # From your Foundry IQ knowledge configuration: FOUNDRY_IQ_KNOWLEDGE_BASE_ID
    foundry_iq_knowledge_base_id: str = os.getenv("FOUNDRY_IQ_KNOWLEDGE_BASE_ID", "")
    foundry_iq_connection_name: str = os.getenv("FOUNDRY_IQ_CONNECTION_NAME", "")

    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")

    azure_vision_endpoint: str = os.getenv("AZURE_VISION_ENDPOINT", "")
    azure_vision_key: str = os.getenv("AZURE_VISION_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_vision_deployment: str = os.getenv(
        "AZURE_OPENAI_VISION_DEPLOYMENT",
        os.getenv("AZURE_FOUNDRY_MODEL_DEPLOYMENT", ""),
    )
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    emergency_contact_text: str = os.getenv("PUBLIC_EMERGENCY_CONTACT", "local emergency services")

    demo_mode: bool = _as_bool(os.getenv("DEMO_MODE"), default=True)
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "en")

    @property
    def foundry_agent_configured(self) -> bool:
        return bool(self.azure_foundry_project_endpoint and (self.azure_foundry_agent_id or self.azure_foundry_agent_name))

    @property
    def foundry_iq_configured(self) -> bool:
        """Backward-compatible name for older code/docs.

        If your documents are already attached to the Foundry agent, a separate
        Foundry IQ knowledge-base id is not required for runtime calls.
        """

        return self.foundry_agent_configured

    @property
    def live_foundry_enabled(self) -> bool:
        return bool(not self.demo_mode and self.foundry_agent_configured)

    @property
    def service_principal_configured(self) -> bool:
        return bool(self.azure_tenant_id and self.azure_client_id and self.azure_client_secret)

    @property
    def foundry_api_key_configured(self) -> bool:
        return bool(self.azure_foundry_api_key)

    @property
    def foundry_uses_api_key(self) -> bool:
        return self.azure_foundry_auth_mode == "api_key" and self.foundry_api_key_configured

    @property
    def foundry_uses_entra(self) -> bool:
        return self.azure_foundry_auth_mode != "api_key"

    @property
    def azure_vision_configured(self) -> bool:
        return bool(self.azure_vision_endpoint and self.azure_vision_key)

    @property
    def azure_openai_vision_configured(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_vision_deployment
        )


def get_settings() -> Settings:
    return Settings()
