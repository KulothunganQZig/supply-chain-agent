"""ERP domain models — Purchase Orders.

Two representations:
    - PurchaseOrderTable: SQLAlchemy ORM model (database table)
    - PurchaseOrder: Pydantic model (validation, serialization, API contracts)

Other tables (Sales Orders, Inventory) will be added one at a time
following the same pattern.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


# ---------------------------------------------------------------------------
# Enums (shared between SQLAlchemy and Pydantic)
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model (the table definition)
# ---------------------------------------------------------------------------

class PurchaseOrderTable(Base):
    """purchase_orders table in the database."""

    __tablename__ = "purchase_orders"

    po_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    supplier: Mapped[str] = mapped_column(String(100))
    material: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(String(100))
    destination_plant: Mapped[str] = mapped_column(String(100))
    required_delivery_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrder(po_id={self.po_id!r}, material={self.material!r}, "
            f"supplier={self.supplier!r}, priority={self.priority!r})>"
        )


# ---------------------------------------------------------------------------
# Pydantic model (validation + serialization)
# ---------------------------------------------------------------------------

class PurchaseOrder(BaseModel):
    """Pydantic schema for Purchase Order validation and API contracts."""

    po_id: str = Field(description="Unique purchase order identifier")
    supplier: str
    material: str
    quantity: int = Field(gt=0)
    origin: str = Field(description="Origin city/country")
    destination_plant: str
    required_delivery_date: date
    priority: Priority = Priority.MEDIUM

    model_config = {"from_attributes": True}  # Enables .model_validate(orm_obj)
