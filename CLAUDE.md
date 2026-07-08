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
- **DONE**: MitigationExecutor decides a primary action per alert (switch_transport_mode / expedite_shipment / notify_carrier by a deterministic decision tree) plus a notify_customer companion when sales orders are affected, then routes every action to auto vs. escalation via `confidence_threshold` / `cost_escalation_threshold`. The `reasoning` field is LLM-generated (Azure OpenAI via shared `src/llm.py`) when `AZURE_OPENAI_ENDPOINT` is set — and falls back to a deterministic explanation otherwise (any LLM failure is caught, so behavior is identical with or without Azure configured); unit-tested in `tests/test_executors/test_mitigation.py` (LLM path untested locally since no `.env` credentials exist)
- **DONE**: AutonomousActionExecutor / HumanApprovalExecutor are real (not stubs) — they record simulated execution / pending-approval outcomes as the two terminal `ActionReport` outputs
- **DONE**: Full workflow runs end-to-end across all 6 executors (verified) — 3 alerts → 6 mitigation actions (3 auto-executed notify_customer, 3 escalated switch_transport_mode/expedite_shipment) — both the autonomous and human-approval branches fire in the same run
- **DONE**: Thin FastAPI wrapper (`src/api.py`) — `POST /run` executes the full pipeline and returns JSON; `GET /health`; Swagger docs at `/docs`
- **DONE**: `src/email_parsing.py` actually parses each carrier email's unstructured `subject`/`body` (LLM when Azure is configured, regex fallback otherwise — both verified to reproduce the mock corpus's intended delay/reason exactly) instead of trusting the pre-tagged `delay_days_mentioned`/`reason` DB columns; wired into `IngestionExecutor`. Closes the requirement doc's "combining structured and unstructured signals" gap.
- **IN PROGRESS**: Azure migration Phase 1 (Azure OpenAI only). Code side done — LLM client centralized in `src/llm.py`, endpoint-format bug fixed (uses OpenAI resource endpoint, not Foundry project endpoint), keyless AAD auth. Bicep provisioning authored in `infra/` (`main.bicep` + `main.bicepparam` + `README.md`). **Blocked on user**: az CLI not installed on this machine, and provisioning needs the user's subscription — user runs `infra/README.md` steps, then sets `AZURE_OPENAI_ENDPOINT`/`MODEL_DEPLOYMENT_NAME` in `.env`. LLM path is still unverified against a live endpoint.
- **NEXT**: after Phase 1 verified live — Azure SQL migration (Phase 1 remainder), then containerize + Container Apps (Phase 2). Candidates beyond migration: Bing-grounded cross-shipment/carrier intelligence (stretch), a real dashboard.

## Azure migration plan (Phase 1 in progress — Azure OpenAI)

Design principle: keep the deterministic WorkflowBuilder pipeline as the control
plane; use Azure AI Foundry only for narrow LLM calls (already how
`mitigation.py`/`email_parsing.py` are built) rather than re-platforming onto
Foundry Agent Service's thread/tool model. GenAIOps best practice is to keep
consequential/costly decisions (auto-execute vs. escalate) deterministic and
auditable, and reserve full agentic tool-use for genuinely open-ended tasks
(e.g. a future Bing-grounded carrier/port risk lookup — see stretch row below).

### Services needed, mapped to what they replace

| # | Azure service | Replaces (local dev) | Status |
|---|---|---|---|
| 1 | Azure OpenAI resource + GPT-4.1 deployment | Deterministic-only fallback reasoning | **Provisioning ready** — Bicep in `infra/`; set `AZURE_OPENAI_ENDPOINT` + `MODEL_DEPLOYMENT_NAME` from its outputs, no code change. (Endpoint-format bug fixed: LLM hooks now use the OpenAI *resource* endpoint via `src/llm.py`, not the Foundry project endpoint.) |
| 2 | Azure SQL Database | `supply_chain.db` (SQLite) | **Code ready** — swap `DATABASE_URL` to `mssql+aioodbc://...`; container image needs `msodbcsql18` + `unixodbc` installed (apt, not pip) since aioodbc wraps the system ODBC driver |
| 3 | User-Assigned Managed Identity | n/a (local dev has no identity) | New — one identity, attached to both the Container App and its scheduled Job |
| 4 | Azure Container Registry | n/a | New — needs a `Dockerfile` (not yet written) |
| 5 | Azure Container Apps (environment + app) | `python -m src.api` / `uvicorn` on a laptop | New |
| 6 | Azure Container Apps Job (cron) or Functions Timer trigger | Manual `POST /run` | New — the pipeline should run periodically, not only on demand |
| 7 | Azure Key Vault | `.env` file | New, optional — only for whatever secret can't use Managed Identity (ideally nothing, see below) |
| 8 | Log Analytics + Application Insights | Console logs (`RichHandler`) | New, optional but recommended — `agent_framework`'s `ChatTelemetryLayer` is OpenTelemetry-based already |
| 9 | *(stretch)* Azure Event Hubs | Static `gps_readings` mock rows | Not started — `eventhub_connection_string`/`eventhub_name` already stubbed in `config.py`, unused |
| 10 | *(stretch)* Azure AI Search | n/a today (email parsing is per-email extraction, not corpus search) | Not started — `azure_search_endpoint`/`azure_search_index_name` already stubbed in `config.py`, unused |
| 11 | *(stretch)* Grounding with Bing Search (via Foundry Agent Service) | n/a | Not started — the one place a real Foundry *Agent* (tool-calling) belongs, per the A-vs-B discussion, for cross-shipment/carrier intelligence |
| 12 | GitHub Actions + Entra ID federated credential (OIDC) | Manual `docker build`/`push` | New — avoids storing any long-lived Azure secret in GitHub |

