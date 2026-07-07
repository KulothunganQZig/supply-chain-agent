# Autonomous Supply Chain Visibility & Mitigation Agent

An agentic AI system that detects supply chain risks and autonomously recommends or executes mitigation actions — built on **Microsoft Agent Framework 1.0** and deployed to **Azure AI Foundry Agent Service**.

## Architecture

The system implements a 6-agent pipeline orchestrated via Microsoft Agent Framework's WorkflowBuilder:

```
Data Sources → Foundry Toolbox → WorkflowBuilder Pipeline
                                       │
                                 IngestionExecutor
                                       │
                                 RiskDetectionExecutor
                                       │
                                 ImpactAnalysisExecutor
                                       │
                                 MitigationExecutor
                                       │
                              ┌────────┴────────┐
                        (confidence ≥ 0.85) (confidence < 0.85)
                              │                 │
                    AutonomousActionExecutor  HumanApprovalExecutor
```

### Agents

| # | Agent | Role | Key Tools |
|---|-------|------|-----------|
| 1 | **Ingestion** | Normalize ERP, transport, GPS, email data | `query_erp`, `parse_email`, `fetch_gps` |
| 2 | **Risk Detection** | Detect shipments at risk of delay | `check_milestones`, `analyze_gps`, `search_emails` |
| 3 | **Impact Analysis** | Evaluate stockout / production stoppage risk | `calc_days_of_supply`, `check_safety_stock` |
| 4 | **Mitigation Decision** | Propose actions with confidence scores | Structured output → action plan |
| 5 | **Autonomous Action** | Execute high-confidence actions | `reroute_shipment`, `notify_carrier`, `send_alert` |
| 6 | **Human Approval** | Escalate high-cost decisions | Checkpoint → approval request via Teams |

### Azure Services

- **Azure AI Foundry Agent Service** — Hosted agent runtime (managed scaling, identity, observability)
- **Azure OpenAI** — GPT-4.1 for agent reasoning
- **Azure SQL Database** — Structured supply chain data (POs, SOs, inventory, shipments)
- **Azure AI Search** — Hybrid vector index for carrier email retrieval
- **Azure Event Hubs** — GPS streaming ingestion
- **Azure Logic Apps** — Notification triggers
- **Azure Monitor** — OpenTelemetry tracing

## Project Structure

```
supply-chain-agent/
├── pyproject.toml                  # Project metadata + dependencies
├── Dockerfile                      # Container for Foundry hosted agent
├── azure.yaml                      # Azure Developer CLI template
├── agent.yaml                      # Foundry agent manifest
├── .env.example                    # Environment variable template
├── infra/                          # Bicep IaC modules
│   ├── main.bicep
│   └── modules/
│       ├── foundry.bicep
│       ├── sql.bicep
│       ├── ai-search.bicep
│       └── monitoring.bicep
├── src/
│   ├── main.py                     # Foundry hosted agent entrypoint
│   ├── workflow.py                 # WorkflowBuilder graph definition
│   ├── state.py                    # Typed message schemas
│   ├── executors/                  # One executor per agent
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   ├── risk_detection.py
│   │   ├── impact_analysis.py
│   │   ├── mitigation.py
│   │   ├── autonomous_action.py
│   │   └── human_approval.py
│   ├── tools/                      # @tool-decorated functions
│   │   ├── __init__.py
│   │   ├── erp_tools.py
│   │   ├── email_tools.py
│   │   ├── gps_tools.py
│   │   ├── carrier_tools.py
│   │   └── notification_tools.py
│   ├── models/                     # Pydantic data models
│   │   ├── __init__.py
│   │   ├── erp.py
│   │   ├── shipment.py
│   │   ├── risk.py
│   │   └── mitigation.py
│   └── config.py                   # Settings + thresholds
├── mock_data/
│   ├── generate.py                 # Synthetic data generator
│   ├── seed_db.py                  # Seed Azure SQL / local SQLite
│   └── sample_emails.json          # Carrier email simulations
├── dashboard/                      # Risk visibility dashboard
│   ├── api/
│   │   └── main.py                 # FastAPI backend
│   └── frontend/                   # React frontend
├── tests/
│   ├── conftest.py
│   ├── test_workflow.py
│   ├── test_executors/
│   └── test_tools/
├── eval/
│   ├── scenarios.json              # End-to-end test scenarios
│   └── run_eval.py                 # Evaluation runner (pytest style)
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint, test on PR
│       └── deploy.yml              # azd deploy on merge to main
└── .vscode/
    ├── settings.json               # Python path, formatter
    ├── launch.json                 # F5 debug config for Agent Inspector
    └── extensions.json             # Recommended extensions
```

## Prerequisites

- Python 3.10+ (recommend 3.12)
- Docker Desktop
- Azure CLI (`az`) + Azure Developer CLI (`azd`)
- VS Code with Foundry Toolkit extension
- Azure subscription with a Foundry project

## Quick Start

```bash
# Clone the repo
git clone https://github.com/<your-username>/supply-chain-agent.git
cd supply-chain-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Foundry project endpoint and model deployment name

# Generate mock data and seed local SQLite
python -m mock_data.generate
python -m mock_data.seed_db

# Run locally with Agent Inspector (from VS Code: F5)
python -m src.main

# Run tests
pytest tests/

# Deploy to Azure
az login
azd up
```

## Development Phases

- **Phase 1**: Mock data + WorkflowBuilder skeleton with all 6 executors
- **Phase 2**: Core agent logic — risk detection, impact analysis, mitigation
- **Phase 3**: Azure deployment — Bicep IaC, Foundry hosting, AI Search index
- **Phase 4**: Advanced — ETA prediction, cost optimization, dashboard

## License

MIT
