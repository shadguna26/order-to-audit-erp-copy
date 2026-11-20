import pytest
from decimal import Decimal
from app.models.master import RawMaterial, Product, BaseUnitType
from app.models.stock import (
    StockLedger,
    StockItemType,
    StockLocationType,
    StockDirection,
    StockDocType
)
from app.services.ledger_service import (
    record_stock_movement,
    get_item_stock_balance,
    get_all_stock_summary,
    get_item_ledger_history
)

def test_append_only_ledger_balance_sum(db):
    """
    NON-NEGOTIABLE RULE 1:
    Balances are SUMs of the ledger. Never overwrite a balance.
    """
    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()

    # Opening balance from seed was 100,000 g
    initial_balance = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id)
    assert initial_balance == Decimal("100000.0000")

    # Add an IN movement of 20,000 g
    record_stock_movement(
        db=db,
        item_type=StockItemType.RAW_MATERIAL,
        item_id=flour.id,
        location_type=StockLocationType.RAW,
        direction=StockDirection.IN,
        qty_base=Decimal("20000.0"),
        base_unit=BaseUnitType.G,
        unit_cost_paise=4,
        source_doc_type=StockDocType.ADJUSTMENT,
        source_doc_id=999,
        created_by=1
    )

    balance_after_in = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id)
    assert balance_after_in == Decimal("120000.0000")

    # Add an OUT movement of 50,000 g
    record_stock_movement(
        db=db,
        item_type=StockItemType.RAW_MATERIAL,
        item_id=flour.id,
        location_type=StockLocationType.RAW,
        direction=StockDirection.OUT,
        qty_base=Decimal("50000.0"),
        base_unit=BaseUnitType.G,
        unit_cost_paise=4,
        source_doc_type=StockDocType.PRODUCTION_ISSUE,
        source_doc_id=1,
        created_by=1
    )

    balance_after_out = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, flour.id)
    assert balance_after_out == Decimal("70000.0000")

    # Verify history trace returns all 3 records in chronological/id order
    history = get_item_ledger_history(db, StockItemType.RAW_MATERIAL, flour.id)
    assert len(history) == 3

def test_full_stock_summary_api(client):
    admin_login = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    token = admin_login.json()["access_token"]

    response = client.get(
        "/api/v1/stock/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw_and_packaging" in data
    assert "finished_goods" in data

    # Check that finished goods includes Kai Murukku 200g with 50 packets opening
    fg_murukku = next(item for item in data["finished_goods"] if item["code"] == "FG-MRK-200G")
    assert fg_murukku["balance_packets"] == 50
