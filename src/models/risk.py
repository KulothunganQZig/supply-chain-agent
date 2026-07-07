"""Risk assessment and alert models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskSource(str, Enum):
    MILESTONE_DELAY = "milestone_delay"
    GPS_ANOMALY = "gps_anomaly"
    EMAIL_SIGNAL = "email_signal"
    ETA_DEVIATION = "eta_deviation"


class RiskAlert(BaseModel):
    alert_id: str
    shipment_id: str
    po_id: str
    severity: RiskSeverity
    risk_score: float = Field(ge=0.0, le=1.0)
    sources: list[RiskSource]
    description: str
    estimated_delay_days: float = 0.0
    detected_at: datetime = Field(default_factory=datetime.utcnow)
