import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class BusinessType(str, enum.Enum):
    MANUFACTURER = "manufacturer"
    TRADER = "trader"


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    business_type = Column(Enum(BusinessType), nullable=False, default=BusinessType.MANUFACTURER)
    gstin = Column(String(15), nullable=True)
    state = Column(String(50), nullable=False, default="Tamil Nadu")
    state_code = Column(String(2), nullable=False, default="33")
    address = Column(Text, nullable=True)
    pincode = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    invoice_prefix = Column(String(10), nullable=False, default="TN")
    variance_tolerance_pct = Column(Numeric(5, 2), nullable=False, default=3.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DocumentSequence(Base):
    """Per-business, per-FY document sequence counter locked with FOR UPDATE."""
    __tablename__ = "document_sequences"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    doc_type = Column(String(30), nullable=False)  # invoice, order, purchase, dispatch, credit_note, payment, production_run
    prefix = Column(String(15), nullable=False)
    fy = Column(String(10), nullable=False)
    last_seq = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("business_id", "doc_type", "prefix", "fy", name="uq_doc_seq_biz_type_prefix_fy"),
    )
