# Supply Chain Visibility Agent

## What this project is
An agentic AI system that detects supply chain risks and autonomously executes or escalates mitigation actions. Built on Microsoft Agent Framework 1.0, targeting Azure AI Foundry Agent Service deployment.

## Architecture
6-executor WorkflowBuilder pipeline:
```
Ingestion → Risk Detection → Impact Analysis → Mitigation → Autonomous Action / Human Approval
```

## Current state (Phase 1 complete, Phase 2 complete — all 6 executors implemented)
- **DONE**: All 7 mock data tables (POs, Shipments, Inventory, Sales Orders, Milestones, GPS, Emails) with Pydantic + SQLAlchemy models, JSON generation, and SQLite seeding
- **DONE**: IngestionExecutor reads live from SQLite — shipments/milestones/GPS/emails plus purchase orders, inventory, and sales orders scoped to the materials those POs carry
- **DONE**: RiskDetectionExecutor scores each shipment across 4 weighted signals (milestone delay, GPS stall, email signal, ETA deviation) and emits RiskAlerts; unit-tested in `tests/test_executors/test_risk_detection.py`
- **DONE**: ImpactAnalysisExecutor joins each alert to its PO/plant/inventory and to sales orders sharing the same material, then flags stockout risk (below safety stock or days-of-supply ≤ critical threshold) and production stoppage risk (delay ≥ remaining days of supply), plus a rough revenue-at-risk figure (quantity × priority-tier $/unit proxy — no real price data in the mock set); unit-tested in `tests/test_executors/test_impact_analysis.py`
- **DONE**: MitigationExecutor decides a primary action per alert (switch_transport_mode / expedite_shipment / notify_carrier by a deterministic decision tree) plus a notify_customer companion when sales orders are affected, then routes every action to auto vs. escalation via `confidence_threshold` / `cost_escalation_threshold`. The `reasoning` field is LLM-generated (Azure OpenAI via `agent_framework_openai.OpenAIChatClient` + AAD auth) when `AZURE_AI_PROJECT_ENDPOINT` is set — this is the first executor wired to call the LLM — and falls back to a deterministic explanation otherwise (any LLM failure is caught, so behavior is identical with or without Azure configured); unit-tested in `tests/test_executors/test_mitigation.py` (LLM path untested locally since no `.env` credentials exist)
- **DONE**: AutonomousActionExecutor / HumanApprovalExecutor are real (not stubs) — they record simulated execution / pending-approval outcomes as the two terminal `ActionReport` outputs
- **DONE**: Full workflow runs end-to-end across all 6 executors (verified) — 3 alerts → 6 mitigation actions (3 auto-executed notify_customer, 3 escalated switch_transport_mode/expedite_shipment) — both the autonomous and human-approval branches fire in the same run
- **DONE**: Thin FastAPI wrapper (`src/api.py`) — `POST /run` executes the full pipeline and returns JSON; `GET /health`; Swagger docs at `/docs`
- **DONE**: `src/email_parsing.py` actually parses each carrier email's unstructured `subject`/`body` (LLM when Azure is configured, regex fallback otherwise — both verified to reproduce the mock corpus's intended delay/reason exactly) instead of trusting the pre-tagged `delay_days_mentioned`/`reason` DB columns; wired into `IngestionExecutor`. Closes the requirement doc's "combining structured and unstructured signals" gap.
- **NEXT**: none currently queued — all 6 executors implemented, requirement-doc gap check items (FastAPI, unstructured email parsing) closed. Candidates for further work: Azure migration (see below), Bing-grounded cross-shipment/carrier intelligence (optional stretch goal), a real dashboard.

## Azure migration plan (discussed, not yet started)
Keep the deterministic WorkflowBuilder pipeline as the control plane; use Azure AI Foundry only for narrow LLM calls (already how `mitigation.py`/`email_parsing.py` are built) rather than re-platforming onto Foundry Agent Service's thread/tool model — GenAIOps best practice is to keep consequential/costly decisions (auto-execute vs. escalate) deterministic and auditable, and reserve full agentic tool-use for genuinely open-ended tasks (e.g. a future Bing-grounded carrier/port risk lookup). Phases: (1) Azure SQL + Foundry project + Managed Identity — `DATABASE_URL`/`AZURE_AI_PROJECT_ENDPOINT` swaps already supported by existing code; (2) containerize `src/api.py` → Azure Container Apps + a scheduled Container Apps Job/Functions Timer (the pipeline needs to run periodically, not just on-demand); (3) replace mock data sources with real feeds (Event Hubs for GPS, Graph API/Logic Apps for email); (4) App Insights via OpenTelemetry, CI/CD via GitHub Actions.

## Key files
- `src/workflow.py` — WorkflowBuilder graph wiring all 6 executors (no stubs remain)
- `src/executors/ingestion.py` — Live SQLite reads, fully implemented
- `src/email_parsing.py` — Unstructured email body/subject parsing (LLM + regex fallback)
- `src/executors/risk_detection.py` — Risk scoring across 4 signals, fully implemented
- `src/executors/impact_analysis.py` — Stockout/stoppage/revenue impact, fully implemented
- `src/executors/mitigation.py` — Action decision + auto/escalation routing + optional LLM reasoning, fully implemented
- `src/executors/autonomous_action.py` — Simulated auto-execution, fully implemented
- `src/executors/human_approval.py` — Escalation reporting, fully implemented
- `src/state.py` — Pydantic message schemas between executors
- `src/models/` — SQLAlchemy tables + Pydantic schemas (erp.py, shipment.py, inventory.py, sales_order.py, milestone.py, gps.py, email.py)
- `src/db.py` — Async SQLAlchemy engine + session factory
- `src/config.py` — Settings with risk scoring weights and thresholds
- `mock_data/generate.py` — Curated dataset with deliberate anomalies
- `mock_data/seed_db.py` — Seeds all 7 tables into SQLite

