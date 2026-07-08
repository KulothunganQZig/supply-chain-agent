"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the supply chain agent system."""

    # Azure OpenAI (LLM reasoning + email parsing).
    # This is the Azure OpenAI *resource* endpoint — https://<resource>.openai.azure.com/ —
    # NOT the Foundry project endpoint. Empty = LLM hooks use their deterministic fallback.
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2025-04-01-preview"
    model_deployment_name: str = "gpt-5-mini"

    # Azure AI Foundry project endpoint — https://<account>.services.ai.azure.com/api/projects/<project>.
    # Reserved for future Foundry Agent Service tool-use (cross-shipment intelligence); NOT used by
    # the current narrow-completion LLM hooks, which go through azure_openai_endpoint above.
    azure_ai_project_endpoint: str = ""

    # Client ID of the user-assigned Managed Identity. Set on the Container App so
    # DefaultAzureCredential (OpenAI) and the SQL ODBC driver (ActiveDirectoryMsi)
    # both bind to the right identity. Empty locally.
    azure_client_id: str = ""

    # Database. Local dev = SQLite (default below). When azure_sql_server is set,
    # db.py builds a keyless mssql+aioodbc URL (ActiveDirectoryMsi) instead — see db.py.
    database_url: str = "sqlite+aiosqlite:///./supply_chain.db"
    azure_sql_server: str = ""    # e.g. sql-sc-xxxx.database.windows.net
    azure_sql_database: str = ""  # e.g. scdb

    # Azure AI Search (empty = skip email search in local dev)
    azure_search_endpoint: str = ""
    azure_search_index_name: str = "carrier-emails"

    # Azure Event Hubs (empty = use file-based GPS mock)
    eventhub_connection_string: str = ""
    eventhub_name: str = "gps-tracking"

    # Agent decision thresholds
    confidence_threshold: float = 0.85
    cost_escalation_threshold: float = 50_000.0
    days_of_supply_critical: int = 3

    # Risk scoring weights
    milestone_delay_weight: float = 0.35
    gps_anomaly_weight: float = 0.25
    email_signal_weight: float = 0.20
    eta_deviation_weight: float = 0.20

    # Risk severity bucket boundaries (risk_score >= threshold)
    risk_severity_critical: float = 0.75
    risk_severity_high: float = 0.50
    risk_severity_medium: float = 0.25

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
