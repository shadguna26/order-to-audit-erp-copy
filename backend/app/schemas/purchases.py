from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime
from app.models.billing import PurchaseStatus

class PurchaseItemCreate(BaseModel):
    raw_material_id: int
    input_qty: Decimal = Field(..., gt=0, description="Quantity in input unit (e.g. 60 for 60 kg)")
    input_unit: str = Field(..., description="Unit: kg, g, l, ml, piece")
    rate_paise_per_unit: int = Field(..., gt=0, description="Purchase rate in paise per input unit (e.g. 4500 for Rs 45/kg)")

class PurchaseCreate(BaseModel):
    supplier_id: int
    supplier_invoice_no: Optional[str] = None
    invoice_date: date
    items: List[PurchaseItemCreate] = Field(..., min_length=1)

class PurchaseItemResponse(BaseModel):
    id: int
    raw_material_id: int
    input_qty: Decimal
    input_unit: str
    qty_base: Decimal
    rate_paise_per_unit: int
    total_amount_paise: int

    model_config = ConfigDict(from_attributes=True)

class PurchaseResponse(BaseModel):
    id: int
    purchase_no: str
    supplier_id: int
    supplier_invoice_no: Optional[str] = None
    invoice_date: date
    total_amount_paise: int
    status: PurchaseStatus
    created_by: int
    created_at: datetime
    items: List[PurchaseItemResponse]

    model_config = ConfigDict(from_attributes=True)
