"""Tests for RiskDetectionExecutor against the curated mock dataset."""

import pytest

from mock_data.generate import CARRIER_EMAILS, GPS_READINGS, MILESTONES, SHIPMENTS
from src.executors.risk_detection import RiskDetectionExecutor
from src.state import IngestedData, RiskAssessment


class _CapturingContext:
    """Minimal WorkflowContext stand-in that just records the sent message."""

    def __init__(self):
        self.sent: RiskAssessment | None = None

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
    )


@pytest.mark.asyncio
async def test_flags_shipments_with_known_anomalies():
    executor = RiskDetectionExecutor(id="risk_detection")
    ctx = _CapturingContext()

    await executor.process(_build_ingested_data(), ctx)

    assert ctx.sent is not None
    alerted_ids = {alert.shipment_id for alert in ctx.sent.alerts}
    assert alerted_ids == {"SH-3001", "SH-3003", "SH-3005"}


@pytest.mark.asyncio
async def test_healthy_shipments_produce_no_alert():
    executor = RiskDetectionExecutor(id="risk_detection")
    ctx = _CapturingContext()

    await executor.process(_build_ingested_data(), ctx)

    alerted_ids = {alert.shipment_id for alert in ctx.sent.alerts}
    assert "SH-3002" not in alerted_ids
    assert "SH-3004" not in alerted_ids


@pytest.mark.asyncio
async def test_multi_signal_shipment_scores_higher_than_single_signal():
    executor = RiskDetectionExecutor(id="risk_detection")
    ctx = _CapturingContext()

    await executor.process(_build_ingested_data(), ctx)

    by_id = {alert.shipment_id: alert for alert in ctx.sent.alerts}
    # SH-3001 fires milestone + email + eta signals; SH-3003 fires GPS only.
    assert by_id["SH-3001"].risk_score > by_id["SH-3003"].risk_score
    assert set(by_id["SH-3001"].sources) >= {"milestone_delay", "email_signal", "eta_deviation"}
    assert by_id["SH-3003"].sources == ["gps_anomaly"]


@pytest.mark.asyncio
async def test_alerts_sorted_by_risk_score_descending():
    executor = RiskDetectionExecutor(id="risk_detection")
    ctx = _CapturingContext()

    await executor.process(_build_ingested_data(), ctx)

    scores = [alert.risk_score for alert in ctx.sent.alerts]
    assert scores == sorted(scores, reverse=True)
