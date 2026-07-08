"""Async database engine and session factory.

Uses SQLAlchemy 2.0 async API with:
    - aiosqlite for local development (SQLite)
    - aioodbc for production (Azure SQL)

The connection string is driven by DATABASE_URL in .env — same code,
swap the string to switch backends.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# Async engine — aiosqlite locally, aioodbc in production
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
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
