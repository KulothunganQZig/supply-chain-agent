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
from datetime import date
from pathlib import Path

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


def generate_purchase_orders() -> list[dict]:
    """Validate and serialize all PO records."""
    return [po.model_dump(mode="json") for po in PURCHASE_ORDERS]


def write_to_file(data: list[dict], filepath: Path) -> None:
    """Write records as pretty-printed JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(data, indent=2, default=str))
    print(f"  {filepath} — {len(data)} records")


def main() -> None:
    print("Generating Purchase Orders...")
    po_data = generate_purchase_orders()

    output_path = Path("mock_data/purchase_orders.json")
    write_to_file(po_data, output_path)

    print("\n=== Purchase Orders Summary ===")
    for po in PURCHASE_ORDERS:
        days_until_due = (po.required_delivery_date - date(2026, 7, 7)).days
        print(
            f"  {po.po_id} | {po.material:<22} | {po.supplier:<16} "
            f"| {po.priority.value:<8} | Due in {days_until_due:>2}d"
        )
    print(f"\nTotal: {len(po_data)} purchase orders generated.")


if __name__ == "__main__":
    main()
