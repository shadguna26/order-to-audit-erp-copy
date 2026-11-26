import pytest
from decimal import Decimal
from datetime import date
from app.models.master import RawMaterial, Product, Customer, BOM, Supplier
from app.models.stock import StockItemType, StockLocationType
from app.models.sales import Order, OrderStatus
from app.services.ledger_service import get_item_stock_balance

def test_full_benchmark_scenario(client, db):
    """
    BENCHMARK SCENARIO (Steps 1 to 8):
    BOM Murukku 200 g, one batch = 200 packets:
    flour 40 kg, oil 10 L, spice mix 1.2 kg, 200 g pouch 200 pcs, carton 10 pcs (carton holds 20 packets).
    Rates: flour Rs 42 (opening) and Rs 45 (new purchase), oil 140/L, spice mix 200/kg, pouch 2.50, carton 15.
    Opening stock: flour 100 kg, oil 30 L, spice mix 5 kg, pouches 500, cartons 30, finished Murukku 200 g = 50 packets.
    Selling price Rs 50 + 5% GST. Factory in Tamil Nadu.

    Steps:
    (1) Purchase 60 kg flour at Rs 45.
    (2) Production run issuing 40 kg flour, 10.5 L oil, 1.2 kg spice.
    (3) Actual output 188 packets, 6 pouches damaged, 9 cartons used.
    (4) Salesman A orders 150 packets for Retailer A (Tamil Nadu).
    (5) Admin approves, creates CGST+SGST invoice, records dispatch.
    (6) Salesman B orders 120 packets for Distributor B (Karnataka): system flags shortage of 32.
    (7) Payment of Rs 4,000 from Retailer A.
    (8) Add labour Rs 1,200 and gas/power Rs 600 to the run; show cost per packet.

    EXPECTED FINAL OUTCOMES:
    - Flour: 120 kg
    - Oil: 19.5 L
    - Pouches: 306
    - Finished goods: 238 after run, 88 after dispatch
    - Yield variance: 188 vs 200 = -6% flagged
    - Oil variance: +5% flagged (Rupee variance Rs 70)
    - Invoice: Rs 7,500 + 187.50 CGST + 187.50 SGST = Rs 7,875
    - Retailer A outstanding: Rs 3,875
    - Distributor B shortage: 32 (IGST applies if invoiced)
    """
    # Authenticate actors
    from tests.conftest import otp_login
    admin_tok = otp_login(client, "+919000000002")["access_token"]
    prod_tok = otp_login(client, "+919000000005")["access_token"]
    sales_a_tok = otp_login(client, "+919000000003")["access_token"]
    sales_b_tok = otp_login(client, "+919000000004")["access_token"]

    admin_hdr = {"Authorization": f"Bearer {admin_tok}"}
    prod_hdr = {"Authorization": f"Bearer {prod_tok}"}
    sales_a_hdr = {"Authorization": f"Bearer {sales_a_tok}"}
    sales_b_hdr = {"Authorization": f"Bearer {sales_b_tok}"}

    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()
    oil = db.query(RawMaterial).filter(RawMaterial.code == "RM-OIL").first()
    spice = db.query(RawMaterial).filter(RawMaterial.code == "RM-SPICE").first()
    pouch = db.query(RawMaterial).filter(RawMaterial.code == "PKG-POUCH-200G").first()
    carton = db.query(RawMaterial).filter(RawMaterial.code == "PKG-CARTON-20").first()
    murukku = db.query(Product).filter(Product.code == "FG-MRK-200G").first()
    bom = db.query(BOM).filter(BOM.product_id == murukku.id).first()
    supplier = db.query(Supplier).first()
    retailer_a = db.query(Customer).filter(Customer.name.like("%Retailer A%")).first()
    distributor_b = db.query(Customer).filter(Customer.name.like("%Distributor B%")).first()

    # (1) Purchase 60 kg flour at Rs 45/kg
    p_res = client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": supplier.id,
            "invoice_date": str(date.today()),
            "items": [{"raw_material_id": flour.id, "input_qty": 60.0, "input_unit": "kg", "rate_paise_per_unit": 4500}]
        },
        headers=prod_hdr
    )
    assert p_res.status_code == 201

    # (2) & (3) Production run
    # Issued: 40 kg flour, 10.5 L oil, 1.2 kg spice, 194 pouches (188+6), 9 cartons
    # Actual output: 188 packets
    run_res = client.post(
        "/api/v1/production/runs",
        json={
            "product_id": murukku.id,
            "bom_id": bom.id,
            "planned_batches": 1,
            "actual_good_output_packets": 188,
            "actual_damaged_pouches": 6,
            "actual_cartons_used": 9,
            "issued_items": [
                {"raw_material_id": flour.id, "actual_qty_base": 40000.0},
                {"raw_material_id": oil.id, "actual_qty_base": 10500.0},
                {"raw_material_id": spice.id, "actual_qty_base": 1200.0},
                {"raw_material_id": pouch.id, "actual_qty_base": 194.0},
                {"raw_material_id": carton.id, "actual_qty_base": 9.0},
            ],
            "overheads": []
        },
        headers=prod_hdr
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # Verify Stock Levels After Run
    assert get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id) == Decimal("120000.0000") # 120 kg
    assert get_item_stock_balance(db, StockItemType.RAW_MATERIAL, oil.id) == Decimal("19500.0000")   # 19.5 L
    assert get_item_stock_balance(db, StockItemType.RAW_MATERIAL, pouch.id) == Decimal("306.0000")   # 306 pouches
    assert get_item_stock_balance(db, StockItemType.FINISHED_GOODS, murukku.id) == Decimal("238.0000") # 238 pkts

    # (4) Salesman A orders 150 packets for Retailer A (Tamil Nadu)
    order_a_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": retailer_a.id,
            "items": [{"product_id": murukku.id, "quantity_packets": 150, "unit_price_paise": 5000}]
        },
        headers=sales_a_hdr
    )
    assert order_a_res.status_code == 201
    order_a_id = order_a_res.json()["id"]

    # (5) Admin approves, creates CGST+SGST invoice, records dispatch
    appr_res = client.post(f"/api/v1/orders/{order_a_id}/approve", headers=admin_hdr)
    assert appr_res.status_code == 200

    inv_res = client.post(f"/api/v1/invoices/from-order/{order_a_id}", headers=admin_hdr)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["subtotal_paise"] == 750000 # Rs 7,500.00
    assert inv_data["cgst_paise"] == 18750      # Rs 187.50
    assert inv_data["sgst_paise"] == 18750      # Rs 187.50
    assert inv_data["igst_paise"] == 0
    assert inv_data["total_paise"] == 787500    # Rs 7,875.00
    assert inv_data["invoice_no"].startswith("TN/")
    inv_id = inv_data["id"]

    # Record Dispatch
    disp_res = client.post(
        "/api/v1/dispatches",
        json={"invoice_id": inv_id, "vehicle_no": "TN-45-AT-1234"},
        headers=admin_hdr
    )
    assert disp_res.status_code == 201

    # Invariant: Finished goods after dispatch = 238 - 150 = 88 packets!
    fg_after_disp = get_item_stock_balance(db, StockItemType.FINISHED_GOODS, murukku.id)
    assert fg_after_disp == Decimal("88.0000")

    # (6) Salesman B orders 120 packets for Distributor B (Karnataka)
    # Check live stock shortage
    stock_chk_res = client.get(f"/api/v1/orders/check-stock/{murukku.id}?quantity=120", headers=sales_b_hdr)
    assert stock_chk_res.status_code == 200
    stock_chk = stock_chk_res.json()
    assert stock_chk["available_packets"] == 88
    assert stock_chk["shortage_packets"] == 32
    assert "Only 88 packets in stock. Short by 32." in stock_chk["shortage_message"]
    assert stock_chk["suggested_batches_to_produce"] == 1

    # (7) Payment of Rs 4,000 from Retailer A
    pay_res = client.post(
        "/api/v1/payments",
        json={
            "customer_id": retailer_a.id,
            "amount_paise": 400000, # Rs 4,000.00
            "payment_mode": "upi",
            "reference_no": "UPI-RET-A-998877"
        },
        headers=admin_hdr
    )
    assert pay_res.status_code == 201

    # Check Retailer A outstanding balance: Rs 7,875 - Rs 4,000 = Rs 3,875 (387,500 paise)
    bal_res = client.get(f"/api/v1/payments/customer/{retailer_a.id}/outstanding", headers=admin_hdr)
    assert bal_res.status_code == 200
    assert bal_res.json()["outstanding_paise"] == 387500

    # (8) Add labour Rs 1,200 and gas/power Rs 600 to the run; show cost per packet
    oh_res = client.post(
        f"/api/v1/production/runs/{run_id}/overheads",
        json=[
            {"overhead_type": "labour", "amount_paise": 120000},
            {"overhead_type": "gas_power", "amount_paise": 60000}
        ],
        headers=prod_hdr
    )
    assert oh_res.status_code == 200
    assert oh_res.json()["cost_per_packet_paise"] == 3114
