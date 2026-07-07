"""Executor 1: Data Ingestion Agent.

Reads shipment tracking data, ERP data, and email communications.
Normalizes and enriches raw data into a unified IngestedData message.
"""

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.state import IngestedData

logger = logging.getLogger("supply_chain_agent.ingestion")


class IngestionExecutor(Executor):
    """Fetches and normalizes data from all supply chain sources.

    Tools (Phase 2):
        - query_erp: Fetch POs, SOs, inventory, shipments, milestones from Azure SQL
        - parse_email: Search and parse carrier emails via Azure AI Search
        - fetch_gps: Read latest GPS readings from Event Hubs or file mock
    """

    @handler
    async def process(self, message: IngestedData, ctx: WorkflowContext[IngestedData]) -> None:
        """Fetch data from all sources and forward to risk detection."""
        logger.info("Ingestion agent starting — fetching data from all sources...")

        # TODO Phase 2: Replace with actual data fetching via @tool functions
        # 1. Query Azure SQL for active shipments with upcoming delivery dates
        # 2. Fetch recent milestones for those shipments
        # 3. Pull latest GPS readings from Event Hubs consumer / file mock
        # 4. Search Azure AI Search for recent carrier emails mentioning delays

        logger.info(
            f"Ingestion complete: {len(message.shipments)} shipments, "
            f"{len(message.milestones)} milestones, "
            f"{len(message.gps_readings)} GPS readings, "
            f"{len(message.email_summaries)} email signals"
        )

        # Forward populated data to next executor (RiskDetection)
        await ctx.send_message(message)
