"""Seed the database with mock Purchase Orders.

Reads from mock_data/purchase_orders.json, validates each record
through the Pydantic model, and inserts into SQLite via SQLAlchemy.

Usage:
    python -m mock_data.seed_db
"""

import asyncio
import json
from datetime import date
from pathlib import Path

from src.db import async_session, create_tables
from src.models.erp import PurchaseOrder, PurchaseOrderTable


async def seed_purchase_orders() -> None:
    """Load PO records from JSON, validate, and insert into the database."""

    # 1. Read the generated JSON
    json_path = Path("mock_data/purchase_orders.json")
    if not json_path.exists():
        print("ERROR: mock_data/purchase_orders.json not found.")
        print("Run `python -m mock_data.generate` first.")
        return

    raw_data = json.loads(json_path.read_text())
    print(f"Read {len(raw_data)} records from {json_path}")

    # 2. Validate each record through Pydantic
    validated = []
    for record in raw_data:
        po = PurchaseOrder.model_validate(record)
        validated.append(po)
        print(f"  Validated: {po.po_id} — {po.material}")

    # 3. Create tables (idempotent — safe to call multiple times)
    await create_tables()
    print("\nDatabase tables created (if not existing).")

    # 4. Insert into database
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
            await session.merge(orm_obj)  # merge = upsert (insert or update)

        await session.commit()
        print(f"\nInserted/updated {len(validated)} purchase orders into the database.")

    # 5. Verify by reading back
    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(PurchaseOrderTable).order_by(PurchaseOrderTable.po_id)
        )
        rows = result.scalars().all()

        print(f"\n=== Verification: {len(rows)} rows in purchase_orders table ===")
        for row in rows:
            print(f"  {row}")


def main() -> None:
    asyncio.run(seed_purchase_orders())


if __name__ == "__main__":
    main()
