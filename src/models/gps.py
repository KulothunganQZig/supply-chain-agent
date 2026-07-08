"""GPS Tracking domain models — SQLAlchemy table + Pydantic schema."""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class GPSReadingTable(Base):
    __tablename__ = "gps_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("shipments.shipment_id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    speed_kmh: Mapped[float] = mapped_column(Float)
    delay_indicator: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        flag = " ⚠ STALL" if self.delay_indicator else ""
        return (
            f"<GPS(shipment={self.shipment_id!r}, speed={self.speed_kmh}km/h{flag})>"
        )


class GPSReading(BaseModel):
    shipment_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float
    delay_indicator: bool = False

    model_config = {"from_attributes": True}
