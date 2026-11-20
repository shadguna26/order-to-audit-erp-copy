from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from app.config import settings

def calculate_gst_breakdown(
    subtotal_paise: int,
    gst_rate_pct: Decimal,
    customer_state_code: str,
    customer_state: str
) -> Dict[str, Any]:
    """
    NON-NEGOTIABLE GST RULE:
    If customer state == Tamil Nadu (code 33) then CGST + SGST (half each),
    otherwise IGST.
    Round tax at line level to paise, consistently.
    """
    is_tamil_nadu = (
        customer_state_code.strip() == settings.COMPANY_STATE_CODE or
        customer_state.strip().lower() == "tamil nadu"
    )

    total_tax_rate = Decimal(str(gst_rate_pct))

    if is_tamil_nadu:
        half_rate = total_tax_rate / Decimal("2.0")
        # Line level rounding in paise: (subtotal * half_rate / 100)
        cgst_dec = (Decimal(subtotal_paise) * half_rate / Decimal("100.0")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        sgst_dec = (Decimal(subtotal_paise) * half_rate / Decimal("100.0")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        cgst_paise = int(cgst_dec)
        sgst_paise = int(sgst_dec)
        igst_paise = 0
    else:
        igst_dec = (Decimal(subtotal_paise) * total_tax_rate / Decimal("100.0")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        cgst_paise = 0
        sgst_paise = 0
        igst_paise = int(igst_dec)

    total_paise = subtotal_paise + cgst_paise + sgst_paise + igst_paise

    return {
        "is_intra_state": is_tamil_nadu,
        "cgst_paise": cgst_paise,
        "sgst_paise": sgst_paise,
        "igst_paise": igst_paise,
        "total_paise": total_paise
    }
