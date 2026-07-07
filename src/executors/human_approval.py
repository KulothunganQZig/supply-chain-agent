"""Executor 6: Human-in-the-Loop Agent.

Escalates high-cost or low-confidence decisions for human approval.
Uses workflow checkpointing to pause execution until approval is received.
"""

import logging

from typing_extensions import Never

from agent_framework import Executor, WorkflowContext, handler

from src.state import ActionReport, MitigationPlan

logger = logging.getLogger("supply_chain_agent.human_approval")


class HumanApprovalExecutor(Executor):
    """Escalates actions requiring human review.

    In production, this executor:
    1. Checkpoints the workflow state
    2. Sends an approval request to Microsoft Teams (via M365 Agents SDK)
    3. Pauses until the human approves or rejects
    4. Resumes execution based on the decision

    For local development, it logs the escalation and marks as pending.
    """

    @handler
    async def process(self, message: MitigationPlan, ctx: WorkflowContext[Never, ActionReport]) -> None:
        """Escalate actions that need human approval."""
        logger.info(
            f"Human approval agent escalating {len(message.escalation_actions)} actions..."
        )

        # TODO Phase 2: Implement human-in-the-loop
        # For each escalation_action:
        # 1. Build a rich approval card with:
        #    - Shipment details, risk severity, impact summary
        #    - Proposed action, estimated cost, confidence score
        #    - Approve / Reject buttons
        # 2. In production: use workflow checkpoint + Teams notification
        # 3. In local dev: log and mark as pending

        # TODO Phase 3: Integrate with Agent Framework checkpointing
        # workflow = WorkflowBuilder(...).with_checkpointing(storage).build()
        # The framework handles pause/resume across process restarts.

        logger.info(f"Escalation complete: {len(message.escalation_actions)} actions pending")

        await ctx.yield_output(ActionReport(
            pending_approvals=message.escalation_actions,
            summary=f"Escalated {len(message.escalation_actions)} actions for human review.",
        ))
