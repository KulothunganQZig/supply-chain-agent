"""Tests for MitigationExecutor, AutonomousActionExecutor, HumanApprovalExecutor.

No AZURE_AI_PROJECT_ENDPOINT is configured in the test environment, so these
exercise the deterministic rule-based fallback path exclusively — the same
path the local pipeline actually runs today.
"""

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
from src.executors.autonomous_action import AutonomousActionExecutor
from src.executors.human_approval import HumanApprovalExecutor
from src.executors.impact_analysis import ImpactAnalysisExecutor
from src.executors.mitigation import MitigationExecutor
from src.executors.risk_detection import RiskDetectionExecutor
from src.state import ActionReport, IngestedData, MitigationPlan


class _CapturingContext:
    def __init__(self):
        self.sent = None

    async def send_message(self, message, target_id=None):
        self.sent = message

    async def yield_output(self, message):
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


async def _run_to_mitigation_plan() -> MitigationPlan:
    risk_ctx = _CapturingContext()
    await RiskDetectionExecutor(id="risk_detection").process(_build_ingested_data(), risk_ctx)

    impact_ctx = _CapturingContext()
    await ImpactAnalysisExecutor(id="impact_analysis").process(risk_ctx.sent, impact_ctx)

    mitigation_ctx = _CapturingContext()
    await MitigationExecutor(id="mitigation").process(impact_ctx.sent, mitigation_ctx)
    return mitigation_ctx.sent


@pytest.mark.asyncio
async def test_every_assessment_gets_a_primary_action():
    plan = await _run_to_mitigation_plan()
    primary_action_ids = {a.action_id for a in plan.actions if a.action_id.endswith("-PRIMARY")}
    assert primary_action_ids == {"ACT-ALERT-SH-3001-PRIMARY", "ACT-ALERT-SH-3005-PRIMARY", "ACT-ALERT-SH-3003-PRIMARY"}


@pytest.mark.asyncio
async def test_stoppage_risk_shipments_get_switch_transport_mode():
    plan = await _run_to_mitigation_plan()
    by_id = {a.action_id: a for a in plan.actions}
    assert by_id["ACT-ALERT-SH-3001-PRIMARY"].action_type == "switch_transport_mode"
    assert by_id["ACT-ALERT-SH-3005-PRIMARY"].action_type == "switch_transport_mode"


@pytest.mark.asyncio
async def test_stockout_only_shipment_gets_expedite():
    plan = await _run_to_mitigation_plan()
    by_id = {a.action_id: a for a in plan.actions}
    assert by_id["ACT-ALERT-SH-3003-PRIMARY"].action_type == "expedite_shipment"


@pytest.mark.asyncio
async def test_every_alert_with_affected_sales_orders_gets_a_notify_companion():
    plan = await _run_to_mitigation_plan()
    notify_ids = {a.action_id for a in plan.actions if a.action_id.endswith("-NOTIFY")}
    assert notify_ids == {
        "ACT-ALERT-SH-3001-NOTIFY",
        "ACT-ALERT-SH-3005-NOTIFY",
        "ACT-ALERT-SH-3003-NOTIFY",
    }
    for action_id in notify_ids:
        action = next(a for a in plan.actions if a.action_id == action_id)
        assert action.action_type == "notify_customer"
        assert action.estimated_cost == 0.0


@pytest.mark.asyncio
async def test_high_cost_low_confidence_actions_are_escalated_not_auto_executed():
    plan = await _run_to_mitigation_plan()
    escalated_ids = {a.action_id for a in plan.escalation_actions}
    auto_ids = {a.action_id for a in plan.auto_actions}

    # The switch_transport_mode actions are deliberately low-confidence (0.65 < 0.85)
    assert "ACT-ALERT-SH-3001-PRIMARY" in escalated_ids
    assert "ACT-ALERT-SH-3005-PRIMARY" in escalated_ids
    # The free notify_customer companions are high-confidence, zero-cost -> auto
    assert "ACT-ALERT-SH-3001-NOTIFY" in auto_ids
    assert "ACT-ALERT-SH-3005-NOTIFY" in auto_ids
    assert "ACT-ALERT-SH-3003-NOTIFY" in auto_ids

    assert not (escalated_ids & auto_ids)
    assert escalated_ids | auto_ids == {a.action_id for a in plan.actions}


@pytest.mark.asyncio
async def test_autonomous_action_executor_reports_all_auto_actions_executed():
    plan = await _run_to_mitigation_plan()

    ctx = _CapturingContext()
    await AutonomousActionExecutor(id="autonomous_action").process(plan, ctx)

    report: ActionReport = ctx.sent
    assert len(report.executed_actions) == len(plan.auto_actions)
    executed_ids = {e["action_id"] for e in report.executed_actions}
    assert executed_ids == {a.action_id for a in plan.auto_actions}


@pytest.mark.asyncio
async def test_human_approval_executor_reports_all_escalations_pending():
    plan = await _run_to_mitigation_plan()

    ctx = _CapturingContext()
    await HumanApprovalExecutor(id="human_approval").process(plan, ctx)

    report: ActionReport = ctx.sent
    assert {a.action_id for a in report.pending_approvals} == {a.action_id for a in plan.escalation_actions}