## Tech stack
- Python 3.14, Microsoft Agent Framework 1.0 (`agent-framework` PyPI package)
- SQLAlchemy 2.0 async + aiosqlite (local) / aioodbc (Azure SQL)
- Pydantic v2 for validation
- Azure OpenAI GPT-4.1 (Phase 2, for LLM-based reasoning in executors)

## Risk signals embedded in mock data
| Signal | Shipments | Detail |
|---|---|---|
| Milestone delays | SH-3001, SH-3005 | customs_cleared stuck |
| GPS stalls | SH-3003, SH-3005 | speed=0 for 36+ hours |
| Carrier emails | SH-3001, SH-3005 | +5d and +4d delay notices |
| Low inventory | Steel Coils (1.9d), Battery Cells (3.0d), Carbon Fiber (2.4d) | Below safety stock |

## Risk scoring weights (from src/config.py)
- milestone_delay_weight: 0.35
- gps_anomaly_weight: 0.25
- email_signal_weight: 0.20
- eta_deviation_weight: 0.20

## Decision thresholds (from src/config.py)
- confidence_threshold: 0.85 (above = auto-execute, below = escalate)
- cost_escalation_threshold: 50000 (above = escalate regardless)
- days_of_supply_critical: 3 (below = stockout risk)
- risk_severity_critical/high/medium: 0.75 / 0.50 / 0.25 (risk_score buckets, else "low")

## Microsoft Agent Framework API patterns
```python
# Executor with handler
class MyExecutor(Executor):
    @handler
    async def process(self, message: InputType, ctx: WorkflowContext[OutputType]) -> None:
        await ctx.send_message(result)  # forward to next executor

# Terminal executor (workflow output)
class FinalExecutor(Executor):
    @handler
    async def process(self, message: InputType, ctx: WorkflowContext[Never, OutputType]) -> None:
        await ctx.yield_output(result)  # emit as workflow output

# WorkflowBuilder
workflow = (
    WorkflowBuilder(start_executor=first_executor)
    .add_edge(first, second)
    .add_edge(second, third, condition=my_condition)
    .build()
)

# Running
result = await workflow.run("trigger")
outputs = result.get_outputs()
```

## Shipment-to-PO mapping
- SH-3001 → PO-1001 (Steel Coils, Tata Steel → Plant-Detroit, CRITICAL, Maersk ocean, DELAYED)
- SH-3002 → PO-1002 (Polymer Resin, BASF → Plant-Chicago, MEDIUM, DB Schenker rail, IN_TRANSIT)
- SH-3003 → PO-1003 (Battery Cells, Samsung SDI → Plant-Houston, HIGH, DHL ocean, IN_TRANSIT)
- SH-3004 → PO-1004 (Adhesive Compound, Dow → Plant-Chicago, LOW, FedEx truck, IN_TRANSIT)
- SH-3005 → PO-1005 (Carbon Fiber Sheets, Sinopec → Plant-Munich, CRITICAL, Kuehne+Nagel ocean, IN_TRANSIT)

## Sales Orders at risk
- SO-2001: AutoCorp needs Steel Coils by Jul 18 (CRITICAL) — only 1.9d of supply
- SO-2003: NextGen Motors needs Battery Cells by Jul 22 (HIGH) — only 3.0d of supply
- SO-2005: Precision Mfg needs Carbon Fiber by Jul 28 (CRITICAL) — only 2.4d of supply
- SO-2006: Atlas Industries needs Steel Coils by Jul 25 (HIGH) — shares the 1.9d supply

## Commands
```bash
python -m mock_data.generate    # Generate JSON mock data
python -m mock_data.seed_db     # Seed SQLite from JSON
python -m src.main              # Run the full pipeline via CLI
python -m src.api               # Run the FastAPI server (:8000) — POST /run, GET /health
pytest tests/                   # Run tests
```

## API (src/api.py)
Thin FastAPI wrapper — no logic beyond `src/workflow.py`, just shapes workflow
events into JSON:
- `GET /health` → `{"status": "ok"}`
- `POST /run` → runs all 6 executors once, returns `alerts`, `impact_assessments`,
  `mitigation_actions`, `auto_actions`, `escalation_actions`, `action_reports`
- Pulled from `WorkflowRunResult`'s `executor_completed` events (`event.data` is
  `sent_messages + yielded_outputs`, isinstance-routed into the right state.py type)
  rather than duplicating the workflow graph
- Interactive docs at `/docs` (Swagger) and `/redoc` for free via FastAPI
- `tests/test_api.py` regenerates + reseeds the SQLite DB before running (unlike the
  executor tests, which construct `IngestedData` in memory and never touch the DB)

## Conventions
- One executor per agent — all 6 now real, in `src/executors/` (no stubs remain in `src/workflow.py`)
- Pydantic models for API/validation, SQLAlchemy models for DB — both in src/models/
- Config-driven thresholds (never hardcode); heuristic proxies with no real backing data
  (revenue-per-unit, mitigation action costs) are documented module constants, not settings
- Full file replacements preferred over incremental edits
- Commit after each working step
- Database is SQLite locally (supply_chain.db), Azure SQL in production — same SQLAlchemy code
- Shared CLI/API startup (`.env` load + logging) lives in `src/bootstrap.py`
