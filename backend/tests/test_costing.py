import pytest
from decimal import Decimal
from datetime import date
from app.models.master import RawMaterial, Supplier
from app.models.stock import StockLedger, StockItemType, StockDirection
from app.services.costing_service import calculate_weighted_average_cost

def test_weighted_average_cost_flour(client, db):
    """
    NON-NEGOTIABLE COSTING RULE:
    Weighted average cost for materials.
    Opening: 100 kg (100,000 g) @ Rs 42/kg = 4.2 paise/g (420,000 paise).
    Purchase: 60 kg (60,000 g) @ Rs 45/kg = 4.5 paise/g (270,000 paise).
    Total: 160,000 g, Total Cost: 690,000 paise.
    Expected WAC: 690,000 / 160,000 = 4.3125 paise/g.
    """
    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()
    supplier = db.query(Supplier).first()

    prod_login = client.post("/api/v1/auth/login", data={"username": "production", "password": "prod123"})
    prod_token = prod_login.json()["access_token"]

    # Record purchase of 60 kg @ Rs 45/kg (4500 paise/kg)
    purchase_payload = {
        "supplier_id": supplier.id,
        "supplier_invoice_no": "PUR-FLOUR-01",
        "invoice_date": str(date.today()),
        "items": [
            {
                "raw_material_id": flour.id,
                "input_qty": 60.0,
                "input_unit": "kg",
                "rate_paise_per_unit": 4500
            }
        ]
    }
    res = client.post(
        "/api/v1/purchases",
        json=purchase_payload,
        headers={"Authorization": f"Bearer {prod_token}"}
    )
    assert res.status_code == 201

    wac = calculate_weighted_average_cost(db, flour.id)
    assert wac == Decimal("4.3125")
