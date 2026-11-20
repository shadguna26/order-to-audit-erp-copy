from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from app.models.stock import StockItemType, StockLocationType, StockDirection, StockDocType
from app.models.master import BaseUnitType

class StockMovementResponse(BaseModel):
    id: int
    item_type: StockItemType
    item_id: int
    location_type: StockLocationType
    direction: StockDirection
    qty_base: Decimal
    base_unit: BaseUnitType
    unit_cost_paise: int
    source_doc_type: StockDocType
    source_doc_id: int
    batch_no: Optional[str] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MaterialStockSummary(BaseModel):
    id: int
    code: str
    name: str
    type: str
    base_unit: str
    balance_base: Decimal
    display_quantity: str
    display_unit: str
    reorder_level_base: Decimal
    is_low_stock: bool

class FinishedGoodsStockSummary(BaseModel):
    id: int
    code: str
    name: str
    hsn_code: str
    pack_size_g: Decimal
    base_unit: str
    balance_packets: int
    display_quantity: str
    display_unit: str

class FullStockSummaryResponse(BaseModel):
    raw_and_packaging: List[MaterialStockSummary]
    finished_goods: List[FinishedGoodsStockSummary]
