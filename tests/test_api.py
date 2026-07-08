"""Tests for the FastAPI wrapper (src/api.py).

Unlike the executor tests (which construct IngestedData in memory), /run goes
through the real IngestionExecutor and therefore the real SQLite DB — so this
module (re)generates and seeds it before running, mirroring the commands a
developer would run by hand (`python -m mock_data.generate && python -m
mock_data.seed_db`).
"""

import pytest
from fastapi.testclient import TestClient

from mock_data.generate import main as generate_mock_data
from mock_data.seed_db import seed_all
from src.api import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
async def _seeded_db():
    generate_mock_data()
    await seed_all()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_pipeline_end_to_end():
    response = client.post("/run")
    assert response.status_code == 200
    body = response.json()

    alert_shipment_ids = {a["shipment_id"] for a in body["alerts"]}
    assert alert_shipment_ids == {"SH-3001", "SH-3003", "SH-3005"}

    assert len(body["impact_assessments"]) == len(body["alerts"])
    assert len(body["mitigation_actions"]) == len(body["auto_actions"]) + len(body["escalation_actions"])

    # Both the autonomous-action and human-approval branches fire for this dataset.
    assert body["auto_actions"]
    assert body["escalation_actions"]
    assert len(body["action_reports"]) == 2