### Credentials / API keys to procure

The mitigation and email-parsing LLM hooks are coded **exclusively against
`DefaultAzureCredential`** (`azure.identity.aio`) — no API key parameter exists
in that code path today. Sticking with that (recommended): in production, the
honest answer is **zero long-lived API keys** — what you actually need to
procure/configure instead is IAM role assignments for the Managed Identity:

| Resource | What to set up | Secret? |
|---|---|---|
| Azure OpenAI / Foundry resource | Assign **Cognitive Services OpenAI User** role to the Managed Identity | No key |
| Azure SQL | Set the Managed Identity as (or map it via) an Azure AD contained database user (`CREATE USER [identity-name] FROM EXTERNAL PROVIDER`) | No key |
| Key Vault (if used) | Assign **Key Vault Secrets User** role to the Managed Identity | No key |

Only the stretch items are genuinely key-based (nothing to do until those are built):

| Resource | Key needed | Notes |
|---|---|---|
| Azure AI Search | Admin or query API key | AAD auth is supported on newer API versions too, but key-based is the simpler default |
| Azure Event Hubs | Connection string (SAS key) | Matches the existing `eventhub_connection_string` config field as-is; AAD is a possible alternative |
| Grounding with Bing Search | Its own resource + API key, procured via Azure Marketplace | Tied specifically to Foundry Agent Service tool use |

**Local dev, outside Azure:** no key needed either — run `az login` once and
`DefaultAzureCredential` picks up your personal Azure AD session, as long as
you have the RBAC roles above on the dev resources. If per-developer RBAC
setup is too much friction for quick local testing, the faster (less secure)
alternative is to add an `api_key` fallback parameter to the two LLM hooks and
paste a key from the Azure OpenAI resource's "Keys and Endpoint" page — that's
a small, deliberate code change we haven't made, flagging it here rather than
doing it silently.

### Phased rollout
1. Azure SQL + Foundry project + Managed Identity + RBAC role assignments above — no code changes beyond `.env` values.
2. Write a `Dockerfile`, push to ACR, deploy `src/api.py` to Container Apps; add the scheduled Container Apps Job.
3. Replace mock data sources with real feeds (Event Hubs for GPS, Graph API/Logic Apps for email) — new ingestion code required.
4. App Insights via OpenTelemetry; CI/CD via GitHub Actions with OIDC (no `AZURE_CREDENTIALS` secret).

## Key files
- `src/workflow.py` — WorkflowBuilder graph wiring all 6 executors (no stubs remain)
- `src/executors/ingestion.py` — Live SQLite reads, fully implemented
- `src/email_parsing.py` — Unstructured email body/subject parsing (LLM + regex fallback)
- `src/executors/risk_detection.py` — Risk scoring across 4 signals, fully implemented
- `src/executors/impact_analysis.py` — Stockout/stoppage/revenue impact, fully implemented
- `src/executors/mitigation.py` — Action decision + auto/escalation routing + optional LLM reasoning, fully implemented
- `src/executors/autonomous_action.py` — Simulated auto-execution, fully implemented
- `src/executors/human_approval.py` — Escalation reporting, fully implemented
- `src/llm.py` — Shared keyless Azure OpenAI chat client for the LLM hooks (mitigation + email parsing)
- `infra/` — Bicep provisioning for Azure OpenAI (main.bicep, main.bicepparam, README.md)
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
- Enums are `StrEnum` (not `(str, Enum)`) — always accessed via `.value` at DB/serialization boundaries
- Config-driven thresholds (never hardcode); heuristic proxies with no real backing data
  (revenue-per-unit, mitigation action costs) are documented module constants, not settings
- Full file replacements preferred over incremental edits
- Commit after each working step
- Database is SQLite locally (supply_chain.db), Azure SQL in production — same SQLAlchemy code
- Shared CLI/API startup (`.env` load + logging) lives in `src/bootstrap.py`
- Lint: `ruff check src/ tests/ mock_data/` must pass clean (config in pyproject.toml)
- Tests are wall-clock-deterministic: `risk_detection._current_time()` is the "now" seam,
  pinned by an autouse fixture in `tests/conftest.py` to 2026-07-07 (the mock dataset's anchor
  date). Production keeps real `datetime.utcnow()`. Don't reintroduce direct `utcnow()` calls in
  risk logic — route through the seam so time-boundary cases (e.g. SH-3003's stall vs. supply)
  stay deterministic.
