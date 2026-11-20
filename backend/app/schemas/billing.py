from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from app.models.billing import InvoiceStatus

class InvoiceItemResponse(BaseModel):
    id: int
    product_id: int
    quantity_packets: int
    unit_price_paise: int
    subtotal_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_paise: int

    model_config = ConfigDict(from_attributes=True)

class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    order_id: int
    customer_id: int
    status: InvoiceStatus
    subtotal_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_paise: int
    whatsapp_share_url: Optional[str] = None
    created_by: int
    created_at: datetime
    items: List[InvoiceItemResponse]

    model_config = ConfigDict(from_attributes=True)

class CreditNoteCreate(BaseModel):
    invoice_id: int
    reason: str = Field(..., min_length=3)

class CreditNoteResponse(BaseModel):
    id: int
    credit_note_no: str
    invoice_id: int
    reason: str
    total_paise: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    customer_id: int
    amount_paise: int = Field(..., gt=0)
    payment_mode: str = Field("cash", description="'cash', 'upi', 'neft_rtgs', 'cheque'")
    reference_no: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_no: str
    customer_id: int
    amount_paise: int
    payment_mode: str
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CustomerBalanceResponse(BaseModel):
    customer_id: int
    customer_name: str
    outstanding_paise: int
    credit_limit_paise: int
