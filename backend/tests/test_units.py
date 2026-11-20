import pytest
from decimal import Decimal
from app.models.master import BaseUnitType
from app.services.unit_service import (
    convert_to_base_unit,
    format_base_quantity_for_display
)

def test_weight_conversions_to_base_grams():
    """
    NON-NEGOTIABLE RULE 2:
    All quantities use Decimal in base units (g, ml, piece).
    Convert units only at the edges.
    """
    # 40 kg flour -> 40,000 g
    res = convert_to_base_unit(Decimal("40.0"), "kg", BaseUnitType.G)
    assert res == Decimal("40000.0000")

    # 1.2 kg spice mix -> 1,200 g
    res = convert_to_base_unit(Decimal("1.2"), "kg", BaseUnitType.G)
    assert res == Decimal("1200.0000")

    # 250 g -> 250 g
    res = convert_to_base_unit(Decimal("250"), "g", BaseUnitType.G)
    assert res == Decimal("250.0000")

def test_volume_conversions_to_base_ml():
    # 10 L oil -> 10,000 ml
    res = convert_to_base_unit(Decimal("10.0"), "L", BaseUnitType.ML)
    assert res == Decimal("10000.0000")

    # 10.5 L oil -> 10,500 ml
    res = convert_to_base_unit(Decimal("10.5"), "litre", BaseUnitType.ML)
    assert res == Decimal("10500.0000")

    # 500 ml -> 500 ml
    res = convert_to_base_unit(Decimal("500"), "ml", BaseUnitType.ML)
    assert res == Decimal("500.0000")

def test_count_conversions():
    # 200 pouches -> 200 pieces
    res = convert_to_base_unit(Decimal("200"), "piece", BaseUnitType.PIECE)
    assert res == Decimal("200.0000")

    res = convert_to_base_unit(Decimal("10"), "carton", BaseUnitType.PIECE)
    assert res == Decimal("10.0000")

def test_invalid_unit_conversion():
    # Attempting to convert weight to volume
    with pytest.raises(ValueError, match="Cannot convert non-weight unit 'L' to base unit 'g'"):
        convert_to_base_unit(Decimal("5.0"), "L", BaseUnitType.G)

    # Attempting to convert volume to count
    with pytest.raises(ValueError, match="Cannot convert non-count unit 'kg' to base unit 'piece'"):
        convert_to_base_unit(Decimal("5.0"), "kg", BaseUnitType.PIECE)

    # Negative quantity
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        convert_to_base_unit(Decimal("-10.0"), "kg", BaseUnitType.G)

def test_format_base_quantity_for_display():
    # 100,000 g -> 100.00 kg
    val, unit = format_base_quantity_for_display(Decimal("100000.0"), BaseUnitType.G)
    assert val == "100.00"
    assert unit == "kg"

    # 500 g -> 500.00 g
    val, unit = format_base_quantity_for_display(Decimal("500.0"), BaseUnitType.G)
    assert val == "500.00"
    assert unit == "g"

    # 30,000 ml -> 30.00 L
    val, unit = format_base_quantity_for_display(Decimal("30000.0"), BaseUnitType.ML)
    assert val == "30.00"
    assert unit == "L"

    # 88 packets -> 88 pcs
    val, unit = format_base_quantity_for_display(Decimal("88.0"), BaseUnitType.PIECE)
    assert val == "88"
    assert unit == "pcs"
