"""Mock data generator — all 7 tables.

Usage:
    python -m mock_data.generate
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from src.models.email import CarrierEmail
from src.models.erp import Priority, PurchaseOrder
from src.models.gps import GPSReading
from src.models.inventory import Inventory
from src.models.milestone import Milestone, MilestoneStatus
from src.models.sales_order import SalesOrder
from src.models.shipment import Shipment, ShipmentStatus, TransportMode

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
# Sales Orders
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
# Milestones (per shipment — SH-3001 and SH-3003 have delays)
# ---------------------------------------------------------------------------

MILESTONES = [
    # SH-3001 (delayed) — customs_cleared is 3 days late, later steps pending
    Milestone(
        shipment_id="SH-3001", milestone="order_confirmed",
        planned_time=datetime(2026, 6, 25, 8, 0),
        actual_time=datetime(2026, 6, 25, 9, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3001", milestone="picked_up",
        planned_time=datetime(2026, 6, 26, 10, 0),
        actual_time=datetime(2026, 6, 26, 14, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3001", milestone="in_transit",
        planned_time=datetime(2026, 6, 28, 6, 0),
        actual_time=datetime(2026, 6, 28, 8, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3001", milestone="customs_cleared",
        planned_time=datetime(2026, 7, 3, 12, 0),
        actual_time=None,
        status=MilestoneStatus.DELAYED,
    ),
    Milestone(
        shipment_id="SH-3001", milestone="out_for_delivery",
        planned_time=datetime(2026, 7, 13, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3001", milestone="delivered",
        planned_time=datetime(2026, 7, 15, 18, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),

    # SH-3002 (healthy) — all on schedule
    Milestone(
        shipment_id="SH-3002", milestone="order_confirmed",
        planned_time=datetime(2026, 6, 28, 6, 0),
        actual_time=datetime(2026, 6, 28, 6, 30),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3002", milestone="picked_up",
        planned_time=datetime(2026, 6, 29, 8, 0),
        actual_time=datetime(2026, 6, 29, 9, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3002", milestone="in_transit",
        planned_time=datetime(2026, 7, 1, 10, 0),
        actual_time=datetime(2026, 7, 1, 10, 30),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3002", milestone="customs_cleared",
        planned_time=datetime(2026, 7, 5, 14, 0),
        actual_time=datetime(2026, 7, 5, 15, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3002", milestone="out_for_delivery",
        planned_time=datetime(2026, 7, 9, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3002", milestone="delivered",
        planned_time=datetime(2026, 7, 10, 14, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),

    # SH-3003 (GPS anomaly) — milestones mostly on time but in_transit stalled
    Milestone(
        shipment_id="SH-3003", milestone="order_confirmed",
        planned_time=datetime(2026, 6, 22, 10, 0),
        actual_time=datetime(2026, 6, 22, 10, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3003", milestone="picked_up",
        planned_time=datetime(2026, 6, 23, 8, 0),
        actual_time=datetime(2026, 6, 23, 9, 30),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3003", milestone="in_transit",
        planned_time=datetime(2026, 6, 25, 6, 0),
        actual_time=datetime(2026, 6, 25, 7, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3003", milestone="customs_cleared",
        planned_time=datetime(2026, 7, 5, 10, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3003", milestone="out_for_delivery",
        planned_time=datetime(2026, 7, 16, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3003", milestone="delivered",
        planned_time=datetime(2026, 7, 18, 20, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),

    # SH-3004 (healthy domestic truck) — fast, on schedule
    Milestone(
        shipment_id="SH-3004", milestone="order_confirmed",
        planned_time=datetime(2026, 7, 3, 7, 0),
        actual_time=datetime(2026, 7, 3, 7, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3004", milestone="picked_up",
        planned_time=datetime(2026, 7, 3, 10, 0),
        actual_time=datetime(2026, 7, 3, 10, 30),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3004", milestone="in_transit",
        planned_time=datetime(2026, 7, 4, 6, 0),
        actual_time=datetime(2026, 7, 4, 6, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3004", milestone="out_for_delivery",
        planned_time=datetime(2026, 7, 7, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3004", milestone="delivered",
        planned_time=datetime(2026, 7, 8, 15, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),

    # SH-3005 (email warning) — in_transit completed but delayed at port
    Milestone(
        shipment_id="SH-3005", milestone="order_confirmed",
        planned_time=datetime(2026, 6, 20, 12, 0),
        actual_time=datetime(2026, 6, 20, 12, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3005", milestone="picked_up",
        planned_time=datetime(2026, 6, 21, 8, 0),
        actual_time=datetime(2026, 6, 21, 10, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3005", milestone="in_transit",
        planned_time=datetime(2026, 6, 23, 6, 0),
        actual_time=datetime(2026, 6, 23, 8, 0),
        status=MilestoneStatus.COMPLETED,
    ),
    Milestone(
        shipment_id="SH-3005", milestone="customs_cleared",
        planned_time=datetime(2026, 7, 5, 10, 0),
        actual_time=None,
        status=MilestoneStatus.DELAYED,
    ),
    Milestone(
        shipment_id="SH-3005", milestone="out_for_delivery",
        planned_time=datetime(2026, 7, 20, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
    Milestone(
        shipment_id="SH-3005", milestone="delivered",
        planned_time=datetime(2026, 7, 22, 8, 0),
        actual_time=None,
        status=MilestoneStatus.PENDING,
    ),
]

# ---------------------------------------------------------------------------
# GPS Readings (SH-3003 has a stall pattern, others normal)
# ---------------------------------------------------------------------------


def _build_gps_readings() -> list[GPSReading]:
    """Build GPS readings programmatically. 4 pings per shipment over 2 days."""
    readings = []
    base_time = datetime(2026, 7, 5, 0, 0)

    # (shipment_id, start_lat, start_lon, end_lat, end_lon, has_stall)
    routes = [
        ("SH-3001", 25.0, 55.0, 30.0, 50.0, False),       # Suez area — delayed but moving slowly
        ("SH-3002", 45.0, -30.0, 42.0, -60.0, False),      # Mid-Atlantic — healthy
        ("SH-3003", 15.0, 145.0, 15.0, 145.0, True),       # Near Guam — STALLED
        ("SH-3004", 31.0, -95.0, 35.0, -90.0, False),      # Houston→Chicago — healthy
        ("SH-3005", 1.3, 103.8, 1.3, 103.8, True),         # Singapore port — STALLED
    ]

    for ship_id, s_lat, s_lon, e_lat, e_lon, stall in routes:
        for i in range(4):
            t = base_time + timedelta(hours=i * 12)
            if stall:
                lat = round(s_lat + 0.001 * i, 4)
                lon = round(s_lon + 0.001 * i, 4)
                speed = 0.0 if i >= 1 else 5.0
                delay = i >= 1
            else:
                progress = i / 3
                lat = round(s_lat + (e_lat - s_lat) * progress, 4)
                lon = round(s_lon + (e_lon - s_lon) * progress, 4)
                speed = round(40 + i * 5, 1)
                delay = False

            readings.append(GPSReading(
                shipment_id=ship_id,
                timestamp=t,
                latitude=lat,
                longitude=lon,
                speed_kmh=speed,
                delay_indicator=delay,
            ))
    return readings


GPS_READINGS = _build_gps_readings()

# ---------------------------------------------------------------------------
# Carrier Emails (delay notifications for SH-3001 and SH-3005)
# ---------------------------------------------------------------------------

CARRIER_EMAILS = [
    CarrierEmail(
        email_id="EM-0001",
        shipment_id="SH-3001",
        **{"from": "operations@maersk.com"},
        to="procurement@company.com",
        received_at=datetime(2026, 7, 5, 14, 30),
        subject="Delay Notice - Shipment SH-3001",
        body=(
            "Dear Customer,\n\n"
            "We regret to inform you that shipment SH-3001 carrying Steel Coils "
            "from Mumbai, India is experiencing a delay of approximately 5 days "
            "due to customs inspection hold at Suez Canal. We are working to "
            "minimize the impact.\n\n"
            "Updated ETA: 2026-07-20\n\n"
            "Best regards,\nMaersk Operations Team"
        ),
        delay_days_mentioned=5,
        reason="customs inspection hold",
    ),
    CarrierEmail(
        email_id="EM-0002",
        shipment_id="SH-3005",
        **{"from": "logistics@kuehne-nagel.com"},
        to="procurement@company.com",
        received_at=datetime(2026, 7, 6, 9, 15),
        subject="URGENT: Shipment SH-3005 Disruption",
        body=(
            "ALERT: Shipment SH-3005 (Carbon Fiber Sheets, Kuehne+Nagel) is "
            "currently stalled at Port of Singapore — awaiting berth. "
            "Root cause: port congestion. Estimated delay: 4 business days. "
            "Revised delivery: 2026-07-26.\n\n"
            "Please advise on priority handling.\n\n"
            "Regards,\nKuehne+Nagel Control Tower"
        ),
        delay_days_mentioned=4,
        reason="port congestion",
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


def generate_milestones() -> list[dict]:
    return [ms.model_dump(mode="json") for ms in MILESTONES]


def generate_gps_readings() -> list[dict]:
    return [gps.model_dump(mode="json") for gps in GPS_READINGS]


def generate_emails() -> list[dict]:
    return [e.model_dump(mode="json", by_alias=True) for e in CARRIER_EMAILS]


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

    print("Generating Milestones...")
    ms_data = generate_milestones()
    write_to_file(ms_data, Path("mock_data/milestones.json"))

    print("Generating GPS Readings...")
    gps_data = generate_gps_readings()
    write_to_file(gps_data, Path("mock_data/gps_readings.json"))

    print("Generating Carrier Emails...")
    email_data = generate_emails()
    write_to_file(email_data, Path("mock_data/carrier_emails.json"))

    # --- Summary ---
    print("\n=== Purchase Orders ===")
    for po in PURCHASE_ORDERS:
        days = (po.required_delivery_date - date(2026, 7, 7)).days
        print(f"  {po.po_id} | {po.material:<22} | {po.priority.value:<8} | Due in {days:>2}d")

    print("\n=== Shipments ===")
    for sh in SHIPMENTS:
        print(f"  {sh.shipment_id} → {sh.po_id} | {sh.carrier:<16} | {sh.mode.value:<6} | {sh.status.value}")

    print("\n=== Inventory ===")
    for inv in INVENTORY:
        flag = " ⚠ LOW" if inv.below_safety_stock else ""
        print(
            f"  {inv.plant:<16} | {inv.material:<22} | "
            f"stock={inv.current_stock:>5} | dos={inv.days_of_supply:>5}d{flag}"
        )

    print("\n=== Sales Orders ===")
    for so in SALES_ORDERS:
        days = (so.delivery_commitment_date - date(2026, 7, 7)).days
        print(f"  {so.so_id} | {so.customer:<28} | {so.material:<22} | Commit in {days:>2}d")

    print("\n=== Milestones ===")
    delayed_ms = [m for m in MILESTONES if m.status == MilestoneStatus.DELAYED]
    print(f"  Total: {len(MILESTONES)} milestones across {len(SHIPMENTS)} shipments")
    print(f"  Delayed: {len(delayed_ms)} ({', '.join(m.shipment_id + '/' + m.milestone for m in delayed_ms)})")

    print("\n=== GPS Readings ===")
    stalls = [g for g in GPS_READINGS if g.delay_indicator]
    stall_ids = ", ".join({g.shipment_id for g in stalls})
    print(f"  Total: {len(GPS_READINGS)} readings, Stalls: {len(stalls)} ({stall_ids})")

    print("\n=== Carrier Emails ===")
    for e in CARRIER_EMAILS:
        print(f"  {e.email_id} | {e.shipment_id} | {e.reason} | +{e.delay_days_mentioned}d delay")

    print(
        f"\nTotal: {len(po_data)} POs, {len(sh_data)} shipments, {len(inv_data)} inventory, "
        f"{len(so_data)} SOs, {len(ms_data)} milestones, {len(gps_data)} GPS, {len(email_data)} emails."
    )


if __name__ == "__main__":
    main()
