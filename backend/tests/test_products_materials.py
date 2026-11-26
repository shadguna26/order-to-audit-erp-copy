"""
Part B tests: Products, Raw Materials, BOM scaling, Deactivate-not-delete,
Invoice price/GST/HSN snapshot immutability, and Opening Stock ledger entries.
"""
from decimal import Decimal
from datetime import datetime, timezone
from tests.conftest import otp_login
from app.models.audit import AuditLog
from app.models.billing import Invoice
from app.models.master import Product
from app.models.stock import StockDocType, StockItemType, StockLedger


def test_duplicate_product_bom_scaling(client, db):
    """Duplicating 200g Kai Murukku to 500g scales raw material BOM quantities by 2.5x."""
    admin_token = otp_login(client, "+919000000002")["access_token"]

    src_res = client.get("/api/v1/products/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert src_res.status_code == 200
    src = src_res.json()
    assert Decimal(str(src["pack_size_g"])) == Decimal("200.00")
    src_flour = next(i for i in src["bom"]["items"] if i["raw_material_code"] == "RM-FLOUR")
    src_pouch = next(i for i in src["bom"]["items"] if i["base_unit"] == "piece")

    dup_res = client.post(
        "/api/v1/products/1/duplicate",
        json={
            "name": "Kai Murukku 500g",
            "name_ta": "கை முறுக்கு 500கி",
            "pack_size_value": 500,
            "pack_size_unit": "g",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dup_res.status_code == 201, dup_res.text
    dup = dup_res.json()
    assert Decimal(str(dup["pack_size_g"])) == Decimal("500.00")
    dup_flour = next(i for i in dup["bom"]["items"] if i["raw_material_code"] == "RM-FLOUR")
    dup_pouch = next(i for i in dup["bom"]["items"] if i["base_unit"] == "piece")

    assert Decimal(str(dup_flour["standard_qty_base"])) == Decimal(str(src_flour["standard_qty_base"])) * Decimal("2.5")
    assert Decimal(str(dup_pouch["standard_qty_base"])) == Decimal(str(src_pouch["standard_qty_base"]))


def test_deactivate_not_delete_used_product(client, db):
    """Products referenced in transactions are deactivated rather than deleted."""
    admin_token = otp_login(client, "+919000000002")["access_token"]

    # Product 1 is used in opening stock / BOM / orders
    del_res = client.delete(
        "/api/v1/products/1",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == 200, del_res.text
    body = del_res.json()
    assert body["deleted"] is False
    assert body["is_active"] is False

    prod = db.query(Product).filter(Product.id == 1).first()
    assert prod is not None
    assert prod.is_active is False


def test_invoice_snapshot_unchanged_after_price_change(client, db):
    """Changing product price/GST/HSN later must never alter previously posted invoices."""
    admin_token = otp_login(client, "+919000000002")["access_token"]

    # 1. Order -> Approve -> Invoice at original price (5000 paise, 5% GST, HSN 21069099)
    ord_res = client.post(
        "/api/v1/orders",
        json={"customer_id": 1, "items": [{"product_id": 1, "quantity_packets": 10}]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ord_res.status_code == 201, ord_res.text
    order_id = ord_res.json()["id"]

    assert client.post(f"/api/v1/orders/{order_id}/approve", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
    inv_res = client.post(f"/api/v1/invoices/from-order/{order_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert inv_res.status_code == 201, inv_res.text
    inv_before = inv_res.json()
    inv_id = inv_before["id"]

    # 2. Update product price, GST rate, and HSN
    upd_res = client.put(
        "/api/v1/products/1",
        json={
            "selling_price_paise": 7500,
            "gst_rate_pct": 12.00,
            "hsn_code": "19059090",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upd_res.status_code == 200, upd_res.text

    # 3. Verify posted invoice snapshot is unchanged
    inv_after_res = client.get(f"/api/v1/invoices/{inv_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert inv_after_res.status_code == 200
    inv_after = inv_after_res.json()
    assert inv_after["total_paise"] == inv_before["total_paise"]
    assert inv_after["items"][0]["unit_price_paise"] == 5000
    assert inv_after["items"][0]["hsn_code"] == "21069099"
    assert Decimal(str(inv_after["items"][0]["gst_rate_pct"])) == Decimal("5.00")

    # 4. Verify audit log recorded the change
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.table_name == "products", AuditLog.record_id == 1, AuditLog.action == "UPDATE")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert audit is not None
    assert audit.old_values["selling_price_paise"] == 5000
    assert audit.new_values["selling_price_paise"] == 7500


def test_opening_stock_creates_ledger_row(client, db):
    """Creating a product or raw material with opening stock appends an opening_balance ledger row."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    prod_token = otp_login(client, "+919000000005")["access_token"]

    # Production role adds raw material with opening stock
    rm_res = client.post(
        "/api/v1/raw-materials",
        json={
            "name": "Black Pepper",
            "type": "raw",
            "base_unit": "g",
            "unit_conversions": {"kg": 1000},
            "reorder_level_base": 500,
            "opening_stock_base": 5000,
            "batch_no": "RM-OB-01",
            "expiry_date": "2027-06-30",
        },
        headers={"Authorization": f"Bearer {prod_token}"},
    )
    assert rm_res.status_code == 201, rm_res.text
    rm_id = rm_res.json()["id"]

    rm_ledger = (
        db.query(StockLedger)
        .filter(
            StockLedger.item_type == StockItemType.RAW_MATERIAL,
            StockLedger.item_id == rm_id,
            StockLedger.source_doc_type == StockDocType.OPENING_BALANCE,
        )
        .first()
    )
    assert rm_ledger is not None
    assert Decimal(str(rm_ledger.qty_base)) == Decimal("5000.0000")
    assert rm_ledger.batch_no == "RM-OB-01"

    # Admin adds product with opening stock & BOM
    p_res = client.post(
        "/api/v1/products",
        json={
            "name": "Pepper Sev 200g",
            "name_ta": "மிளகு சேவ் 200கி",
            "voice_aliases": "milagu sev, pepper sev",
            "pack_size_value": 200,
            "pack_size_unit": "g",
            "packets_per_carton": 20,
            "selling_price_paise": 6000,
            "gst_rate_pct": 5.00,
            "hsn_code": "21069099",
            "opening_stock_packets": 45,
            "batch_no": "FG-OB-01",
            "expiry_date": "2027-03-31",
            "expected_yield_packets": 200,
            "bom_items": [{"raw_material_id": rm_id, "standard_qty_base": 1500}],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert p_res.status_code == 201, p_res.text
    prod = p_res.json()
    assert prod["balance_packets"] == 45

    fg_ledger = (
        db.query(StockLedger)
        .filter(
            StockLedger.item_type == StockItemType.FINISHED_GOODS,
            StockLedger.item_id == prod["id"],
            StockLedger.source_doc_type == StockDocType.OPENING_BALANCE,
        )
        .first()
    )
    assert fg_ledger is not None
    assert Decimal(str(fg_ledger.qty_base)) == Decimal("45.0000")

    # Search by Tamil name & voice alias
    search_res = client.get(
        "/api/v1/products?search=மிளகு",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert search_res.status_code == 200
    assert any(p["id"] == prod["id"] for p in search_res.json())


def test_role_restrictions_products_and_hsn_validation(client, db):
    """Salesman cannot create products; invalid HSN is rejected."""
    sales_token = otp_login(client, "+919000000003")["access_token"]
    admin_token = otp_login(client, "+919000000002")["access_token"]

    res = client.post(
        "/api/v1/products",
        json={"name": "Test", "selling_price_paise": 5000, "hsn_code": "2106"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert res.status_code == 403

    bad_hsn = client.post(
        "/api/v1/products",
        json={"name": "Test", "selling_price_paise": 5000, "hsn_code": "123"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert bad_hsn.status_code == 422
