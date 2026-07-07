"""Shipment domain models — SQLAlchemy table + Pydantic schema."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class TransportMode(str, Enum):
    TRUCK = "truck"
    RAIL = "rail"
    OCEAN = "ocean"
    AIR = "air"


class ShipmentStatus(str, Enum):
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    DELIVERED = "delivered"


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class ShipmentTable(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    po_id: Mapped[str] = mapped_column(String(20), ForeignKey("purchase_orders.po_id"))
    carrier: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    planned_departure: Mapped[datetime] = mapped_column(DateTime)
    planned_arrival: Mapped[datetime] = mapped_column(DateTime)
    current_location: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="planned")

    def __repr__(self) -> str:
        return (
            f"<Shipment(id={self.shipment_id!r}, po={self.po_id!r}, "
            f"carrier={self.carrier!r}, status={self.status!r})>"
        )


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class Shipment(BaseModel):
    shipment_id: str
    po_id: str
    carrier: str
    mode: TransportMode
    origin: str
    destination: str
    planned_departure: datetime
    planned_arrival: datetime
    current_location: str = ""
    status: ShipmentStatus = ShipmentStatus.PLANNED

    model_config = {"from_attributes": True}