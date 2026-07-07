"""ERP domain models — Purchase Orders, Sales Orders, Inventory."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PurchaseOrder(BaseModel):
    po_id: str = Field(description="Unique purchase order identifier")
    supplier: str
    material: str
    quantity: int
    origin: str = Field(description="Origin city/country")
    destination_plant: str
    required_delivery_date: date
    priority: Priority = Priority.MEDIUM


class SalesOrder(BaseModel):
    so_id: str = Field(description="Unique sales order identifier")
    customer: str
    material: str
    quantity: int
    delivery_commitment_date: date
    priority: Priority = Priority.MEDIUM


class InventoryRecord(BaseModel):
    plant: str
    material: str
    current_stock: int
    safety_stock: int
    daily_consumption: float

    @property
    def days_of_supply(self) -> float:
        """Calculate how many days current stock covers."""
        if self.daily_consumption <= 0:
            return float("inf")
        return self.current_stock / self.daily_consumption

    @property
    def below_safety_stock(self) -> bool:
        return self.current_stock < self.safety_stock
