import pytest
from decimal import Decimal
from datetime import date
from app.models.master import RawMaterial, Supplier
from app.models.billing import Purchase
from app.models.audit import AuditLog
from app.models.stock import StockLedger, StockItemType, StockDirection, StockDocType
from app.services.ledger_service import get_item_stock_balance

def test_benchmark_step_1_purchase_flour(client, db):
    """
    BENCHMARK STEP 1:
    (1) Purchase 60 kg flour at Rs 45/kg.
    Initial opening stock: 100 kg flour.
    Expected: Flour balance becomes 160 kg (160,000 g).
    """
    # 1. Salesman cannot create purchases (RBAC check)
    from tests.conftest import otp_login
    sales_token = otp_login(client, "+919000000003")["access_token"]

    supplier = db.query(Supplier).first()
    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()

    purchase_payload = {
        "supplier_id": supplier.id,
        "supplier_invoice_no": "INV-2026-999",
        "invoice_date": str(date.today()),
        "items": [
            {
                "raw_material_id": flour.id,
                "input_qty": 60.0,
                "input_unit": "kg",
                "rate_paise_per_unit": 4500 # Rs 45.00/kg
            }
        ]
    }

    forbidden_res = client.post(
        "/api/v1/purchases",
        json=purchase_payload,
        headers={"Authorization": f"Bearer {sales_token}"}
    )
    assert forbidden_res.status_code == 403

    # 2. Production incharge records the purchase
    prod_token = otp_login(client, "+919000000005")["access_token"]

    res = client.post(
        "/api/v1/purchases",
        json=purchase_payload,
        headers={"Authorization": f"Bearer {prod_token}"}
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["purchase_no"].startswith("PO/")
    assert data["total_amount_paise"] == 270000 # 60 kg * 4500 paise = 270,000 paise (Rs 2,700)
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert Decimal(item["qty_base"]) == Decimal("60000.0000") # 60,000 g

    # 3. Check append-only stock_ledger
    ledger_entry = db.query(StockLedger).filter(
        StockLedger.source_doc_type == StockDocType.PURCHASE,
        StockLedger.source_doc_id == data["id"]
    ).first()
    assert ledger_entry is not None
    assert ledger_entry.direction == StockDirection.IN
    assert ledger_entry.qty_base == Decimal("60000.0000")

    # 4. Invariant: Ledger balance is exactly 160 kg (100 kg opening + 60 kg purchase)
    flour_balance = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id)
    assert flour_balance == Decimal("160000.0000")

    # 5. Check Audit Log written
    audit_entry = db.query(AuditLog).filter(
        AuditLog.table_name == "purchases",
        AuditLog.record_id == data["id"]
    ).first()
    assert audit_entry is not None
    assert audit_entry.action == "INSERT"
