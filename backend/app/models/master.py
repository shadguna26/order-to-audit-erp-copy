import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class MaterialType(str, enum.Enum):
    RAW = "raw"
    PACKAGING = "packaging"

class BaseUnitType(str, enum.Enum):
    G = "g"
    ML = "ml"
    PIECE = "piece"

class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)  # RM-FLOUR, PKG-POUCH-200G
    name = Column(String(100), nullable=False)                          # "Rice Flour", "Refined Sunflower Oil"
    type = Column(Enum(MaterialType), nullable=False)                   # raw or packaging
    base_unit = Column(Enum(BaseUnitType), nullable=False)              # g, ml, piece
    unit_conversions = Column(JSON, nullable=True)                      # e.g. {"kg": 1000, "bag_25kg": 25000}
    reorder_level_base = Column(Numeric(14, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)  # FG-MRK-200G
    name = Column(String(100), nullable=False)                          # "Kai Murukku 200g"
    name_ta = Column(String(120), nullable=True)                        # Optional Tamil name
    voice_aliases = Column(Text, nullable=True)                         # Comma-separated voice aliases
    category = Column(String(60), nullable=True, default="Snacks")
    hsn_code = Column(String(10), nullable=False, default="21069099")   # Indian GST HSN for savory snacks
    gst_rate_pct = Column(Numeric(5, 2), nullable=False, default=5.00)  # 5% GST
    pack_size_g = Column(Numeric(10, 2), nullable=False, default=200.00)
    pack_size_value = Column(Numeric(10, 2), nullable=False, default=200.00)
    pack_size_unit = Column(String(10), nullable=False, default="g")
    packets_per_carton = Column(Integer, nullable=False, default=20)
    selling_price_paise = Column(BigInteger, nullable=False, default=5000)
    shelf_life_days = Column(Integer, nullable=True, default=90)
    reorder_level_packets = Column(Integer, nullable=False, default=0)
    base_unit = Column(Enum(BaseUnitType), nullable=False, default=BaseUnitType.PIECE)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    boms = relationship("BOM", back_populates="product")

class BOM(Base):
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)                          # e.g. "Standard Batch (200 pkts)"
    batch_size_packets = Column(Integer, nullable=False, default=200)
    expected_yield_packets = Column(Integer, nullable=False, default=200)
    tolerance_pct = Column(Numeric(5, 2), nullable=False, default=3.00) # Variance threshold
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="boms")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")

class BOMItem(Base):
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bom.id", ondelete="CASCADE"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    standard_qty_base = Column(Numeric(14, 4), nullable=False)          # In base unit (g, ml, piece)
    base_unit = Column(Enum(BaseUnitType), nullable=False)

    bom = relationship("BOM", back_populates="items")
    raw_material = relationship("RawMaterial")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)                          # e.g. "Sri Murugan Stores"
    gstin = Column(String(15), nullable=True)                           # 33AAAAA1111A1Z1
    state = Column(String(50), nullable=False, default="Tamil Nadu")
    state_code = Column(String(2), nullable=False, default="33")        # TN is 33
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    customer_type = Column(String(30), nullable=False, default="retailer") # retailer, distributor
    credit_limit_paise = Column(BigInteger, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class PriceList(Base):
    __tablename__ = "price_list"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_type = Column(String(30), nullable=False)                  # 'retailer', 'distributor'
    price_paise = Column(BigInteger, nullable=False)                    # In paise (e.g. 5000 = Rs 50)
    effective_from = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    gstin = Column(String(15), nullable=True)
    state = Column(String(50), nullable=False, default="Tamil Nadu")
    state_code = Column(String(2), nullable=False, default="33")
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
