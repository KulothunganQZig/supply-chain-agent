"""Shipment, milestone, and GPS tracking models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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
    CANCELLED = "cancelled"


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


class MilestoneStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    DELAYED = "delayed"
    SKIPPED = "skipped"


class Milestone(BaseModel):
    shipment_id: str
    milestone: str = Field(description="e.g. 'picked_up', 'customs_cleared', 'departed_port'")
    timestamp: datetime
    status: MilestoneStatus


class GPSReading(BaseModel):
    shipment_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float
    delay_indicator: bool = False
