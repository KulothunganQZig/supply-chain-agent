"""Typed message schemas passed between executors in the workflow.

Each executor receives a message and emits a message via ctx.send_message().
The message type determines which handler is invoked on the receiving executor.
"""

from pydantic import BaseModel, Field

from src.models.erp import PurchaseOrder
from src.models.gps import GPSReading
from src.models.inventory import Inventory
from src.models.milestone import Milestone
from src.models.sales_order import SalesOrder
from src.models.shipment import Shipment


class IngestedData(BaseModel):
    """Output of IngestionExecutor → input to RiskDetectionExecutor."""

    shipments: list[Shipment] = []
    milestones: list[Milestone] = []
    gps_readings: list[GPSReading] = []
    email_summaries: list[dict] = Field(default_factory=list)
    purchase_orders: list[PurchaseOrder] = Field(default_factory=list)
    sales_orders: list[SalesOrder] = Field(default_factory=list)
    inventory: list[Inventory] = Field(default_factory=list)


class RiskAlert(BaseModel):
    """A single detected risk."""

    alert_id: str
    shipment_id: str
    po_id: str
    severity: str  # critical, high, medium, low
    risk_score: float = Field(ge=0.0, le=1.0)
    sources: list[str] = []  # milestone_delay, gps_anomaly, email_signal
    description: str = ""
    estimated_delay_days: float = 0.0


class RiskAssessment(BaseModel):
    """Output of RiskDetectionExecutor → input to ImpactAnalysisExecutor."""

    alerts: list[RiskAlert] = []
    ingested_data: IngestedData | None = None


class ImpactAssessment(BaseModel):
    """Impact for a single risk alert."""

    alert_id: str
    shipment_id: str
    affected_sales_orders: list[str] = []
    affected_plants: list[str] = []
    days_of_supply_remaining: float = 0.0
    stockout_risk: bool = False
    production_stoppage_risk: bool = False
    estimated_revenue_impact: float = 0.0
    summary: str = ""


class ImpactReport(BaseModel):
    """Output of ImpactAnalysisExecutor → input to MitigationExecutor."""

    assessments: list[ImpactAssessment] = []
    alerts: list[RiskAlert] = []


class MitigationAction(BaseModel):
    """A single proposed mitigation action."""

    action_id: str
    alert_id: str
    shipment_id: str
    action_type: str  # expedite, reroute, notify_customer, etc.
    description: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    estimated_cost: float = Field(ge=0.0)
    estimated_delay_reduction_days: float = 0.0
    reasoning: str = ""


class MitigationPlan(BaseModel):
    """Output of MitigationExecutor → routed to AutonomousAction or HumanApproval."""

    actions: list[MitigationAction] = []
    auto_actions: list[MitigationAction] = Field(default_factory=list)
    escalation_actions: list[MitigationAction] = Field(default_factory=list)


class ActionReport(BaseModel):
    """Output of AutonomousAction or HumanApproval → workflow output."""

    executed_actions: list[dict] = Field(default_factory=list)
    pending_approvals: list[MitigationAction] = Field(default_factory=list)
    summary: str = ""