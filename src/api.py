"""FastAPI wrapper around the supply chain agent workflow.

Thin HTTP surface over the same WorkflowBuilder pipeline `src/main.py` runs
from the CLI — no separate business logic, just triggers a run and shapes
the workflow's events into a JSON response.

Usage:
    python -m src.api                       # dev server on :8000
    uvicorn src.api:app --reload            # equivalent, with autoreload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.bootstrap import bootstrap
from src.state import ActionReport, ImpactReport, MitigationPlan, RiskAssessment
from src.workflow import build_workflow

bootstrap()
logger = logging.getLogger("supply_chain_agent.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the schema exists and seed on first boot.

    Baked-in SQLite is already seeded at build time, so this is effectively a
    no-op there; on a fresh Azure SQL database it creates the tables and loads
    the mock data (idempotent — skips if already populated).
    """
    from mock_data.seed_db import seed_if_empty

    await seed_if_empty()
    yield


app = FastAPI(
    title="Supply Chain Visibility Agent",
    description="Detects supply chain risks and autonomously executes or escalates mitigation actions.",
    version="0.1.0",
    lifespan=lifespan,
)

# App Insights (no-op unless APPLICATIONINSIGHTS_CONNECTION_STRING is set).
from src.telemetry import setup_telemetry  # noqa: E402

setup_telemetry(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/run")
async def run_pipeline() -> dict:
    """Run the full 6-executor pipeline once and return every stage's output."""
    logger.info("API: running pipeline...")
    workflow = build_workflow()
    result = await workflow.run("run")

    risk_assessment: RiskAssessment | None = None
    impact_report: ImpactReport | None = None
    mitigation_plan: MitigationPlan | None = None
    action_reports: list[ActionReport] = []

    for event in result:
        if event.type != "executor_completed" or not event.data:
            continue
        for item in event.data:
            if isinstance(item, RiskAssessment):
                risk_assessment = item
            elif isinstance(item, ImpactReport):
                impact_report = item
            elif isinstance(item, MitigationPlan):
                mitigation_plan = item
            elif isinstance(item, ActionReport):
                action_reports.append(item)

    return {
        "alerts": [a.model_dump() for a in (risk_assessment.alerts if risk_assessment else [])],
        "impact_assessments": [a.model_dump() for a in (impact_report.assessments if impact_report else [])],
        "mitigation_actions": [a.model_dump() for a in (mitigation_plan.actions if mitigation_plan else [])],
        "auto_actions": [a.model_dump() for a in (mitigation_plan.auto_actions if mitigation_plan else [])],
        "escalation_actions": [
            a.model_dump() for a in (mitigation_plan.escalation_actions if mitigation_plan else [])
        ],
        "action_reports": [r.model_dump() for r in action_reports],
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
