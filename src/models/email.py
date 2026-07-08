"""Carrier Email domain models — SQLAlchemy table + Pydantic schema."""

from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class CarrierEmailTable(Base):
    __tablename__ = "carrier_emails"

    email_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("shipments.shipment_id"))
    sender: Mapped[str] = mapped_column(String(200))
    recipient: Mapped[str] = mapped_column(String(200))
    received_at: Mapped[datetime] = mapped_column(DateTime)
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    delay_days_mentioned: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(200), default="")

    def __repr__(self) -> str:
        return (
            f"<Email(id={self.email_id!r}, shipment={self.shipment_id!r}, "
            f"delay={self.delay_days_mentioned}d, reason={self.reason!r})>"
        )


class CarrierEmail(BaseModel):
    email_id: str
    shipment_id: str
    sender: str = Field(alias="from", default="")
    recipient: str = Field(alias="to", default="")
    received_at: datetime
    subject: str
    body: str
    delay_days_mentioned: int = 0
    reason: str = ""

    model_config = {"from_attributes": True, "populate_by_name": True}
