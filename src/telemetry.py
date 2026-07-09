"""Azure Monitor / Application Insights wiring (OpenTelemetry).

Best-effort and opt-in: only activates when APPLICATIONINSIGHTS_CONNECTION_STRING
is set (i.e. in Azure). Locally it's a no-op — the heavy azure-monitor packages
are lazy-imported inside the function, so they aren't even required to be
installed for local dev/tests.

configure_azure_monitor() sets the global OpenTelemetry provider + exporters;
agent_framework then emits its LLM/executor spans to that provider (its
instrumentation is on by default, re-asserted here), and FastAPIInstrumentor
adds HTTP request traces. Result in App Insights: request traces, per-executor
and per-LLM-call spans, and app logs.
"""

import logging
import os

logger = logging.getLogger("supply_chain_agent.telemetry")


def setup_telemetry(app=None) -> None:
    """Enable App Insights telemetry if configured. Never raises."""
    if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        return
    try:
        from agent_framework.observability import enable_instrumentation
        from azure.monitor.opentelemetry import configure_azure_monitor

        # Reads APPLICATIONINSIGHTS_CONNECTION_STRING from the environment.
        configure_azure_monitor(logger_name="supply_chain_agent")
        enable_instrumentation()  # framework LLM/executor spans -> global provider

        if app is not None:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)

        logger.info("Application Insights telemetry enabled")
    except Exception:
        logger.warning("App Insights telemetry setup failed; continuing without it", exc_info=True)
