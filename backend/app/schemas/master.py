import re
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.master import BaseUnitType, MaterialType

HSN_REGEX = re.compile(r"^\d{4}(\d{2})?(\d{2})?$")


def compute_pack_size_g(value: Decimal, unit: str) -> Decimal:
    u = (unit or "g").strip().lower()
    if u in ("kg", "l"):
        return (value * Decimal("1000")).quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


class RawMaterialCreate(BaseModel):
    code: Optional[str] = Field(None, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    type: MaterialType
    base_unit: BaseUnitType
    unit_conversions: Optional[Dict[str, float]] = None
    reorder_level_base: Decimal = Field(Decimal("0"), ge=0)
    opening_stock_base: Optional[Decimal] = Field(None, gt=0)
    opening_unit_cost_paise: Decimal = Field(Decimal("0"), ge=0)
    batch_no: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None


class RawMaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[MaterialType] = None
    base_unit: Optional[BaseUnitType] = None
    unit_conversions: Optional[Dict[str, float]] = None
    reorder_level_base: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RawMaterialResponse(BaseModel):
    id: int
    code: str
    name: str
    type: MaterialType
    base_unit: BaseUnitType
    unit_conversions: Optional[Dict[str, float]] = None
    reorder_level_base: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BOMItemInput(BaseModel):
    raw_material_id: int
    standard_qty_base: Decimal = Field(..., gt=0)
    base_unit: Optional[BaseUnitType] = None


class BOMItemDetail(BaseModel):
    id: int
    raw_material_id: int
    raw_material_code: str
    raw_material_name: str
    material_type: str
    standard_qty_base: Decimal
    base_unit: BaseUnitType


class BOMDetail(BaseModel):
    id: int
    name: str
    batch_size_packets: int
    expected_yield_packets: int
    tolerance_pct: Decimal
    items: List[BOMItemDetail] = []


class ProductCreate(BaseModel):
    code: Optional[str] = Field(None, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=120)
    voice_aliases: Optional[str] = None
    category: Optional[str] = Field("Snacks", max_length=60)
    pack_size_value: Decimal = Field(Decimal("200"), gt=0)
    pack_size_unit: str = Field("g", max_length=10)
    packets_per_carton: int = Field(20, gt=0)
    selling_price_paise: int = Field(..., gt=0)
    gst_rate_pct: Decimal = Field(Decimal("5.00"), ge=0, le=100)
    hsn_code: str = Field("21069099", min_length=4, max_length=8)
    shelf_life_days: Optional[int] = Field(90, ge=0)
    reorder_level_packets: int = Field(0, ge=0)
    is_active: bool = True
    # Optional opening stock
    opening_stock_packets: Optional[int] = Field(None, gt=0)
    batch_no: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None
    # Optional BOM recipe
    bom_name: Optional[str] = None
    expected_yield_packets: int = Field(200, gt=0)
    bom_items: Optional[List[BOMItemInput]] = None

    @field_validator("hsn_code")
    @classmethod
    def validate_hsn(cls, v: str) -> str:
        clean = v.strip()
        if not HSN_REGEX.match(clean):
            raise ValueError("HSN code must be 4, 6, or 8 digits")
        return clean


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=120)
    voice_aliases: Optional[str] = None
    category: Optional[str] = Field(None, max_length=60)
    pack_size_value: Optional[Decimal] = Field(None, gt=0)
    pack_size_unit: Optional[str] = Field(None, max_length=10)
    packets_per_carton: Optional[int] = Field(None, gt=0)
    selling_price_paise: Optional[int] = Field(None, gt=0)
    gst_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    hsn_code: Optional[str] = Field(None, min_length=4, max_length=8)
    shelf_life_days: Optional[int] = Field(None, ge=0)
    reorder_level_packets: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    # Optional BOM update
    expected_yield_packets: Optional[int] = Field(None, gt=0)
    bom_items: Optional[List[BOMItemInput]] = None

    @field_validator("hsn_code")
    @classmethod
    def validate_hsn(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if not HSN_REGEX.match(clean):
            raise ValueError("HSN code must be 4, 6, or 8 digits")
        return clean


class ProductDuplicateRequest(BaseModel):
    code: Optional[str] = Field(None, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    name_ta: Optional[str] = Field(None, max_length=120)
    pack_size_value: Decimal = Field(..., gt=0)
    pack_size_unit: str = Field("g", max_length=10)
    packets_per_carton: Optional[int] = Field(None, gt=0)
    selling_price_paise: Optional[int] = Field(None, gt=0)
    opening_stock_packets: Optional[int] = Field(None, gt=0)
    batch_no: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None


class ProductResponse(BaseModel):
    id: int
    code: str
    name: str
    name_ta: Optional[str] = None
    voice_aliases: Optional[str] = None
    category: Optional[str] = None
    hsn_code: str
    gst_rate_pct: Decimal
    pack_size_g: Decimal
    pack_size_value: Decimal
    pack_size_unit: str
    packets_per_carton: int
    selling_price_paise: int
    shelf_life_days: Optional[int] = None
    reorder_level_packets: int
    base_unit: BaseUnitType
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    balance_packets: int = 0
    bom: Optional[BOMDetail] = None
