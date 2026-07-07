"""Entrypoint for the Supply Chain Visibility Agent.

Runs locally for development (with Agent Inspector support via F5 in VS Code)
or as a Foundry Hosted Agent in production.
"""

import asyncio
import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

from src.config import settings
from src.state import IngestedData
from src.workflow import build_workflow

# Load .env file (Agent Framework does not auto-load it)
load_dotenv()

logging.basicConfig(
    level=settings.log_level,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("supply_chain_agent")


async def run_pipeline():
    """Execute the supply chain agent pipeline once.

    In production, this would be triggered by:
    - A scheduled routine (Foundry routines / cron)
    - An Event Hubs trigger (new GPS data batch)
    - A manual invocation via the Responses API
    """
    logger.info("Building supply chain agent workflow...")
    workflow = build_workflow()

    # Start the pipeline with a trigger message.
    # The IngestionExecutor receives this and populates it with real data.
    trigger = IngestedData()

    logger.info("Starting pipeline execution...")

    # Stream events to see each executor's progress in real time
    async for event in workflow.run_stream(trigger):
        logger.info(f"[{event.executor_id}] {event.type}")

    logger.info("Pipeline execution complete.")


def main():
    """CLI entrypoint."""
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
