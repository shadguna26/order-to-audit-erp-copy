from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple
from app.models.master import BaseUnitType

# Allowed input unit aliases
WEIGHT_UNITS = {"kg": Decimal("1000.0"), "g": Decimal("1.0"), "gram": Decimal("1.0"), "grams": Decimal("1.0")}
VOLUME_UNITS = {"l": Decimal("1000.0"), "litre": Decimal("1000.0"), "liter": Decimal("1000.0"), "ml": Decimal("1.0")}
COUNT_UNITS = {"piece": Decimal("1.0"), "pcs": Decimal("1.0"), "packet": Decimal("1.0"), "pkt": Decimal("1.0"), "carton": Decimal("1.0")}

def normalize_unit_string(unit: str) -> str:
    return unit.strip().lower()

def convert_to_base_unit(
    quantity: Decimal,
    from_unit: str,
    target_base_unit: BaseUnitType
) -> Decimal:
    """
    NON-NEGOTIABLE RULE 2:
    All quantities use Decimal in base units (g, ml, piece).
    Convert units only at the edges (kg, litre, packet, carton). Never use floats.
    """
    if quantity < Decimal("0"):
        raise ValueError(f"Quantity cannot be negative: {quantity}")

    u = normalize_unit_string(from_unit)

    if target_base_unit == BaseUnitType.G:
        if u not in WEIGHT_UNITS:
            raise ValueError(f"Cannot convert non-weight unit '{from_unit}' to base unit 'g'")
        return (quantity * WEIGHT_UNITS[u]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    elif target_base_unit == BaseUnitType.ML:
        if u not in VOLUME_UNITS:
            raise ValueError(f"Cannot convert non-volume unit '{from_unit}' to base unit 'ml'")
        return (quantity * VOLUME_UNITS[u]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    elif target_base_unit == BaseUnitType.PIECE:
        if u not in COUNT_UNITS:
            raise ValueError(f"Cannot convert non-count unit '{from_unit}' to base unit 'piece'")
        return (quantity * COUNT_UNITS[u]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    else:
        raise ValueError(f"Unsupported base unit: {target_base_unit}")

def format_base_quantity_for_display(qty_base: Decimal, base_unit: BaseUnitType) -> Tuple[str, str]:
    """
    Returns (formatted_number, unit_label)
    e.g. (100000.0, BaseUnitType.G) -> ("100.00", "kg")
         (500.0, BaseUnitType.G)    -> ("500.00", "g")
         (30000.0, BaseUnitType.ML) -> ("30.00", "L")
         (88.0, BaseUnitType.PIECE) -> ("88", "pkts")
    """
    if base_unit == BaseUnitType.G:
        if qty_base >= Decimal("1000.0"):
            val = (qty_base / Decimal("1000.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return (f"{val:f}", "kg")
        return (f"{qty_base.quantize(Decimal('0.01')):f}", "g")

    elif base_unit == BaseUnitType.ML:
        if qty_base >= Decimal("1000.0"):
            val = (qty_base / Decimal("1000.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return (f"{val:f}", "L")
        return (f"{qty_base.quantize(Decimal('0.01')):f}", "ml")

    elif base_unit == BaseUnitType.PIECE:
        return (f"{int(qty_base)}", "pcs")

    return (f"{qty_base}", str(base_unit.value))
