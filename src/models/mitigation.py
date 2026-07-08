"""Mitigation action and decision models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    EXPEDITE_SHIPMENT = "expedite_shipment"
    REROUTE_SHIPMENT = "reroute_shipment"
    SWITCH_TRANSPORT_MODE = "switch_transport_mode"
    NOTIFY_CUSTOMER = "notify_customer"
    NOTIFY_CARRIER = "notify_carrier"
    ACTIVATE_BACKUP_SUPPLIER = "activate_backup_supplier"
    ADJUST_PRODUCTION_SCHEDULE = "adjust_production_schedule"


class MitigationAction(BaseModel):
    action_id: str
    alert_id: str
    shipment_id: str
    action_type: ActionType
    description: str
    confidence: float = Field(ge=0.0, le=1.0, description="Agent confidence in this action")
    estimated_cost: float = Field(ge=0.0, description="Estimated cost of executing this action (USD)")
    estimated_delay_reduction_days: float = 0.0
    reasoning: str = Field(description="LLM reasoning chain for this recommendation")


class ActionOutcome(StrEnum):
    EXECUTED_AUTO = "executed_automatically"
    APPROVED_HUMAN = "approved_by_human"
    REJECTED_HUMAN = "rejected_by_human"
    PENDING_APPROVAL = "pending_approval"
    FAILED = "failed"


class ExecutedAction(BaseModel):
    action_id: str
    outcome: ActionOutcome
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    executed_by: str = Field(description="'agent' or human approver name")
    notes: str = ""


class ImpactAssessment(BaseModel):
    alert_id: str
    shipment_id: str
    affected_sales_orders: list[str] = []
    affected_plants: list[str] = []
    days_of_supply_remaining: float = 0.0
    stockout_risk: bool = False
    production_stoppage_risk: bool = False
    estimated_revenue_impact: float = 0.0
    summary: str = ""
