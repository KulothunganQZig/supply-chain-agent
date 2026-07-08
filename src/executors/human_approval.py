"""Executor 6: Human-in-the-Loop Agent.

Escalates mitigation actions that fell below the confidence threshold or
exceeded the cost-escalation threshold — the challenge's "escalate when cost
impact is high" rule, applied via src/config.py's decision thresholds.
"""

import logging
from typing import Never

from agent_framework import Executor, WorkflowContext, handler

from src.state import ActionReport, MitigationPlan

logger = logging.getLogger("supply_chain_agent.human_approval")


class HumanApprovalExecutor(Executor):
    """Surfaces escalated mitigation actions for human review."""

    @handler
    async def process(self, message: MitigationPlan, ctx: WorkflowContext[Never, ActionReport]) -> None:
        logger.info(f"Human approval: escalating {len(message.escalation_actions)} action(s)...")

        for action in message.escalation_actions:
            logger.info(
                f"  PENDING {action.action_id} | {action.action_type} | "
                f"confidence={action.confidence:.2f} | cost=${action.estimated_cost:,.0f}"
            )

        await ctx.yield_output(
            ActionReport(
                pending_approvals=message.escalation_actions,
                summary=f"Escalated {len(message.escalation_actions)} action(s) for human review.",
            )
        )
