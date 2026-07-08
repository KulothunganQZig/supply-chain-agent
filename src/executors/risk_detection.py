"""Executor 2: Shipment Risk Detection Agent.

Scores every active shipment against four independent signal sources —
milestone delays, GPS stalls, carrier-email delay notices, and shipment-level
ETA status — and emits a RiskAlert for each shipment where at least one
signal fires. Weights and severity bucket boundaries are config-driven
(see src/config.py).
"""

import logging
from collections import defaultdict
from datetime import datetime

from agent_framework import Executor, WorkflowContext, handler

from src.config import settings
from src.models.gps import GPSReading
from src.models.milestone import Milestone, MilestoneStatus
from src.models.shipment import Shipment, ShipmentStatus
from src.state import IngestedData, RiskAlert, RiskAssessment

logger = logging.getLogger("supply_chain_agent.risk_detection")

# Magnitude beyond which a signal's sub-score saturates at 1.0.
_MILESTONE_DELAY_SATURATION_DAYS = 5.0
_GPS_STALL_SATURATION_HOURS = 48.0
_EMAIL_DELAY_SATURATION_DAYS = 7.0


def _current_time() -> datetime:
    """Analysis reference time ('now').

    Production uses real wall-clock — a live risk engine must measure how long a
    milestone/GPS stall has actually persisted. This is a seam so tests can pin a
    fixed reference (the mock dataset uses fixed timestamps; see tests/conftest.py).
    """
    return datetime.utcnow()


def _milestone_delay_signal(milestones: list[Milestone], now: datetime) -> tuple[float, float]:
    """Sub-score + estimated delay (days) from milestones stuck in DELAYED status."""
    delayed = [m for m in milestones if m.status == MilestoneStatus.DELAYED]
    if not delayed:
        return 0.0, 0.0
    delay_days = max(0.0, max((now - m.planned_time).total_seconds() / 86400 for m in delayed))
    return min(1.0, delay_days / _MILESTONE_DELAY_SATURATION_DAYS), delay_days


def _gps_anomaly_signal(gps_readings: list[GPSReading], now: datetime) -> tuple[float, float]:
    """Sub-score + estimated delay (days) from an ongoing GPS stall (speed=0)."""
    stalled = sorted(
        (g for g in gps_readings if g.delay_indicator or g.speed_kmh == 0),
        key=lambda g: g.timestamp,
    )
    if not stalled:
        return 0.0, 0.0
    stall_hours = max(0.0, (now - stalled[0].timestamp).total_seconds() / 3600)
    return min(1.0, stall_hours / _GPS_STALL_SATURATION_HOURS), stall_hours / 24


def _email_signal(emails: list[dict]) -> tuple[float, float]:
    """Sub-score + estimated delay (days) from carrier delay notices."""
    if not emails:
        return 0.0, 0.0
    delay_days = max(e.get("delay_days_mentioned", 0) for e in emails)
    return min(1.0, delay_days / _EMAIL_DELAY_SATURATION_DAYS), float(delay_days)


def _eta_deviation_signal(shipment: Shipment) -> float:
    """The ERP's own DELAYED status is the simplest available ETA-miss signal."""
    return 1.0 if shipment.status == ShipmentStatus.DELAYED else 0.0


def _severity_for(risk_score: float) -> str:
    if risk_score >= settings.risk_severity_critical:
        return "critical"
    if risk_score >= settings.risk_severity_high:
        return "high"
    if risk_score >= settings.risk_severity_medium:
        return "medium"
    return "low"


class RiskDetectionExecutor(Executor):
    """Detects shipments at risk of delay and raises scored RiskAlerts."""

    @handler
    async def process(self, message: IngestedData, ctx: WorkflowContext[RiskAssessment]) -> None:
        logger.info(f"Risk detection: analyzing {len(message.shipments)} shipments...")
        now = _current_time()

        milestones_by_shipment: dict[str, list[Milestone]] = defaultdict(list)
        for m in message.milestones:
            milestones_by_shipment[m.shipment_id].append(m)

        gps_by_shipment: dict[str, list[GPSReading]] = defaultdict(list)
        for g in message.gps_readings:
            gps_by_shipment[g.shipment_id].append(g)

        emails_by_shipment: dict[str, list[dict]] = defaultdict(list)
        for e in message.email_summaries:
            emails_by_shipment[e["shipment_id"]].append(e)

        alerts: list[RiskAlert] = []
        for shipment in message.shipments:
            sid = shipment.shipment_id
            milestone_score, milestone_delay = _milestone_delay_signal(milestones_by_shipment[sid], now)
            gps_score, gps_delay = _gps_anomaly_signal(gps_by_shipment[sid], now)
            email_score, email_delay = _email_signal(emails_by_shipment[sid])
            eta_score = _eta_deviation_signal(shipment)

            risk_score = (
                settings.milestone_delay_weight * milestone_score
                + settings.gps_anomaly_weight * gps_score
                + settings.email_signal_weight * email_score
                + settings.eta_deviation_weight * eta_score
            )
            risk_score = min(1.0, max(0.0, risk_score))

            if risk_score <= 0.0:
                continue

            sources: list[str] = []
            reasons: list[str] = []
            if milestone_score > 0:
                sources.append("milestone_delay")
                reasons.append(f"milestone delayed {milestone_delay:.1f}d")
            if gps_score > 0:
                sources.append("gps_anomaly")
                reasons.append(f"GPS stalled {gps_delay * 24:.0f}h")
            if email_score > 0:
                sources.append("email_signal")
                reasons.append(f"carrier email reports {email_delay:.0f}d delay")
            if eta_score > 0:
                sources.append("eta_deviation")
                reasons.append("shipment marked delayed")

            estimated_delay_days = max(milestone_delay, gps_delay, email_delay)

            alerts.append(
                RiskAlert(
                    alert_id=f"ALERT-{sid}",
                    shipment_id=sid,
                    po_id=shipment.po_id,
                    severity=_severity_for(risk_score),
                    risk_score=round(risk_score, 3),
                    sources=sources,
                    description=f"{sid} at risk: " + "; ".join(reasons),
                    estimated_delay_days=round(estimated_delay_days, 1),
                )
            )

        alerts.sort(key=lambda a: a.risk_score, reverse=True)

        logger.info(f"Risk detection complete: {len(alerts)} alert(s) raised")
        for alert in alerts:
            logger.info(f"  {alert.alert_id} | {alert.severity:<8} | score={alert.risk_score} | {alert.sources}")

        await ctx.send_message(RiskAssessment(alerts=alerts, ingested_data=message))
