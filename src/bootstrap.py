"""Shared startup for both entrypoints (CLI `src/main.py` and API `src/api.py`)."""

import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

from src.config import settings


def bootstrap() -> None:
    """Load .env and configure logging. Safe to call more than once."""
    load_dotenv()
    logging.basicConfig(
        level=settings.log_level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
        force=True,
    )
