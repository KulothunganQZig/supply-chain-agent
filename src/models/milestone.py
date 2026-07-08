"""Milestone domain models — SQLAlchemy table + Pydantic schema."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class MilestoneStatus(StrEnum):
    COMPLETED = "completed"
    PENDING = "pending"
    DELAYED = "delayed"


class MilestoneTable(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("shipments.shipment_id"))
    milestone: Mapped[str] = mapped_column(String(50))
    planned_time: Mapped[datetime] = mapped_column(DateTime)
    actual_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    def __repr__(self) -> str:
        return (
            f"<Milestone(shipment={self.shipment_id!r}, step={self.milestone!r}, "
            f"status={self.status!r})>"
        )


class Milestone(BaseModel):
    shipment_id: str
    milestone: str
    planned_time: datetime
    actual_time: datetime | None = None
    status: MilestoneStatus = MilestoneStatus.PENDING

    model_config = {"from_attributes": True}
