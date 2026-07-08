"""WorkflowBuilder graph definition for the supply chain agent pipeline.

    Ingestion → Risk Detection → Impact Analysis → Mitigation Decision
                                                         │
                                               confidence_router
                                              ╱                 ╲
                                  Autonomous Action      Human Approval
"""

from agent_framework import WorkflowBuilder

from src.executors.autonomous_action import AutonomousActionExecutor
from src.executors.human_approval import HumanApprovalExecutor
from src.executors.impact_analysis import ImpactAnalysisExecutor
from src.executors.ingestion import IngestionExecutor
from src.executors.mitigation import MitigationExecutor
from src.executors.risk_detection import RiskDetectionExecutor
from src.state import MitigationPlan

import logging

logger = logging.getLogger("supply_chain_agent.workflow")


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def has_auto_actions(message: MitigationPlan) -> bool:
    return len(message.auto_actions) > 0


def has_escalation_actions(message: MitigationPlan) -> bool:
    return len(message.escalation_actions) > 0


# ---------------------------------------------------------------------------
# Build the workflow
# ---------------------------------------------------------------------------

def build_workflow():
    """Construct the supply chain agent workflow."""

    ingestion = IngestionExecutor(id="ingestion")
    risk_detection = RiskDetectionExecutor(id="risk_detection")
    impact_analysis = ImpactAnalysisExecutor(id="impact_analysis")
    mitigation = MitigationExecutor(id="mitigation")
    autonomous_action = AutonomousActionExecutor(id="autonomous_action")
    human_approval = HumanApprovalExecutor(id="human_approval")

    workflow = (
        WorkflowBuilder(start_executor=ingestion, output_from=[autonomous_action, human_approval])
        .add_edge(ingestion, risk_detection)
        .add_edge(risk_detection, impact_analysis)
        .add_edge(impact_analysis, mitigation)
        .add_edge(mitigation, autonomous_action, condition=has_auto_actions)
        .add_edge(mitigation, human_approval, condition=has_escalation_actions)
        .build()
    )
    return workflow
