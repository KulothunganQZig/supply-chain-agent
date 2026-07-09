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
- **DONE (verified live)**: Azure migration Phase 1 — Azure OpenAI provisioned via `infra/main.bicep` and the pipeline's LLM reasoning confirmed running against the real model. Deployed resource `oai-supplychain-vpv6suzb4aue6` (rg `rg-supplychain-agent`, eastus2), model `gpt-5-mini` (GlobalStandard), keyless AAD auth via the dev's `az login` + Cognitive Services OpenAI User role. `.env` (gitignored) holds the endpoint. `python -m src.main` now emits genuinely LLM-authored `reasoning` strings, not the deterministic fallback. Gotchas hit + resolved: (1) az CLI installed **without admin** via pip into a dedicated venv (`~/azcli-venv`); (2) `gpt-4.1`/`gpt-4.1-mini`/`gpt-4o-mini` are all in a deprecating state (blocked for new deployments) → switched to `gpt-5-mini`; (3) `gpt-5-mini` needs the `GlobalStandard` SKU (no regional Standard); (4) gpt-5 models need a **2025+ api-version** (`2024-10-21` → 404, `2025-04-01-preview` works).
- **DONE (verified live)**: Azure migration Phase 2 — the app runs on **Azure Container Apps**, keyless end-to-end. Image built in the cloud via `az acr build` (no local Docker — Docker Desktop engine was down) and pushed to ACR `acrsupplychain85768`; Container App `ca-supplychain` (env `cae-supplychain`) pulls it via a user-assigned Managed Identity `id-supplychain-app` (AcrPull) and calls gpt-5-mini via the same identity (Cognitive Services OpenAI User). `POST /run` on the live FQDN returns 200 with genuinely LLM-authored reasoning. Working `Dockerfile` (bakes+seeds SQLite, serves `uvicorn src.api:app` on :8000, honors `$PORT`), `.dockerignore`, and `pyproject` `[tool.setuptools] packages`. Steps documented in `infra/container-apps.md`. Key gotcha: set `AZURE_CLIENT_ID` env on the app so `DefaultAzureCredential` binds the right user-assigned identity.
- **DONE (verified live)**: Azure SQL migration — the app now reads/writes **Azure SQL**, keyless. Server `sql-sc-309221` (westus3 — East regions were capacity-blocked), DB `scdb` (Basic), AAD-only auth. `db.py` builds an `mssql+aioodbc` URL with `Authentication=ActiveDirectoryMsi` (ODBC driver fetches the AAD token for the user-assigned MI — no password) when `AZURE_SQL_SERVER` is set; SQLite otherwise. Dockerfile installs `msodbcsql18`+`unixodbc` (pinned `python:3.12-slim-bookworm` to match the MS repo). App seeds the empty DB on startup via `seed_if_empty()` (FastAPI lifespan). One manual step done: `infra/sql-grant.sql` T-SQL run in Portal Query Editor to make the MI a db user. Verified: `POST /run` returns 200 reading from Azure SQL, same 3 alerts + LLM reasoning. Image is now `v2`.
- **DONE**: Bicep consolidation — `infra/main.bicep` is now **full-stack** IaC (Log Analytics, Managed Identity, ACR, Azure OpenAI + gpt-5-mini, Azure SQL server/db/firewall, Container Apps env + app), keyless via the one identity. Compile-validated + what-if'd against the live RG: converges (6 NoChange); remaining diffs are benign (az-vs-bicep role-assignment GUID names, explicit Log Analytics name, minor property normalization). **Not re-applied** over the live stack (which was `az`-bootstrapped and works) — it's the go-forward source of truth for fresh deploys. SQL contained-user grant stays out-of-band (`infra/sql-grant.sql`, T-SQL not ARM).
- **DONE (Azure side)**: CI/CD — `.github/workflows/ci-cd.yml` lints+tests on push/PR and, on push to main, `az acr build` + `az containerapp update`. Auth is keyless **OIDC** via a dedicated identity `id-supplychain-cicd` (federated credential for `repo:KulothunganQZig/supply-chain-agent:ref:refs/heads/main`, Contributor on the RG). **User steps remaining**: add 3 repo secrets (`AZURE_CLIENT_ID`/`TENANT_ID`/`SUBSCRIPTION_ID` — values in `infra/cicd.md`) and push to main to trigger it. Not yet run (needs the secrets + a push).
- **DONE (partial, verified live)**: App Insights / OpenTelemetry. `appi-supplychain` (workspace-based, on `log-supplychain`) provisioned + in Bicep; `src/telemetry.py` wires `configure_azure_monitor()` + `agent_framework` instrumentation + FastAPIInstrumentor (opt-in via `APPLICATIONINSIGHTS_CONNECTION_STRING`, no-op locally). **Logs flow** — confirmed in the workspace (`AppTraces`, incl. "Application Insights telemetry enabled" + the pipeline/LLM logs). **Known gap**: distributed traces (`AppRequests`/`AppDependencies` — HTTP/LLM/SQL spans) are NOT exporting, only logs; likely an OTel trace-provider/instrumentation nuance (suspect: interaction between `configure_azure_monitor` and `agent_framework` observability, or FastAPIInstrumentor timing) — needs follow-up. Query telemetry via the **Log Analytics workspace** tables (`AppTraces`…), not the classic `az monitor app-insights query` schema (returns empty for workspace-based).
- **KNOWN ISSUE (surfaced by App Insights)**: Azure SQL cold-connect is flaky — a fresh replica sometimes hits `Login timeout expired` on all retries during startup (Basic tier, cross-region westus3 ↔ eastus2, MSI token + TDS handshake > timeout). App **self-heals** (Container Apps restarts until a replica connects; steady-state /run is 6/6 reliable) but cold starts can be slow/flaky. Startup now retries 6×5s (`api.py` lifespan). Fuller fixes if needed: shorter per-attempt ODBC timeout + more attempts, SQL in-region (was capacity-blocked), or Python-side token auth (azure-identity → `SQL_COPT_SS_ACCESS_TOKEN`) instead of the driver's `ActiveDirectoryMsi`.
- **NEXT (optional)**: fix distributed-trace export; scheduled Container Apps Job (periodic runs). Stretch: Bing-grounded cross-shipment intelligence, dashboard.

### Live Azure resources (all in rg-supplychain-agent, keyless via MI id-supplychain-app)
- Azure OpenAI `oai-supplychain-vpv6suzb4aue6` (eastus2) — gpt-5-mini deployment
- ACR `acrsupplychain85768` — image `supply-chain-agent:v2`
- Container Apps `cae-supplychain` / `ca-supplychain` (eastus2) — the running app
- Azure SQL `sql-sc-309221` / db `scdb` (westus3)
- Managed Identity `id-supplychain-app` — roles: AcrPull, Cognitive Services OpenAI User, + SQL contained user (db_ddladmin/datareader/datawriter)

## Azure migration plan (Phase 1 OpenAI + Phase 2 Container Apps DONE — SQL next)

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
| 1 | Azure OpenAI resource + gpt-5-mini deployment | Deterministic-only fallback reasoning | **DONE, verified live** — deployed via Bicep (`infra/`), `.env` set, LLM reasoning confirmed against the real model. Keyless AAD (no key). |
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
