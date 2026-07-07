"""Executor 1: Data Ingestion Agent.

Reads all supply chain data from SQLite, validates through Pydantic,
and assembles into an IngestedData message for the risk detection executor.
"""

import logging

from sqlalchemy import select
from typing_extensions import Never

from agent_framework import Executor, WorkflowContext, handler

from src.db import async_session
from src.models.email import CarrierEmail, CarrierEmailTable
from src.models.gps import GPSReading, GPSReadingTable
from src.models.milestone import Milestone, MilestoneTable
from src.models.shipment import Shipment, ShipmentTable
from src.state import IngestedData

logger = logging.getLogger("supply_chain_agent.ingestion")


class IngestionExecutor(Executor):
    """Fetches and normalizes data from all supply chain sources.

    Reads from SQLite (local dev) or Azure SQL (production) — same code,
    different DATABASE_URL in .env.
    """

    @handler
    async def process(self, message: str, ctx: WorkflowContext[IngestedData]) -> None:
        """Fetch data from the database and forward to risk detection.

        Accepts a str trigger message (e.g. "run") from the workflow entrypoint.
        """
        logger.info("Ingestion agent starting — fetching data from database...")

        # 1. Fetch active shipments (not delivered)
        async with async_session() as session:
            result = await session.execute(
                select(ShipmentTable).where(ShipmentTable.status != "delivered")
            )
            shipment_rows = result.scalars().all()

        shipments = [Shipment.model_validate(row) for row in shipment_rows]
        logger.info(f"  Fetched {len(shipments)} active shipments")

        # 2. Fetch milestones for those shipments
        shipment_ids = [s.shipment_id for s in shipments]
        async with async_session() as session:
            result = await session.execute(
                select(MilestoneTable).where(MilestoneTable.shipment_id.in_(shipment_ids))
            )
            milestone_rows = result.scalars().all()

        milestones = [Milestone.model_validate(row) for row in milestone_rows]
        logger.info(f"  Fetched {len(milestones)} milestones")

        # 3. Fetch GPS readings
        async with async_session() as session:
            result = await session.execute(
                select(GPSReadingTable).where(GPSReadingTable.shipment_id.in_(shipment_ids))
            )
            gps_rows = result.scalars().all()

        gps_readings = [GPSReading.model_validate(row) for row in gps_rows]
        logger.info(f"  Fetched {len(gps_readings)} GPS readings")

        # 4. Fetch carrier emails
        async with async_session() as session:
            result = await session.execute(
                select(CarrierEmailTable).where(
                    CarrierEmailTable.shipment_id.in_(shipment_ids)
                )
            )
            email_rows = result.scalars().all()

        email_summaries = []
        for row in email_rows:
            email_summaries.append({
                "email_id": row.email_id,
                "shipment_id": row.shipment_id,
                "subject": row.subject,
                "delay_days_mentioned": row.delay_days_mentioned,
                "reason": row.reason,
            })
        logger.info(f"  Fetched {len(email_summaries)} carrier emails")

        # 5. Assemble and forward
        ingested = IngestedData(
            shipments=shipments,
            milestones=milestones,
            gps_readings=gps_readings,
            email_summaries=email_summaries,
        )

        logger.info(
            f"Ingestion complete: {len(shipments)} shipments, "
            f"{len(milestones)} milestones, {len(gps_readings)} GPS, "
            f"{len(email_summaries)} emails"
        )

        await ctx.send_message(ingested)