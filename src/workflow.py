"""WorkflowBuilder graph definition for the supply chain agent pipeline.

    Ingestion → Risk Detection → Impact Analysis → Mitigation Decision
                                                         │
                                               confidence_router
                                              ╱                 ╲
                                  Autonomous Action      Human Approval
"""

from typing_extensions import Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from src.executors.ingestion import IngestionExecutor
from src.state import (
    ActionReport,
    ImpactReport,
    IngestedData,
    MitigationPlan,
    RiskAssessment,
)

import logging

logger = logging.getLogger("supply_chain_agent.workflow")


# ---------------------------------------------------------------------------
# Stub executors (Phase 2: these will get real logic)
# ---------------------------------------------------------------------------

class RiskDetectionExecutor(Executor):
    @handler
    async def process(self, message: IngestedData, ctx: WorkflowContext[RiskAssessment]) -> None:
        logger.info(f"Risk detection: analyzing {len(message.shipments)} shipments...")
        # TODO Phase 2: implement real risk detection
        await ctx.send_message(RiskAssessment(alerts=[], ingested_data=message))


class ImpactAnalysisExecutor(Executor):
    @handler
    async def process(self, message: RiskAssessment, ctx: WorkflowContext[ImpactReport]) -> None:
        logger.info(f"Impact analysis: evaluating {len(message.alerts)} alerts...")
        # TODO Phase 2: implement real impact analysis
        await ctx.send_message(ImpactReport(assessments=[], alerts=message.alerts))


class MitigationExecutor(Executor):
    @handler
    async def process(self, message: ImpactReport, ctx: WorkflowContext[MitigationPlan]) -> None:
        logger.info(f"Mitigation: proposing actions for {len(message.assessments)} impacts...")
        # TODO Phase 2: implement real mitigation logic
        await ctx.send_message(MitigationPlan(actions=[], auto_actions=[], escalation_actions=[]))


class AutonomousActionExecutor(Executor):
    @handler
    async def process(self, message: MitigationPlan, ctx: WorkflowContext[Never, ActionReport]) -> None:
        logger.info(f"Autonomous action: executing {len(message.auto_actions)} actions...")
        await ctx.yield_output(ActionReport(
            executed_actions=[],
            summary=f"Executed {len(message.auto_actions)} autonomous actions.",
        ))


class HumanApprovalExecutor(Executor):
    @handler
    async def process(self, message: MitigationPlan, ctx: WorkflowContext[Never, ActionReport]) -> None:
        logger.info(f"Human approval: escalating {len(message.escalation_actions)} actions...")
        await ctx.yield_output(ActionReport(
            pending_approvals=message.escalation_actions,
            summary=f"Escalated {len(message.escalation_actions)} actions for review.",
        ))


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
        WorkflowBuilder(start_executor=ingestion)
        .add_edge(ingestion, risk_detection)
        .add_edge(risk_detection, impact_analysis)
        .add_edge(impact_analysis, mitigation)
        .add_edge(mitigation, autonomous_action, condition=has_auto_actions)
        .add_edge(mitigation, human_approval, condition=has_escalation_actions)
        .build()
    )
    return workflow