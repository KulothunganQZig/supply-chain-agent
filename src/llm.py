"""Shared Azure OpenAI chat client for the LLM-backed executor hooks.

`mitigation.py` (action reasoning) and `email_parsing.py` (delay extraction)
both want a single-turn completion from Azure OpenAI when it's configured, and
a graceful fall-back to their deterministic path otherwise. This centralizes
that so the endpoint/auth wiring lives in exactly one place instead of being
hand-rolled — and mis-configured — in each.

Keyless by default: authenticates with DefaultAzureCredential (AAD token), so
production uses a Managed Identity and local dev uses your `az login` session —
no API key in the code path. `complete()` returns None on any failure (not
configured, no credential, network, auth, content filter), which every caller
treats as "use the deterministic fallback".
"""

import logging

from src.config import settings

logger = logging.getLogger("supply_chain_agent.llm")

_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


def azure_openai_configured() -> bool:
    """True when an Azure OpenAI endpoint is set, so the LLM path should be attempted."""
    return bool(settings.azure_openai_endpoint)


async def complete(prompt: str) -> str | None:
    """Run a single user prompt through Azure OpenAI. Returns None on any failure.

    None means "fall back" — callers must handle it. Never raises.
    """
    if not azure_openai_configured():
        return None
    try:
        from agent_framework import Message
        from agent_framework_openai import OpenAIChatClient
        from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
        from openai import AsyncAzureOpenAI

        async with DefaultAzureCredential() as credential:
            token_provider = get_bearer_token_provider(credential, _COGNITIVE_SERVICES_SCOPE)
            azure_client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_deployment=settings.model_deployment_name,
                api_version=settings.azure_openai_api_version,
                azure_ad_token_provider=token_provider,
            )
            chat_client = OpenAIChatClient(async_client=azure_client)
            response = await chat_client.get_response([Message("user", [prompt])])
            return response.text.strip() or None
    except Exception:
        logger.warning("Azure OpenAI call failed; caller will use deterministic fallback", exc_info=True)
        return None
