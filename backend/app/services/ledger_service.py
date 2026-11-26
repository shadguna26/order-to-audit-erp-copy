from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc

from app.models.stock import (
    StockLedger,
    StockItemType,
    StockLocationType,
    StockDirection,
    StockDocType
)
from app.models.master import RawMaterial, Product, BaseUnitType
from app.services.unit_service import format_base_quantity_for_display

def record_stock_movement(
    db: Session,
    item_type: StockItemType,
    item_id: int,
    location_type: StockLocationType,
    direction: StockDirection,
    qty_base: Decimal,
    base_unit: BaseUnitType,
    unit_cost_paise: Decimal,
    source_doc_type: StockDocType,
    source_doc_id: int,
    created_by: int,
    batch_no: Optional[str] = None,
    expiry_date: Optional[date] = None,
    business_id: int = 1,
) -> StockLedger:
    """
    NON-NEGOTIABLE RULE 1:
    A single append-only stock_ledger table is the source of truth.
    Every row has item, location type (raw / packaging / finished),
    qty in base unit, direction, source document type + id,
    batch no (optional), user, timestamp.
    Balances are SUMs of the ledger. Never overwrite a balance.
    """
    if qty_base <= Decimal("0"):
        raise ValueError(f"Quantity for stock movement must be positive: {qty_base}")

    entry = StockLedger(
        business_id=business_id,
        item_type=item_type,
        item_id=item_id,
        location_type=location_type,
        direction=direction,
        qty_base=qty_base,
        base_unit=base_unit,
        unit_cost_paise=unit_cost_paise,
        source_doc_type=source_doc_type,
        source_doc_id=source_doc_id,
        batch_no=batch_no,
        expiry_date=expiry_date,
        created_by=created_by
    )
    db.add(entry)
    db.flush()
    return entry

def get_item_stock_balance(
    db: Session,
    item_type: StockItemType,
    item_id: int,
    location_type: Optional[StockLocationType] = None,
    business_id: int = 1,
) -> Decimal:
    """
    Calculates stock balance dynamically from the append-only stock ledger:
    SUM(CASE WHEN direction = 'IN' THEN qty_base ELSE -qty_base END)
    """
    query = db.query(
        func.coalesce(
            func.sum(
                case(
                    (StockLedger.direction == StockDirection.IN, StockLedger.qty_base),
                    else_=-StockLedger.qty_base
                )
            ),
            0
        )
    ).filter(
        StockLedger.business_id == business_id,
        StockLedger.item_type == item_type,
        StockLedger.item_id == item_id
    )

    if location_type:
        query = query.filter(StockLedger.location_type == location_type)

    balance = query.scalar()
    return Decimal(str(balance or "0.0000"))

def get_all_stock_summary(db: Session, business_id: int = 1) -> Dict[str, Any]:
    """
    Returns full factory stock snapshot computed dynamically from stock_ledger:
    - Raw materials
    - Packaging items
    - Finished goods
    """
    raw_materials = db.query(RawMaterial).filter(
        RawMaterial.business_id == business_id,
        RawMaterial.is_active == True,
    ).all()
    products = db.query(Product).filter(
        Product.business_id == business_id,
        Product.is_active == True,
    ).all()

    materials_summary = []
    for rm in raw_materials:
        loc = StockLocationType.PACKAGING if rm.type.value == "packaging" else StockLocationType.RAW
        balance_base = get_item_stock_balance(
            db,
            item_type=StockItemType.RAW_MATERIAL,
            item_id=rm.id,
            location_type=loc,
            business_id=business_id,
        )
        display_val, display_unit = format_base_quantity_for_display(balance_base, rm.base_unit)
        materials_summary.append({
            "id": rm.id,
            "code": rm.code,
            "name": rm.name,
            "type": rm.type.value,
            "base_unit": rm.base_unit.value,
            "balance_base": balance_base,
            "display_quantity": display_val,
            "display_unit": display_unit,
            "reorder_level_base": rm.reorder_level_base,
            "is_low_stock": balance_base <= rm.reorder_level_base
        })

    products_summary = []
    for p in products:
        balance_base = get_item_stock_balance(
            db,
            item_type=StockItemType.FINISHED_GOODS,
            item_id=p.id,
            location_type=StockLocationType.FINISHED,
            business_id=business_id,
        )
        display_val, display_unit = format_base_quantity_for_display(balance_base, p.base_unit)
        products_summary.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "hsn_code": p.hsn_code,
            "pack_size_g": p.pack_size_g,
            "base_unit": p.base_unit.value,
            "balance_packets": int(balance_base),
            "display_quantity": display_val,
            "display_unit": display_unit
        })

    return {
        "raw_and_packaging": materials_summary,
        "finished_goods": products_summary
    }

def get_item_ledger_history(
    db: Session,
    item_type: StockItemType,
    item_id: int,
    limit: int = 100,
    business_id: int = 1,
) -> List[StockLedger]:
    """
    Fetches immutable ledger trail for any item.
    Rule: 'Clicking any stock number opens its ledger showing every movement and source document.'
    """
    return db.query(StockLedger).filter(
        StockLedger.business_id == business_id,
        StockLedger.item_type == item_type,
        StockLedger.item_id == item_id
    ).order_by(desc(StockLedger.id)).limit(limit).all()
