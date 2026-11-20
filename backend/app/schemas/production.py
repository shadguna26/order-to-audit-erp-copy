from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

class BOMItemPrefill(BaseModel):
    raw_material_id: int
    code: str
    name: str
    type: str
    standard_qty_base: Decimal
    base_unit: str
    display_quantity: str
    display_unit: str
    unit_cost_wac_paise: Decimal

class BOMPrefillResponse(BaseModel):
    bom_id: int
    product_id: int
    product_name: str
    batch_size_packets: int
    planned_batches: int
    planned_output_packets: int
    tolerance_pct: Decimal
    items: List[BOMItemPrefill]

class ProductionIssueItemCreate(BaseModel):
    raw_material_id: int
    actual_qty_base: Decimal = Field(..., gt=0)

class ProductionOverheadCreate(BaseModel):
    overhead_type: str = Field(..., description="'labour', 'gas_power', etc.")
    amount_paise: int = Field(..., gt=0, description="Amount in paise (e.g. 120000 = Rs 1,200)")
    notes: Optional[str] = None

class ProductionRunCreate(BaseModel):
    product_id: int
    bom_id: int
    planned_batches: int = Field(1, ge=1)
    actual_good_output_packets: int = Field(..., ge=1)
    actual_damaged_pouches: int = Field(0, ge=0)
    actual_cartons_used: int = Field(0, ge=0)
    issued_items: List[ProductionIssueItemCreate]
    overheads: List[ProductionOverheadCreate] = []

class ProductionRunItemResponse(BaseModel):
    id: int
    raw_material_id: int
    standard_qty_base: Decimal
    actual_qty_base: Decimal
    base_unit: str
    unit_cost_paise: Decimal
    variance_pct: Decimal
    variance_cost_paise: int
    is_flagged: bool

    model_config = ConfigDict(from_attributes=True)

class ProductionOverheadResponse(BaseModel):
    id: int
    overhead_type: str
    amount_paise: int
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProductionRunResponse(BaseModel):
    id: int
    run_no: str
    bom_id: int
    product_id: int
    planned_batches: int
    planned_output_packets: int
    actual_good_output_packets: int
    actual_damaged_pouches: int
    actual_cartons_used: int
    yield_variance_pct: Decimal
    is_yield_flagged: bool
    total_material_cost_paise: int
    total_overhead_cost_paise: int
    cost_per_packet_paise: int
    created_by: int
    created_at: datetime
    items: List[ProductionRunItemResponse]
    overheads: List[ProductionOverheadResponse]

    model_config = ConfigDict(from_attributes=True)
