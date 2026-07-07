"""Mock data generator — Purchase Orders, Shipments, Inventory, Sales Orders.

Usage:
    python -m mock_data.generate
"""

import json
from datetime import date, datetime
from pathlib import Path

from src.models.erp import Priority, PurchaseOrder
from src.models.shipment import Shipment, ShipmentStatus, TransportMode
from src.models.inventory import Inventory
from src.models.sales_order import SalesOrder

# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

PURCHASE_ORDERS = [
    PurchaseOrder(
        po_id="PO-1001",
        supplier="Tata Steel",
        material="Steel Coils",
        quantity=500,
        origin="Mumbai, India",
        destination_plant="Plant-Detroit",
        required_delivery_date=date(2026, 7, 15),
        priority=Priority.CRITICAL,
    ),
    PurchaseOrder(
        po_id="PO-1002",
        supplier="BASF",
        material="Polymer Resin",
        quantity=1200,
        origin="Ludwigshafen, Germany",
        destination_plant="Plant-Chicago",
        required_delivery_date=date(2026, 8, 1),
        priority=Priority.MEDIUM,
    ),
    PurchaseOrder(
        po_id="PO-1003",
        supplier="Samsung SDI",
        material="Battery Cells",
        quantity=300,
        origin="Ulsan, South Korea",
        destination_plant="Plant-Houston",
        required_delivery_date=date(2026, 7, 20),
        priority=Priority.HIGH,
    ),
    PurchaseOrder(
        po_id="PO-1004",
        supplier="Dow Chemical",
        material="Adhesive Compound",
        quantity=800,
        origin="Houston, USA",
        destination_plant="Plant-Chicago",
        required_delivery_date=date(2026, 8, 10),
        priority=Priority.LOW,
    ),
    PurchaseOrder(
        po_id="PO-1005",
        supplier="Sinopec",
        material="Carbon Fiber Sheets",
        quantity=200,
        origin="Beijing, China",
        destination_plant="Plant-Munich",
        required_delivery_date=date(2026, 7, 25),
        priority=Priority.CRITICAL,
    ),
]

# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------

SHIPMENTS = [
    Shipment(
        shipment_id="SH-3001",
        po_id="PO-1001",
        carrier="Maersk",
        mode=TransportMode.OCEAN,
        origin="Mumbai, India",
        destination="Detroit, USA",
        planned_departure=datetime(2026, 6, 25, 8, 0),
        planned_arrival=datetime(2026, 7, 15, 18, 0),
        current_location="Held at customs — Suez Canal",
        status=ShipmentStatus.DELAYED,
    ),
    Shipment(
        shipment_id="SH-3002",
        po_id="PO-1002",
        carrier="DB Schenker",
        mode=TransportMode.RAIL,
        origin="Ludwigshafen, Germany",
        destination="Chicago, USA",
        planned_departure=datetime(2026, 6, 28, 6, 0),
        planned_arrival=datetime(2026, 7, 10, 14, 0),
        current_location="En route — mid-Atlantic",
        status=ShipmentStatus.IN_TRANSIT,
    ),
    Shipment(
        shipment_id="SH-3003",
        po_id="PO-1003",
        carrier="DHL Global",
        mode=TransportMode.OCEAN,
        origin="Ulsan, South Korea",
        destination="Houston, USA",
        planned_departure=datetime(2026, 6, 22, 10, 0),
        planned_arrival=datetime(2026, 7, 18, 20, 0),
        current_location="Near Guam — GPS stall detected",
        status=ShipmentStatus.IN_TRANSIT,
    ),
    Shipment(
        shipment_id="SH-3004",
        po_id="PO-1004",
        carrier="FedEx Freight",
        mode=TransportMode.TRUCK,
        origin="Houston, USA",
        destination="Chicago, USA",
        planned_departure=datetime(2026, 7, 3, 7, 0),
        planned_arrival=datetime(2026, 7, 8, 15, 0),
        current_location="En route — near Dallas, TX",
        status=ShipmentStatus.IN_TRANSIT,
    ),
    Shipment(
        shipment_id="SH-3005",
        po_id="PO-1005",
        carrier="Kuehne+Nagel",
        mode=TransportMode.OCEAN,
        origin="Beijing, China",
        destination="Munich, Germany",
        planned_departure=datetime(2026, 6, 20, 12, 0),
        planned_arrival=datetime(2026, 7, 22, 8, 0),
        current_location="Port of Singapore — awaiting berth",
        status=ShipmentStatus.IN_TRANSIT,
    ),
]

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

