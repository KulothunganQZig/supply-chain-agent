"""Executor 5: Autonomous Action Agent.

Executes every mitigation action the Mitigation Decision Agent cleared for
auto-execution (high confidence, cost under the escalation threshold).
Execution is simulated — recorded as a structured outcome — since this
prototype has no real carrier/CRM integration to call.
"""

import logging
from typing import Never

from agent_framework import Executor, WorkflowContext, handler

from src.state import ActionReport, MitigationPlan

logger = logging.getLogger("supply_chain_agent.autonomous_action")


class AutonomousActionExecutor(Executor):
    """Auto-executes cleared mitigation actions and reports the outcomes."""

    @handler
    async def process(self, message: MitigationPlan, ctx: WorkflowContext[Never, ActionReport]) -> None:
        logger.info(f"Autonomous action: executing {len(message.auto_actions)} action(s)...")

        executed_actions = []
        for action in message.auto_actions:
            logger.info(f"  EXECUTED {action.action_id} | {action.action_type} | {action.description}")
            executed_actions.append(
                {
                    "action_id": action.action_id,
                    "shipment_id": action.shipment_id,
                    "action_type": action.action_type,
                    "outcome": "executed_automatically",
                    "executed_by": "agent",
                    "notes": action.description,
                }
            )

        await ctx.yield_output(
            ActionReport(
                executed_actions=executed_actions,
                summary=f"Executed {len(executed_actions)} autonomous action(s).",
            )
        )
