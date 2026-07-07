"""Typed message schemas passed between executors in the workflow.

Each executor receives and emits these messages via the WorkflowBuilder edge system.
The message type determines which handler is invoked on the receiving executor.
"""

from pydantic import BaseModel, Field

from src.models.mitigation import ExecutedAction, ImpactAssessment, MitigationAction
from src.models.risk import RiskAlert
from src.models.shipment import GPSReading, Milestone, Shipment


class IngestedData(BaseModel):
    """Output of IngestionExecutor → input to RiskDetectionExecutor."""

    shipments: list[Shipment] = []
    milestones: list[Milestone] = []
    gps_readings: list[GPSReading] = []
    email_summaries: list[dict] = Field(default_factory=list, description="Parsed email signals")


class RiskAssessment(BaseModel):
    """Output of RiskDetectionExecutor → input to ImpactAnalysisExecutor."""

    alerts: list[RiskAlert] = []
    ingested_data: IngestedData | None = None


class ImpactReport(BaseModel):
    """Output of ImpactAnalysisExecutor → input to MitigationExecutor."""

    assessments: list[ImpactAssessment] = []
    alerts: list[RiskAlert] = []


class MitigationPlan(BaseModel):
    """Output of MitigationExecutor → routed to AutonomousAction or HumanApproval."""

    actions: list[MitigationAction] = []
    auto_actions: list[MitigationAction] = Field(
        default_factory=list, description="Actions with confidence >= threshold"
    )
    escalation_actions: list[MitigationAction] = Field(
        default_factory=list, description="Actions requiring human approval"
    )


class ActionReport(BaseModel):
    """Output of AutonomousActionExecutor or HumanApprovalExecutor → final output."""

    executed_actions: list[ExecutedAction] = []
    pending_approvals: list[MitigationAction] = []
    summary: str = ""
