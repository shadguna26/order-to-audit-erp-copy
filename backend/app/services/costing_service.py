from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.stock import StockLedger, StockItemType, StockDirection
from app.models.master import RawMaterial

def calculate_weighted_average_cost(db: Session, raw_material_id: int) -> Decimal:
    """
    NON-NEGOTIABLE COSTING RULE:
    Weighted average cost (WAC) for materials.
    Computed across all incoming receipts (opening stock, purchases) in the append-only stock_ledger:
    WAC = SUM(qty_base * unit_cost_paise) / SUM(qty_base)
    Returns cost in paise per base unit (e.g. paise per gram, paise per ml).
    """
    entries = db.query(
        StockLedger.qty_base,
        StockLedger.unit_cost_paise
    ).filter(
        StockLedger.item_type == StockItemType.RAW_MATERIAL,
        StockLedger.item_id == raw_material_id,
        StockLedger.direction == StockDirection.IN
    ).all()

    if not entries:
        return Decimal("0.0000")

    total_cost_paise = Decimal("0.0")
    total_qty_base = Decimal("0.0")

    for qty, unit_cost in entries:
        total_cost_paise += Decimal(qty) * Decimal(unit_cost)
        total_qty_base += Decimal(qty)

    if total_qty_base <= Decimal("0.0"):
        return Decimal("0.0000")

    wac = (total_cost_paise / total_qty_base).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return wac

def get_all_material_wac(db: Session) -> Dict[int, Decimal]:
    """Returns a map of {raw_material_id: wac_paise_per_base_unit}."""
    materials = db.query(RawMaterial.id).all()
    return {m.id: calculate_weighted_average_cost(db, m.id) for m in materials}
