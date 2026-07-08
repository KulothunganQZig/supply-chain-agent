"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the supply chain agent system."""

    # Azure AI Foundry
    azure_ai_project_endpoint: str = ""
    model_deployment_name: str = "gpt-4.1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./supply_chain.db"

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
