from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Numeric, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.master import BaseUnitType

class ProductionRun(Base):
    """
    Tracks manufacturing batches, standard vs actual usage, good output,
    damaged packaging, variances, and overheads.
    """
    __tablename__ = "production_runs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True, default=1)
    run_no = Column(String(50), nullable=False, index=True) # PR/2026-27/0001
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    planned_batches = Column(Integer, nullable=False, default=1)
    planned_output_packets = Column(Integer, nullable=False)            # e.g. 200
    actual_good_output_packets = Column(Integer, nullable=False)        # e.g. 188
    actual_damaged_pouches = Column(Integer, nullable=False, default=0) # e.g. 6
    actual_cartons_used = Column(Integer, nullable=False, default=0)    # e.g. 9
    yield_variance_pct = Column(Numeric(6, 2), nullable=False)          # e.g. -6.00%
    is_yield_flagged = Column(Boolean, nullable=False, default=False)
    total_material_cost_paise = Column(BigInteger, nullable=False, default=0)
    total_overhead_cost_paise = Column(BigInteger, nullable=False, default=0)
    cost_per_packet_paise = Column(BigInteger, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("business_id", "run_no", name="uq_production_runs_biz_no"),
    )

    bom = relationship("BOM")
    product = relationship("Product")
    creator = relationship("User")
    items = relationship("ProductionRunItem", back_populates="production_run", cascade="all, delete-orphan")
    overheads = relationship("ProductionOverhead", back_populates="production_run", cascade="all, delete-orphan")

class ProductionRunItem(Base):
    __tablename__ = "production_run_items"

    id = Column(Integer, primary_key=True, index=True)
    production_run_id = Column(Integer, ForeignKey("production_runs.id", ondelete="CASCADE"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    standard_qty_base = Column(Numeric(14, 4), nullable=False)
    actual_qty_base = Column(Numeric(14, 4), nullable=False)
    base_unit = Column(String(20), nullable=False)
    unit_cost_paise = Column(Numeric(14, 4), nullable=False)           # Weighted average cost in paise/base unit
    variance_pct = Column(Numeric(6, 2), nullable=False)               # ((actual - standard)/standard) * 100
    variance_cost_paise = Column(BigInteger, nullable=False)           # Difference in rupees (in paise)
    is_flagged = Column(Boolean, nullable=False, default=False)        # True if abs(variance_pct) > tolerance

    production_run = relationship("ProductionRun", back_populates="items")
    raw_material = relationship("RawMaterial")

class ProductionOverhead(Base):
    __tablename__ = "production_overheads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True, default=1)
    production_run_id = Column(Integer, ForeignKey("production_runs.id", ondelete="CASCADE"), nullable=False)
    overhead_type = Column(String(50), nullable=False)                 # 'labour', 'gas_power', 'other'
    amount_paise = Column(BigInteger, nullable=False)                  # In paise (e.g. 120000 = Rs 1,200)
    notes = Column(Text, nullable=True)

    production_run = relationship("ProductionRun", back_populates="overheads")
