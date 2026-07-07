"""WorkflowBuilder graph definition for the supply chain agent pipeline.

This module defines the 6-executor directed graph:

    Ingestion → Risk Detection → Impact Analysis → Mitigation Decision
                                                         │
                                               confidence_router
                                              ╱                 ╲
                                  Autonomous Action      Human Approval

The conditional edge (confidence_router) splits based on the confidence
threshold defined in config.py.

API reference:
    https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.workflowbuilder
"""

from agent_framework import WorkflowBuilder

from src.executors.autonomous_action import AutonomousActionExecutor
from src.executors.human_approval import HumanApprovalExecutor
from src.executors.impact_analysis import ImpactAnalysisExecutor
from src.executors.ingestion import IngestionExecutor
from src.executors.mitigation import MitigationExecutor
from src.executors.risk_detection import RiskDetectionExecutor
from src.state import MitigationPlan


# ---------------------------------------------------------------------------
# Conditional edge functions
# These receive the message emitted by the MitigationExecutor and return True
# to activate the downstream branch.
# ---------------------------------------------------------------------------

def has_auto_actions(message: MitigationPlan) -> bool:
    """Route to AutonomousActionExecutor if there are high-confidence actions."""
    return len(message.auto_actions) > 0


def has_escalation_actions(message: MitigationPlan) -> bool:
    """Route to HumanApprovalExecutor if there are actions needing approval."""
    return len(message.escalation_actions) > 0


# ---------------------------------------------------------------------------
# Executor instances (created once, reused across workflow runs)
# ---------------------------------------------------------------------------

ingestion = IngestionExecutor(id="ingestion")
risk_detection = RiskDetectionExecutor(id="risk_detection")
impact_analysis = ImpactAnalysisExecutor(id="impact_analysis")
mitigation = MitigationExecutor(id="mitigation")
autonomous_action = AutonomousActionExecutor(id="autonomous_action")
human_approval = HumanApprovalExecutor(id="human_approval")


def build_workflow():
    """Construct and return the supply chain agent workflow.

    Uses the WorkflowBuilder fluent API:
        WorkflowBuilder(start_executor=...)
            .add_edge(source, target, condition=...)
            .build()

    Returns:
        A compiled Workflow ready for .run() or .run_stream().
    """
    workflow = (
        WorkflowBuilder(start_executor=ingestion)
        # Sequential: ingestion → risk → impact → mitigation
        .add_edge(ingestion, risk_detection)
        .add_edge(risk_detection, impact_analysis)
        .add_edge(impact_analysis, mitigation)
        # Fan-out: mitigation → autonomous (high confidence) AND/OR human (low confidence)
        .add_edge(mitigation, autonomous_action, condition=has_auto_actions)
        .add_edge(mitigation, human_approval, condition=has_escalation_actions)
        .build()
    )
    return workflow
