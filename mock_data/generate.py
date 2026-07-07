"""Mock data generator — Purchase Orders.

Generates 5 curated PO records with deliberate variety:
    - PO-1001: Critical priority, tight deadline   (will become a delayed shipment)
    - PO-1002: Medium priority, comfortable buffer  (healthy shipment)
    - PO-1003: High priority, overseas supplier     (GPS anomaly candidate)
    - PO-1004: Low priority, domestic               (healthy shipment)
    - PO-1005: Critical priority, long transit       (email warning candidate)

Each record is validated through the Pydantic model before output.

Usage:
    python -m mock_data.generate
"""

import json
from pathlib import Path
from datetime import date, datetime

from src.models.erp import Priority, PurchaseOrder

# ---------------------------------------------------------------------------
# Hand-curated PO records
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

from src.models.shipment import Shipment, ShipmentStatus, TransportMode

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


def generate_purchase_orders() -> list[dict]:
    """Validate and serialize all PO records."""
    return [po.model_dump(mode="json") for po in PURCHASE_ORDERS]

def generate_shipments() -> list[dict]:
    """Validate and serialize all Shipment records."""
    return [s.model_dump(mode="json") for s in SHIPMENTS]

def write_to_file(data: list[dict], filepath: Path) -> None:
    """Write records as pretty-printed JSON."""
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
    print(f"\nTotal: {len(po_data)} POs, {len(sh_data)} shipments.")


if __name__ == "__main__":
    main()
