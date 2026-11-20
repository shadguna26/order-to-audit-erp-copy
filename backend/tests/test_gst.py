import pytest
from decimal import Decimal
from app.services.gst_service import calculate_gst_breakdown

def test_tamil_nadu_cgst_sgst_split():
    """
    NON-NEGOTIABLE GST RULE:
    If customer state == Tamil Nadu (code 33) then CGST+SGST (half each).
    Round tax at line level to paise, consistently.
    150 packets @ Rs 50 = Rs 7,500 (750,000 paise).
    5% GST: 2.5% CGST = Rs 187.50 (18,750 paise), 2.5% SGST = Rs 187.50 (18,750 paise).
    Total = Rs 7,875 (787,500 paise).
    """
    res = calculate_gst_breakdown(
        subtotal_paise=750000,
        gst_rate_pct=Decimal("5.00"),
        customer_state_code="33",
        customer_state="Tamil Nadu"
    )
    assert res["is_intra_state"] is True
    assert res["cgst_paise"] == 18750
    assert res["sgst_paise"] == 18750
    assert res["igst_paise"] == 0
    assert res["total_paise"] == 787500

def test_interstate_karnataka_igst():
    """
    If customer state != Tamil Nadu (e.g. Karnataka 29), IGST applies.
    """
    res = calculate_gst_breakdown(
        subtotal_paise=750000,
        gst_rate_pct=Decimal("5.00"),
        customer_state_code="29",
        customer_state="Karnataka"
    )
    assert res["is_intra_state"] is False
    assert res["cgst_paise"] == 0
    assert res["sgst_paise"] == 0
    assert res["igst_paise"] == 37500
    assert res["total_paise"] == 787500
