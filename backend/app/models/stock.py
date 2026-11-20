import enum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Numeric, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
from app.models.master import BaseUnitType

class StockItemType(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    FINISHED_GOODS = "finished_goods"

class StockLocationType(str, enum.Enum):
    RAW = "raw"
    PACKAGING = "packaging"
    FINISHED = "finished"

class StockDirection(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"

class StockDocType(str, enum.Enum):
    OPENING_BALANCE = "opening_balance"
    PURCHASE = "purchase"
    PRODUCTION_ISSUE = "production_issue"
    PRODUCTION_OUTPUT = "production_output"
    DISPATCH = "dispatch"
    CREDIT_NOTE_RETURN = "credit_note_return"
    ADJUSTMENT = "adjustment"

class StockLedger(Base):
    """
    NON-NEGOTIABLE RULE 1:
    A single append-only stock_ledger table is the source of truth.
    Every row has item, location type, qty in base unit, direction,
    source document type + id, batch no (optional), user, timestamp.
    Balances are SUMs of the ledger. Never overwrite a balance.
    """
    __tablename__ = "stock_ledger"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_type = Column(Enum(StockItemType), nullable=False)
    item_id = Column(Integer, nullable=False)                      # raw_materials.id or products.id
    location_type = Column(Enum(StockLocationType), nullable=False)
    direction = Column(Enum(StockDirection), nullable=False)      # IN or OUT
    qty_base = Column(Numeric(14, 4), nullable=False)             # Always positive Decimal in base units (g, ml, piece)
    base_unit = Column(Enum(BaseUnitType), nullable=False)
    unit_cost_paise = Column(Numeric(14, 4), nullable=False, default=0) # Valuation at transaction time in paise/base unit
    source_doc_type = Column(Enum(StockDocType), nullable=False)
    source_doc_id = Column(Integer, nullable=False)               # Foreign ID of source transaction
    batch_no = Column(String(50), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_stock_ledger_item", "item_type", "item_id"),
        Index("ix_stock_ledger_source", "source_doc_type", "source_doc_id"),
    )
