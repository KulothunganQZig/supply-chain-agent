"""Executor 3: Impact Analysis Agent.

Evaluates the operational impact of detected risks:
- Stockout risk (days of supply vs estimated delay)
- Production stoppage risk (critical materials)
- Revenue impact (affected sales orders)
"""

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.state import ImpactReport, RiskAssessment

logger = logging.getLogger("supply_chain_agent.impact_analysis")


class ImpactAnalysisExecutor(Executor):
    """Calculates business impact for each risk alert.

    Tools (Phase 2):
        - calc_days_of_supply: Query inventory and compute remaining coverage
        - check_safety_stock: Determine if stock will fall below safety level
        - find_affected_orders: Map PO delays to downstream sales orders
    """

    @handler
    async def process(self, message: RiskAssessment, ctx: WorkflowContext[ImpactReport]) -> None:
        """Evaluate business impact for each risk alert."""
        logger.info(f"Impact analysis agent evaluating {len(message.alerts)} alerts...")

        assessments = []

        # TODO Phase 2: Implement impact analysis
        # For each alert:
        # 1. Look up inventory for the affected material at the destination plant
        # 2. Calculate days_of_supply = current_stock / daily_consumption
        # 3. Compare days_of_supply against estimated_delay_days
        # 4. If days_of_supply < delay → stockout_risk = True
        # 5. If material is critical priority → production_stoppage_risk = True
        # 6. Find affected SOs and estimate revenue impact
        # 7. Use LLM to generate a human-readable impact summary

        logger.info(f"Impact analysis complete: {len(assessments)} assessments")

        await ctx.send_message(ImpactReport(assessments=assessments, alerts=message.alerts))
