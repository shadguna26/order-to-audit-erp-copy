import enum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Numeric, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class OrderStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    INVOICED = "invoiced"
    DISPATCHED = "dispatched"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True) # SO/2026-27/0001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    salesman_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.SUBMITTED)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer")
    salesman = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_packets = Column(Integer, nullable=False)
    unit_price_paise = Column(BigInteger, nullable=False)              # In paise
    tax_rate_pct = Column(Numeric(5, 2), nullable=False, default=5.00)
    subtotal_paise = Column(BigInteger, nullable=False)
    cgst_paise = Column(BigInteger, nullable=False, default=0)
    sgst_paise = Column(BigInteger, nullable=False, default=0)
    igst_paise = Column(BigInteger, nullable=False, default=0)
    total_paise = Column(BigInteger, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Dispatch(Base):
    """
    NON-NEGOTIABLE RULE 6:
    Stock movements for dispatch happen at dispatch, not at order time.
    """
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_no = Column(String(50), unique=True, nullable=False, index=True) # DSP/2026-27/0001
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    vehicle_no = Column(String(30), nullable=True)
    driver_phone = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order")
    invoice = relationship("Invoice")
    creator = relationship("User")
