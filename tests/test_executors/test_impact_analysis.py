"""Tests for ImpactAnalysisExecutor against the curated mock dataset."""

import pytest

from mock_data.generate import (
    CARRIER_EMAILS,
    GPS_READINGS,
    INVENTORY,
    MILESTONES,
    PURCHASE_ORDERS,
    SALES_ORDERS,
    SHIPMENTS,
)
from src.executors.impact_analysis import ImpactAnalysisExecutor
from src.executors.risk_detection import RiskDetectionExecutor
from src.state import IngestedData, ImpactReport, RiskAssessment


class _CapturingContext:
    """Minimal WorkflowContext stand-in that just records the sent message."""

    def __init__(self):
        self.sent = None

    async def send_message(self, message, target_id=None):
        self.sent = message


def _build_ingested_data() -> IngestedData:
    email_summaries = [
        {
            "email_id": e.email_id,
            "shipment_id": e.shipment_id,
            "subject": e.subject,
            "delay_days_mentioned": e.delay_days_mentioned,
            "reason": e.reason,
        }
        for e in CARRIER_EMAILS
    ]
    return IngestedData(
        shipments=SHIPMENTS,
        milestones=MILESTONES,
        gps_readings=GPS_READINGS,
        email_summaries=email_summaries,
        purchase_orders=PURCHASE_ORDERS,
        sales_orders=SALES_ORDERS,
        inventory=INVENTORY,
    )


async def _run_pipeline() -> ImpactReport:
    risk_ctx = _CapturingContext()
    await RiskDetectionExecutor(id="risk_detection").process(_build_ingested_data(), risk_ctx)
    assert isinstance(risk_ctx.sent, RiskAssessment)

    impact_ctx = _CapturingContext()
    await ImpactAnalysisExecutor(id="impact_analysis").process(risk_ctx.sent, impact_ctx)
    return impact_ctx.sent


@pytest.mark.asyncio
async def test_low_stock_materials_flagged_as_stockout_risk():
    report = await _run_pipeline()

    by_shipment = {a.shipment_id: a for a in report.assessments}
    # SH-3001 (Steel Coils, 1.9d), SH-3003 (Battery Cells, 3.0d), SH-3005 (Carbon Fiber, 2.4d)
    # are all below or at the safety-stock / critical-days threshold.
    assert by_shipment["SH-3001"].stockout_risk is True
    assert by_shipment["SH-3003"].stockout_risk is True
    assert by_shipment["SH-3005"].stockout_risk is True


@pytest.mark.asyncio
async def test_affected_sales_orders_joined_by_material():
    report = await _run_pipeline()
    by_shipment = {a.shipment_id: a for a in report.assessments}

    # Steel Coils feeds both SO-2001 and SO-2006.
    assert set(by_shipment["SH-3001"].affected_sales_orders) == {"SO-2001", "SO-2006"}
    assert set(by_shipment["SH-3003"].affected_sales_orders) == {"SO-2003"}
    assert set(by_shipment["SH-3005"].affected_sales_orders) == {"SO-2005"}


@pytest.mark.asyncio
async def test_affected_plants_match_po_destination():
    report = await _run_pipeline()
    by_shipment = {a.shipment_id: a for a in report.assessments}

    assert by_shipment["SH-3001"].affected_plants == ["Plant-Detroit"]
    assert by_shipment["SH-3003"].affected_plants == ["Plant-Houston"]
    assert by_shipment["SH-3005"].affected_plants == ["Plant-Munich"]


@pytest.mark.asyncio
async def test_revenue_impact_is_positive_for_every_alert():
    report = await _run_pipeline()
    assert report.assessments
    for assessment in report.assessments:
        assert assessment.estimated_revenue_impact > 0
