"""Sales Order domain models — SQLAlchemy table + Pydantic schema."""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base
from src.models.erp import Priority


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class SalesOrderTable(Base):
    __tablename__ = "sales_orders"

    so_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer: Mapped[str] = mapped_column(String(100))
    material: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    delivery_commitment_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    def __repr__(self) -> str:
        return (
            f"<SalesOrder(so_id={self.so_id!r}, customer={self.customer!r}, "
            f"material={self.material!r}, priority={self.priority!r})>"
        )


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class SalesOrder(BaseModel):
    so_id: str = Field(description="Unique sales order identifier")
    customer: str
    material: str
    quantity: int = Field(gt=0)
    delivery_commitment_date: date
    priority: Priority = Priority.MEDIUM

    model_config = {"from_attributes": True}