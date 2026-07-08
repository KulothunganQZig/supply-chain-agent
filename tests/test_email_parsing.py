"""Tests for src/email_parsing.py — the regex fallback (no Azure endpoint
configured in the test environment, so this is the path that actually runs).
"""

import pytest

from mock_data.generate import CARRIER_EMAILS
from src.email_parsing import parse_email_delay_signal


def _email(email_id: str):
    return next(e for e in CARRIER_EMAILS if e.email_id == email_id)


@pytest.mark.asyncio
async def test_customs_hold_email_parsed_from_body_text():
    email = _email("EM-0001")
    signal = await parse_email_delay_signal(email.subject, email.body)

    assert signal.mentions_delay is True
    assert signal.delay_days == 5.0
    assert signal.reason == "customs inspection hold at Suez Canal"


@pytest.mark.asyncio
async def test_port_congestion_email_parsed_from_body_text():
    email = _email("EM-0002")
    signal = await parse_email_delay_signal(email.subject, email.body)

    assert signal.mentions_delay is True
    assert signal.delay_days == 4.0
    assert signal.reason == "port congestion"


@pytest.mark.asyncio
async def test_no_delay_mentioned_in_plain_status_update():
    signal = await parse_email_delay_signal(
        "Shipment on schedule", "Your shipment is on track and will arrive as planned."
    )
    assert signal.mentions_delay is False
    assert signal.delay_days == 0.0