INVENTORY = [
    Inventory(
        plant="Plant-Detroit",
        material="Steel Coils",
        current_stock=150,
        safety_stock=500,
        daily_consumption=80.0,
    ),
    Inventory(
        plant="Plant-Chicago",
        material="Polymer Resin",
        current_stock=3000,
        safety_stock=1000,
        daily_consumption=100.0,
    ),
    Inventory(
        plant="Plant-Houston",
        material="Battery Cells",
        current_stock=90,
        safety_stock=200,
        daily_consumption=30.0,
    ),
    Inventory(
        plant="Plant-Chicago",
        material="Adhesive Compound",
        current_stock=2500,
        safety_stock=600,
        daily_consumption=50.0,
    ),
    Inventory(
        plant="Plant-Munich",
        material="Carbon Fiber Sheets",
        current_stock=60,
        safety_stock=150,
        daily_consumption=25.0,
    ),
]

# ---------------------------------------------------------------------------
# Sales Orders (demand side — links materials to customers)
# ---------------------------------------------------------------------------

SALES_ORDERS = [
    SalesOrder(
        so_id="SO-2001",
        customer="AutoCorp Inc.",
        material="Steel Coils",
        quantity=400,
        delivery_commitment_date=date(2026, 7, 18),
        priority=Priority.CRITICAL,
    ),
    SalesOrder(
        so_id="SO-2002",
        customer="BuildTech Solutions",
        material="Polymer Resin",
        quantity=600,
        delivery_commitment_date=date(2026, 8, 5),
        priority=Priority.MEDIUM,
    ),
    SalesOrder(
        so_id="SO-2003",
        customer="NextGen Motors",
        material="Battery Cells",
        quantity=250,
        delivery_commitment_date=date(2026, 7, 22),
        priority=Priority.HIGH,
    ),
    SalesOrder(
        so_id="SO-2004",
        customer="GlobalParts Ltd.",
        material="Adhesive Compound",
        quantity=500,
        delivery_commitment_date=date(2026, 8, 15),
        priority=Priority.LOW,
    ),
    SalesOrder(
        so_id="SO-2005",
        customer="Precision Manufacturing Co.",
        material="Carbon Fiber Sheets",
        quantity=150,
        delivery_commitment_date=date(2026, 7, 28),
        priority=Priority.CRITICAL,
    ),
    SalesOrder(
        so_id="SO-2006",
        customer="Atlas Industries",
        material="Steel Coils",
        quantity=300,
        delivery_commitment_date=date(2026, 7, 25),
        priority=Priority.HIGH,
    ),
]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_purchase_orders() -> list[dict]:
    return [po.model_dump(mode="json") for po in PURCHASE_ORDERS]


def generate_shipments() -> list[dict]:
    return [s.model_dump(mode="json") for s in SHIPMENTS]


def generate_inventory() -> list[dict]:
    return [inv.model_dump(mode="json") for inv in INVENTORY]


def generate_sales_orders() -> list[dict]:
    return [so.model_dump(mode="json") for so in SALES_ORDERS]


def write_to_file(data: list[dict], filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(data, indent=2, default=str))
    print(f"  {filepath} — {len(data)} records")


def main() -> None:
    print("Generating Purchase Orders...")
    po_data = generate_purchase_orders()
    write_to_file(po_data, Path("mock_data/purchase_orders.json"))

    print("Generating Shipments...")
    sh_data = generate_shipments()
    write_to_file(sh_data, Path("mock_data/shipments.json"))

    print("Generating Inventory...")
    inv_data = generate_inventory()
    write_to_file(inv_data, Path("mock_data/inventory.json"))

    print("Generating Sales Orders...")
    so_data = generate_sales_orders()
    write_to_file(so_data, Path("mock_data/sales_orders.json"))

    print("\n=== Summary ===")
    for po in PURCHASE_ORDERS:
        days_until_due = (po.required_delivery_date - date(2026, 7, 7)).days
        print(
            f"  {po.po_id} | {po.material:<22} | {po.priority.value:<8} | Due in {days_until_due:>2}d"
        )

    print()
    for sh in SHIPMENTS:
        print(
            f"  {sh.shipment_id} → {sh.po_id} | {sh.carrier:<16} | {sh.mode.value:<6} | {sh.status.value}"
        )

    print()
    for inv in INVENTORY:
        flag = " ⚠ LOW" if inv.below_safety_stock else ""
        print(
            f"  {inv.plant:<16} | {inv.material:<22} | "
            f"stock={inv.current_stock:>5} | dos={inv.days_of_supply:>5}d{flag}"
        )

    print()
    for so in SALES_ORDERS:
        days_until_commit = (so.delivery_commitment_date - date(2026, 7, 7)).days
        print(
            f"  {so.so_id} | {so.customer:<28} | {so.material:<22} | {so.priority.value:<8} | Commit in {days_until_commit:>2}d"
        )

    print(
        f"\nTotal: {len(po_data)} POs, {len(sh_data)} shipments, "
        f"{len(inv_data)} inventory, {len(so_data)} sales orders."
    )


if __name__ == "__main__":
    main()