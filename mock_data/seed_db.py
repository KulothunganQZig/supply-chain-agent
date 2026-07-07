"""Seed the database with mock data.

Usage:
    python -m mock_data.seed_db
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from src.db import async_session, create_tables
from src.models.erp import PurchaseOrder, PurchaseOrderTable
from src.models.shipment import Shipment, ShipmentTable
from src.models.inventory import Inventory, InventoryTable
from src.models.sales_order import SalesOrder, SalesOrderTable


async def seed_purchase_orders() -> None:
    json_path = Path("mock_data/purchase_orders.json")
    if not json_path.exists():
        print("ERROR: mock_data/purchase_orders.json not found. Run generate first.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"Read {len(raw_data)} records from {json_path}")

    validated = []
    for record in raw_data:
        po = PurchaseOrder.model_validate(record)
        validated.append(po)
        print(f"  Validated: {po.po_id} — {po.material}")

    await create_tables()
    print("\nDatabase tables created (if not existing).")

    async with async_session() as session:
        for po in validated:
            orm_obj = PurchaseOrderTable(
                po_id=po.po_id,
                supplier=po.supplier,
                material=po.material,
                quantity=po.quantity,
                origin=po.origin,
                destination_plant=po.destination_plant,
                required_delivery_date=po.required_delivery_date,
                priority=po.priority.value,
            )
            await session.merge(orm_obj)
        await session.commit()
        print(f"\nInserted/updated {len(validated)} purchase orders.")

    async with async_session() as session:
        result = await session.execute(
            select(PurchaseOrderTable).order_by(PurchaseOrderTable.po_id)
        )
        rows = result.scalars().all()
        print(f"\n=== Verification: {len(rows)} rows in purchase_orders table ===")
        for row in rows:
            print(f"  {row}")

    await seed_shipments()
    await seed_inventory()
    await seed_sales_orders()


async def seed_shipments() -> None:
    json_path = Path("mock_data/shipments.json")
    if not json_path.exists():
        print("ERROR: mock_data/shipments.json not found.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"\nRead {len(raw_data)} shipments from {json_path}")

    validated = [Shipment.model_validate(r) for r in raw_data]
    for s in validated:
        print(f"  Validated: {s.shipment_id} → {s.po_id}")

    async with async_session() as session:
        for s in validated:
            orm_obj = ShipmentTable(
                shipment_id=s.shipment_id,
                po_id=s.po_id,
                carrier=s.carrier,
                mode=s.mode.value,
                origin=s.origin,
                destination=s.destination,
                planned_departure=s.planned_departure,
                planned_arrival=s.planned_arrival,
                current_location=s.current_location,
                status=s.status.value,
            )
            await session.merge(orm_obj)
        await session.commit()
        print(f"Inserted/updated {len(validated)} shipments.")

    async with async_session() as session:
        result = await session.execute(
            select(ShipmentTable).order_by(ShipmentTable.shipment_id)
        )
        rows = result.scalars().all()
        print(f"\n=== Verification: {len(rows)} rows in shipments table ===")
        for row in rows:
            print(f"  {row}")


async def seed_inventory() -> None:
    json_path = Path("mock_data/inventory.json")
    if not json_path.exists():
        print("ERROR: mock_data/inventory.json not found.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"\nRead {len(raw_data)} inventory records from {json_path}")

    validated = [Inventory.model_validate(r) for r in raw_data]
    for inv in validated:
        print(f"  Validated: {inv.plant} — {inv.material} (dos={inv.days_of_supply}d)")

    async with async_session() as session:
        for inv in validated:
            orm_obj = InventoryTable(
                plant=inv.plant,
                material=inv.material,
                current_stock=inv.current_stock,
                safety_stock=inv.safety_stock,
                daily_consumption=inv.daily_consumption,
            )
            await session.merge(orm_obj)
        await session.commit()
        print(f"Inserted/updated {len(validated)} inventory records.")

    async with async_session() as session:
        result = await session.execute(
            select(InventoryTable).order_by(InventoryTable.plant)
        )
        rows = result.scalars().all()
        print(f"\n=== Verification: {len(rows)} rows in inventory table ===")
        for row in rows:
            print(f"  {row}")


async def seed_sales_orders() -> None:
    json_path = Path("mock_data/sales_orders.json")
    if not json_path.exists():
        print("ERROR: mock_data/sales_orders.json not found.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"\nRead {len(raw_data)} sales orders from {json_path}")

    validated = [SalesOrder.model_validate(r) for r in raw_data]
    for so in validated:
        print(f"  Validated: {so.so_id} — {so.customer} ({so.material})")

    async with async_session() as session:
        for so in validated:
            orm_obj = SalesOrderTable(
                so_id=so.so_id,
                customer=so.customer,
                material=so.material,
                quantity=so.quantity,
                delivery_commitment_date=so.delivery_commitment_date,
                priority=so.priority.value,
            )
            await session.merge(orm_obj)
        await session.commit()
        print(f"Inserted/updated {len(validated)} sales orders.")

    async with async_session() as session:
        result = await session.execute(
            select(SalesOrderTable).order_by(SalesOrderTable.so_id)
        )
        rows = result.scalars().all()
        print(f"\n=== Verification: {len(rows)} rows in sales_orders table ===")
        for row in rows:
            print(f"  {row}")


def main() -> None:
    asyncio.run(seed_purchase_orders())


if __name__ == "__main__":
    main()