from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from app.models.sales import OrderStatus

class OrderItemCreate(BaseModel):
    product_id: int
    quantity_packets: int = Field(..., gt=0)
    unit_price_paise: Optional[int] = None

class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity_packets: int
    unit_price_paise: int
    tax_rate_pct: Decimal
    subtotal_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_paise: int

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    order_no: str
    customer_id: int
    salesman_id: int
    status: OrderStatus
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class StockCoverageCheckItem(BaseModel):
    product_id: int
    requested_packets: int

class StockCoverageResponse(BaseModel):
    product_id: int
    product_name: str
    requested_packets: int
    available_packets: int
    has_shortage: bool
    shortage_packets: int
    shortage_message: Optional[str] = None
    suggested_batches_to_produce: int
    can_dispatch_available: bool

class DispatchCreate(BaseModel):
    invoice_id: int
    vehicle_no: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None

class DispatchResponse(BaseModel):
    id: int
    dispatch_no: str
    order_id: int
    invoice_id: int
    vehicle_no: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
