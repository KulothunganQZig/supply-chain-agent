"""Executor 3: Impact Analysis Agent.

For each risk alert, joins back to the purchase order (material, destination
plant), the plant's current inventory position, and any sales orders that
draw on the same material — then evaluates stockout risk, production
stoppage risk, and a rough revenue-at-risk estimate.
"""

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.config import settings
from src.models.erp import PurchaseOrder
from src.models.inventory import Inventory
from src.models.sales_order import SalesOrder
from src.state import ImpactAssessment, ImpactReport, RiskAssessment

logger = logging.getLogger("supply_chain_agent.impact_analysis")

# Rough $-per-unit proxy by sales-order priority, used only because the mock
# dataset carries no unit price. Swap for real PO/SO pricing in production.
_REVENUE_PER_UNIT_BY_PRIORITY = {
    "critical": 500.0,
    "high": 300.0,
    "medium": 150.0,
    "low": 50.0,
}


def _find_purchase_order(po_id: str, purchase_orders: list[PurchaseOrder]) -> PurchaseOrder | None:
    return next((po for po in purchase_orders if po.po_id == po_id), None)


def _find_inventory(plant: str, material: str, inventory: list[Inventory]) -> Inventory | None:
    return next((inv for inv in inventory if inv.plant == plant and inv.material == material), None)


def _find_sales_orders(material: str, sales_orders: list[SalesOrder]) -> list[SalesOrder]:
    return [so for so in sales_orders if so.material == material]


def _revenue_at_risk(affected_sales_orders: list[SalesOrder]) -> float:
    return sum(
        so.quantity * _REVENUE_PER_UNIT_BY_PRIORITY.get(so.priority.value, 0.0)
        for so in affected_sales_orders
    )


class ImpactAnalysisExecutor(Executor):
    """Evaluates stockout risk, production stoppage risk, and revenue impact per alert."""

    @handler
    async def process(self, message: RiskAssessment, ctx: WorkflowContext[ImpactReport]) -> None:
        logger.info(f"Impact analysis: evaluating {len(message.alerts)} alerts...")

        data = message.ingested_data
        purchase_orders = data.purchase_orders if data else []
        sales_orders = data.sales_orders if data else []
        inventory = data.inventory if data else []

        assessments: list[ImpactAssessment] = []
        for alert in message.alerts:
            po = _find_purchase_order(alert.po_id, purchase_orders)
            plant = po.destination_plant if po else ""
            material = po.material if po else ""

            inv = _find_inventory(plant, material, inventory) if po else None
            affected_sales_orders = _find_sales_orders(material, sales_orders) if po else []

            days_of_supply = inv.days_of_supply if inv else 0.0
            stockout_risk = bool(
                inv and (inv.below_safety_stock or days_of_supply <= settings.days_of_supply_critical)
            )
            production_stoppage_risk = stockout_risk and alert.estimated_delay_days >= days_of_supply
            revenue_impact = _revenue_at_risk(affected_sales_orders)

            summary_parts = [f"{alert.shipment_id} risks {material or 'unknown material'}"]
            if inv:
                summary_parts.append(f"at {plant} ({days_of_supply:.1f}d supply remaining)")
            if stockout_risk:
                summary_parts.append("— STOCKOUT RISK")
            if production_stoppage_risk:
                summary_parts.append("— PRODUCTION STOPPAGE LIKELY")
            if affected_sales_orders:
                so_ids = ", ".join(so.so_id for so in affected_sales_orders)
                summary_parts.append(f"; affects sales orders {so_ids}")

            assessments.append(
                ImpactAssessment(
                    alert_id=alert.alert_id,
                    shipment_id=alert.shipment_id,
                    affected_sales_orders=[so.so_id for so in affected_sales_orders],
                    affected_plants=[plant] if plant else [],
                    days_of_supply_remaining=round(days_of_supply, 1),
                    stockout_risk=stockout_risk,
                    production_stoppage_risk=production_stoppage_risk,
                    estimated_revenue_impact=round(revenue_impact, 2),
                    summary=" ".join(summary_parts),
                )
            )

        logger.info(f"Impact analysis complete: {len(assessments)} assessment(s)")
        for a in assessments:
            logger.info(
                f"  {a.alert_id} | stockout={a.stockout_risk} | "
                f"stoppage={a.production_stoppage_risk} | revenue=${a.estimated_revenue_impact:,.0f}"
            )

        await ctx.send_message(ImpactReport(assessments=assessments, alerts=message.alerts))
