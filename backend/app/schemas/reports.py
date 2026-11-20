from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SalesRegisterItem(BaseModel):
    id: int
    invoice_no: str
    invoice_date: str
    customer_name: str
    customer_gstin: str
    state: str
    subtotal_paise: int
    subtotal_rs: str
    cgst_paise: int
    cgst_rs: str
    sgst_paise: int
    sgst_rs: str
    igst_paise: int
    igst_rs: str
    total_paise: int
    total_rs: str

class GSTSummarySupply(BaseModel):
    taxable_value_paise: int
    taxable_value_rs: str
    cgst_paise: Optional[int] = 0
    cgst_rs: Optional[str] = "0.00"
    sgst_paise: Optional[int] = 0
    sgst_rs: Optional[str] = "0.00"
    igst_paise: Optional[int] = 0
    igst_rs: Optional[str] = "0.00"
    total_tax_paise: int
    total_tax_rs: str

class GSTSummaryResponse(BaseModel):
    period: Dict[str, str]
    intra_state_supplies: Dict[str, Any]
    inter_state_supplies: Dict[str, Any]
    totals: Dict[str, Any]

class PurchaseRegisterItem(BaseModel):
    id: int
    purchase_no: str
    invoice_date: str
    supplier_name: str
    supplier_invoice_no: str
    items_count: int
    total_amount_paise: int
    total_amount_rs: str
    status: str

class AgeingReportItem(BaseModel):
    customer_id: int
    customer_name: str
    state: str
    phone: str
    total_outstanding_paise: int
    total_outstanding_rs: str
    bucket_0_30_paise: int
    bucket_0_30_rs: str
    bucket_31_60_paise: int
    bucket_31_60_rs: str
    bucket_61_90_paise: int
    bucket_61_90_rs: str
    bucket_90_plus_paise: int
    bucket_90_plus_rs: str

class ProductionReportItem(BaseModel):
    id: int
    run_no: str
    date: str
    product_name: str
    planned_output: int
    actual_good_output: int
    damaged_pouches: int
    cartons_used: int
    yield_variance_pct: str
    is_yield_flagged: bool
    material_cost_rs: str
    overhead_cost_rs: str
    cost_per_packet_rs: str
