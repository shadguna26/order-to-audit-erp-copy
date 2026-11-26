import pytest
from decimal import Decimal
from datetime import date
from app.models.master import Product, BOM, RawMaterial, Supplier
from app.models.stock import StockItemType, StockLocationType
from app.services.ledger_service import get_item_stock_balance

def test_benchmark_steps_2_3_8_production_run(client, db):
    """
    BENCHMARK SCENARIO:
    (1) Purchase 60 kg flour @ Rs 45/kg.
    (2) Production run issuing 40 kg flour, 10.5 L oil, 1.2 kg spice.
    (3) Actual output 188 packets, 6 pouches damaged, 9 cartons used.
    (8) Add labour Rs 1,200 and gas/power Rs 600 to the run; show cost per packet.

    EXPECTED OUTCOMES:
    - Flour stock: 120 kg (120,000 g)
    - Oil stock: 19.5 L (19,500 ml)
    - Pouches stock: 306 pcs (500 opening - 194 consumed)
    - Finished Murukku 200g: 238 packets (50 opening + 188 output)
    - Yield variance: 188 vs 200 = -6% (Flagged)
    - Oil variance: 10.5 L vs 10 L = +5% (Flagged)
    - Oil rupee variance: 0.5 L extra @ Rs 140/L = Rs 70 (7,000 paise)
    """
    from tests.conftest import otp_login
    prod_token = otp_login(client, "+919000000005")["access_token"]
    headers = {"Authorization": f"Bearer {prod_token}"}

    # Step 1: Purchase 60 kg flour @ Rs 45/kg
    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()
    oil = db.query(RawMaterial).filter(RawMaterial.code == "RM-OIL").first()
    spice = db.query(RawMaterial).filter(RawMaterial.code == "RM-SPICE").first()
    pouch = db.query(RawMaterial).filter(RawMaterial.code == "PKG-POUCH-200G").first()
    carton = db.query(RawMaterial).filter(RawMaterial.code == "PKG-CARTON-20").first()
    murukku = db.query(Product).filter(Product.code == "FG-MRK-200G").first()
    bom = db.query(BOM).filter(BOM.product_id == murukku.id).first()
    supplier = db.query(Supplier).first()

    p_res = client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": supplier.id,
            "invoice_date": str(date.today()),
            "items": [{"raw_material_id": flour.id, "input_qty": 60.0, "input_unit": "kg", "rate_paise_per_unit": 4500}]
        },
        headers=headers
    )
    assert p_res.status_code == 201

    # Check BOM Pre-fill API
    prefill_res = client.get(f"/api/v1/production/prefill/{bom.id}?batches=1", headers=headers)
    assert prefill_res.status_code == 200
    prefill_data = prefill_res.json()
    assert prefill_data["planned_output_packets"] == 200

    # Step 2 & 3: Production Run
    # Pouches consumed = 188 good + 6 damaged = 194
    # Cartons used = 9
    run_payload = {
        "product_id": murukku.id,
        "bom_id": bom.id,
        "planned_batches": 1,
        "actual_good_output_packets": 188,
        "actual_damaged_pouches": 6,
        "actual_cartons_used": 9,
        "issued_items": [
            {"raw_material_id": flour.id, "actual_qty_base": 40000.0}, # 40 kg flour
            {"raw_material_id": oil.id, "actual_qty_base": 10500.0},   # 10.5 L oil (standard 10 L)
            {"raw_material_id": spice.id, "actual_qty_base": 1200.0},  # 1.2 kg spice
            {"raw_material_id": pouch.id, "actual_qty_base": 194.0},   # 188 good + 6 damaged
            {"raw_material_id": carton.id, "actual_qty_base": 9.0},    # 9 cartons
        ],
        "overheads": []
    }

    run_res = client.post("/api/v1/production/runs", json=run_payload, headers=headers)
    assert run_res.status_code == 201, run_res.text
    run_data = run_res.json()
    run_id = run_data["id"]

    # Verify Variances
    assert Decimal(run_data["yield_variance_pct"]) == Decimal("-6.00")
    assert run_data["is_yield_flagged"] is True

    oil_item = next(i for i in run_data["items"] if i["raw_material_id"] == oil.id)
    assert Decimal(oil_item["variance_pct"]) == Decimal("5.00")
    assert oil_item["is_flagged"] is True
    assert oil_item["variance_cost_paise"] == 7000 # 500 ml * 14 paise/ml = Rs 70 (7,000 paise)

    flour_item = next(i for i in run_data["items"] if i["raw_material_id"] == flour.id)
    assert Decimal(flour_item["variance_pct"]) == Decimal("0.00")
    assert flour_item["is_flagged"] is False

    # Verify Stock Balances in Stock Ledger
    # Flour: 160 kg - 40 kg = 120 kg (120,000 g)
    flour_bal = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id)
    assert flour_bal == Decimal("120000.0000")

    # Oil: 30 L - 10.5 L = 19.5 L (19,500 ml)
    oil_bal = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, oil.id)
    assert oil_bal == Decimal("19500.0000")

    # Pouches: 500 - 194 = 306 pcs
    pouch_bal = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, pouch.id)
    assert pouch_bal == Decimal("306.0000")

    # Finished Goods: 50 opening + 188 output = 238 packets
    fg_bal = get_item_stock_balance(db, StockItemType.FINISHED_GOODS, murukku.id)
    assert fg_bal == Decimal("238.0000")

    # Step 8: Add Overheads (Labour Rs 1,200 and Gas/Power Rs 600)
    overhead_payload = [
        {"overhead_type": "labour", "amount_paise": 120000, "notes": "Shift wages for 2 operators"},
        {"overhead_type": "gas_power", "amount_paise": 60000, "notes": "Commercial LPG cylinder consumption"}
    ]
    oh_res = client.post(f"/api/v1/production/runs/{run_id}/overheads", json=overhead_payload, headers=headers)
    assert oh_res.status_code == 200
    oh_data = oh_res.json()

    assert oh_data["total_overhead_cost_paise"] == 180000 # Rs 1,800
    # Material cost = 405,500 paise + Overheads 180,000 paise = 585,500 paise
    # Cost per packet = 585,500 / 188 = 3,114 paise (~Rs 31.14)
    assert oh_data["cost_per_packet_paise"] == 3114
