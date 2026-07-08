"""Entrypoint for the Supply Chain Visibility Agent.

Usage:
    python -m src.main
"""

import asyncio
import logging

from src.bootstrap import bootstrap
from src.workflow import build_workflow

bootstrap()
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
        logger.info("Pipeline completed with no terminal outputs (no risk alerts were raised)")

    logger.info("Pipeline execution complete.")


def main():
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()