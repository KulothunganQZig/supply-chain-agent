"""Seed the database with all mock data.

Usage:
    python -m mock_data.seed_db
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from src.db import async_session, create_tables
from src.models.email import CarrierEmail, CarrierEmailTable
from src.models.erp import PurchaseOrder, PurchaseOrderTable
from src.models.gps import GPSReading, GPSReadingTable
from src.models.inventory import Inventory, InventoryTable
from src.models.milestone import Milestone, MilestoneTable
from src.models.sales_order import SalesOrder, SalesOrderTable
from src.models.shipment import Shipment, ShipmentTable


async def seed_table(
    json_filename: str,
    pydantic_cls: type,
    orm_cls: type,
    label: str,
    to_orm: callable,
    order_by=None,
) -> None:
    """Generic seeder: read JSON → validate → upsert → verify."""
    json_path = Path(f"mock_data/{json_filename}")
    if not json_path.exists():
        print(f"ERROR: {json_path} not found. Run generate first.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"\nRead {len(raw_data)} {label} from {json_path}")

    validated = [pydantic_cls.model_validate(r) for r in raw_data]
    for v in validated:
        print(f"  Validated: {v}")

    async with async_session() as session:
        for v in validated:
            await session.merge(to_orm(v))
        await session.commit()
        print(f"Inserted/updated {len(validated)} {label}.")

    if order_by is not None:
        async with async_session() as session:
            result = await session.execute(select(orm_cls).order_by(order_by))
            rows = result.scalars().all()
            print(f"\n=== Verification: {len(rows)} rows in {orm_cls.__tablename__} ===")
            for row in rows:
                print(f"  {row}")


async def seed_all() -> None:
    await create_tables()
    print("Database tables created (if not existing).")

    # 1. Purchase Orders
    await seed_table(
        "purchase_orders.json", PurchaseOrder, PurchaseOrderTable,
        "purchase orders",
        lambda po: PurchaseOrderTable(
            po_id=po.po_id, supplier=po.supplier, material=po.material,
            quantity=po.quantity, origin=po.origin,
            destination_plant=po.destination_plant,
            required_delivery_date=po.required_delivery_date,
            priority=po.priority.value,
        ),
        order_by=PurchaseOrderTable.po_id,
    )

    # 2. Shipments
    await seed_table(
        "shipments.json", Shipment, ShipmentTable,
        "shipments",
        lambda s: ShipmentTable(
            shipment_id=s.shipment_id, po_id=s.po_id, carrier=s.carrier,
            mode=s.mode.value, origin=s.origin, destination=s.destination,
            planned_departure=s.planned_departure,
            planned_arrival=s.planned_arrival,
            current_location=s.current_location, status=s.status.value,
        ),
        order_by=ShipmentTable.shipment_id,
    )

    # 3. Inventory
    await seed_table(
        "inventory.json", Inventory, InventoryTable,
        "inventory records",
        lambda inv: InventoryTable(
            plant=inv.plant, material=inv.material,
            current_stock=inv.current_stock, safety_stock=inv.safety_stock,
            daily_consumption=inv.daily_consumption,
        ),
        order_by=InventoryTable.plant,
    )

    # 4. Sales Orders
    await seed_table(
        "sales_orders.json", SalesOrder, SalesOrderTable,
        "sales orders",
        lambda so: SalesOrderTable(
            so_id=so.so_id, customer=so.customer, material=so.material,
            quantity=so.quantity,
            delivery_commitment_date=so.delivery_commitment_date,
            priority=so.priority.value,
        ),
        order_by=SalesOrderTable.so_id,
    )

    # 5. Milestones
    await seed_table(
        "milestones.json", Milestone, MilestoneTable,
        "milestones",
        lambda ms: MilestoneTable(
            shipment_id=ms.shipment_id, milestone=ms.milestone,
            planned_time=ms.planned_time, actual_time=ms.actual_time,
            status=ms.status.value,
        ),
        order_by=MilestoneTable.shipment_id,
    )

    # 6. GPS Readings
    await seed_table(
        "gps_readings.json", GPSReading, GPSReadingTable,
        "GPS readings",
        lambda g: GPSReadingTable(
            shipment_id=g.shipment_id, timestamp=g.timestamp,
            latitude=g.latitude, longitude=g.longitude,
            speed_kmh=g.speed_kmh, delay_indicator=g.delay_indicator,
        ),
        order_by=GPSReadingTable.shipment_id,
    )

    # 7. Carrier Emails
    await seed_table(
        "carrier_emails.json", CarrierEmail, CarrierEmailTable,
        "carrier emails",
        lambda e: CarrierEmailTable(
            email_id=e.email_id, shipment_id=e.shipment_id,
            sender=e.sender, recipient=e.recipient,
            received_at=e.received_at, subject=e.subject, body=e.body,
            delay_days_mentioned=e.delay_days_mentioned, reason=e.reason,
        ),
        order_by=CarrierEmailTable.email_id,
    )


def main() -> None:
    asyncio.run(seed_all())


if __name__ == "__main__":
    main()
