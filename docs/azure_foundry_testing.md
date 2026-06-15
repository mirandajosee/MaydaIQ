# Azure Foundry Live Testing

MaydaIQ now supports two runtime paths:

- **Local demo:** `DEMO_MODE=true`, deterministic retrieval from `data/knowledge_pack`.
- **Live Foundry agent:** `DEMO_MODE=false`, calls your existing Microsoft Foundry agent.

## Minimum Variables For Your Existing Agent

If your documents are already attached to the Foundry agent, the live path only needs:

```env
DEMO_MODE=false
AZURE_FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_FOUNDRY_AUTH_MODE=entra
AZURE_FOUNDRY_TOKEN_SCOPE=https://ai.azure.com/.default
AZURE_FOUNDRY_ALLOW_INTERACTIVE_LOGIN=false
AZURE_FOUNDRY_AGENT_ID=<your-agent-id>
AZURE_FOUNDRY_AGENT_VERSION=9
AZURE_FOUNDRY_MODEL_DEPLOYMENT=<your-model-deployment>
```

Authentication can use either:

- `az login` through `DefaultAzureCredential`, recommended for local testing. MaydaIQ does not launch an interactive browser login from the Streamlit request path.
- `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` for service-principal auth.
- `AZURE_FOUNDRY_ALLOW_INTERACTIVE_LOGIN=true` for local-only troubleshooting when Azure CLI is not installed or not visible to the Streamlit process.

The token audience must match the Foundry project endpoint. Current Foundry Responses agent-reference calls expect `https://ai.azure.com/.default`; using the older Azure OpenAI/Cognitive Services scope can produce a 401 even after a successful `az login`.

The Foundry project `/openai/v1/` path must not receive an `api-version` query parameter. Keep `AZURE_OPENAI_API_VERSION` only for separate Azure OpenAI/Vision flows, not for the Foundry agent-reference request.

Do not use `AZURE_FOUNDRY_AUTH_MODE=api_key` for agents whose tools or knowledge connections are configured with OBO authentication. Microsoft Foundry returns a 400 error for that combination.

## Optional Variables

`AZURE_FOUNDRY_MODEL_DEPLOYMENT` is required by the Responses API even when the agent is referenced with `agent_reference`.

`FOUNDRY_IQ_KNOWLEDGE_BASE_ID` and `FOUNDRY_IQ_CONNECTION_NAME` are not required when retrieval documents are already attached to the agent. Keep them empty unless you later build a direct Foundry IQ retrieval/index adapter.

Azure Vision variables are optional. Without them, MaydaIQ uses deterministic privacy-safe image fallback.

## Install Live SDKs

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The requirements include:

- `azure-ai-projects`
- `azure-identity`

## Run The App

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

The sidebar shows whether MaydaIQ is in `LOCAL_DEMO`, `FOUNDRY_LIVE_READY`, or fallback mode.

## Public Demo Users

End users do not need a Microsoft account. The Streamlit app runs server-side and uses the API key or server identity from `.env`. If live Foundry access is unavailable, MaydaIQ falls back to local demo retrieval instead of asking users to authenticate.
