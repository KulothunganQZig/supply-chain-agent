"""Inventory domain models — SQLAlchemy table + Pydantic schema."""

from pydantic import BaseModel, Field
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class InventoryTable(Base):
    """inventory table — one row per plant-material combination."""

    __tablename__ = "inventory"

    plant: Mapped[str] = mapped_column(String(100), primary_key=True)
    material: Mapped[str] = mapped_column(String(100), primary_key=True)
    current_stock: Mapped[int] = mapped_column(Integer)
    safety_stock: Mapped[int] = mapped_column(Integer)
    daily_consumption: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        dos = round(self.current_stock / self.daily_consumption, 1) if self.daily_consumption > 0 else float("inf")
        return (
            f"<Inventory(plant={self.plant!r}, material={self.material!r}, "
            f"stock={self.current_stock}, dos={dos}d)>"
        )


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class Inventory(BaseModel):
    plant: str
    material: str
    current_stock: int = Field(ge=0)
    safety_stock: int = Field(ge=0)
    daily_consumption: float = Field(ge=0)

    @property
    def days_of_supply(self) -> float:
        if self.daily_consumption <= 0:
            return float("inf")
        return round(self.current_stock / self.daily_consumption, 1)

    @property
    def below_safety_stock(self) -> bool:
        return self.current_stock < self.safety_stock

    model_config = {"from_attributes": True}