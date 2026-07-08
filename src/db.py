"""Async database engine and session factory.

Uses SQLAlchemy 2.0 async API with:
    - aiosqlite for local development (SQLite)
    - aioodbc + Managed Identity for Azure SQL (keyless)

Backend is chosen by config: SQLite by default, Azure SQL when
azure_sql_server is set (see _resolve_database_url).
"""

from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


def _resolve_database_url() -> str:
    """SQLite locally; keyless Azure SQL (aioodbc + Managed Identity) when configured.

    Azure SQL auth is ActiveDirectoryMsi — the msodbcsql18 driver fetches an AAD
    token for the user-assigned Managed Identity itself (client id from
    azure_client_id), so there is no password anywhere. Requires the ODBC driver,
    which is installed in the container image (not on the dev host, which has no
    admin to install it).
    """
    if not settings.azure_sql_server:
        return settings.database_url

    odbc = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{settings.azure_sql_server},1433;"
        f"Database={settings.azure_sql_database};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
        "Authentication=ActiveDirectoryMsi;"
        f"UID={settings.azure_client_id}"
    )
    return "mssql+aioodbc:///?odbc_connect=" + quote_plus(odbc)


# Async engine — aiosqlite locally, aioodbc + Managed Identity for Azure SQL
engine = create_async_engine(
    _resolve_database_url(),
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,  # Azure SQL drops idle connections; validate before use
)

# Session factory — one session per unit of work
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


async def create_tables() -> None:
    """Create all tables defined in Base.metadata.

    Used for local dev / testing. In production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables. Use only in testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
