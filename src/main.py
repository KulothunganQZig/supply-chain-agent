"""Entrypoint for the Supply Chain Visibility Agent.

Usage:
    python -m src.main
"""

import asyncio
import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

from src.config import settings
from src.workflow import build_workflow

load_dotenv()

logging.basicConfig(
    level=settings.log_level,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("supply_chain_agent")


async def run_pipeline():
    """Execute the supply chain agent pipeline."""
    logger.info("Building supply chain agent workflow...")
    workflow = build_workflow()

    logger.info("Starting pipeline execution...")

    # Run the workflow with a simple trigger string
    # The IngestionExecutor accepts str and fetches data from the DB
    result = await workflow.run("run")

    # Print outputs from terminal executors
    outputs = result.get_outputs()
    if outputs:
        for output in outputs:
            logger.info(f"Workflow output: {output}")
    else:
        logger.info("Pipeline completed (no terminal outputs — expected until Phase 2)")

    logger.info("Pipeline execution complete.")


def main():
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()