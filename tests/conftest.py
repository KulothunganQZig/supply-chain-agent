"""Shared pytest fixtures.

The mock dataset (mock_data/generate.py) is a snapshot anchored to 2026-07-07
as "today" — that's the reference date its own summary output uses. But the
risk engine measures delays against real wall-clock time (datetime.utcnow()),
so as real time marches past the fixed mock timestamps, borderline cases (e.g.
SH-3003's ~3-day GPS stall vs. its 3.0-day supply) drift across decision
thresholds and make time-dependent assertions flaky.

This autouse fixture pins the risk engine's reference "now" to the dataset's
anchor so the whole suite is deterministic regardless of when it runs.
Production is unaffected — it keeps using real wall-clock via
risk_detection._current_time().
"""

from datetime import datetime

import pytest

import src.executors.risk_detection as risk_detection

# Matches mock_data/generate.py's date(2026, 7, 7) reference anchor.
REFERENCE_NOW = datetime(2026, 7, 7, 12, 0)


@pytest.fixture(autouse=True)
def _pin_reference_time(monkeypatch):
    monkeypatch.setattr(risk_detection, "_current_time", lambda: REFERENCE_NOW)
