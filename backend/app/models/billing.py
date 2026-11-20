import enum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Enum, ForeignKey, Text, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PurchaseStatus(str, enum.Enum):
    RECEIVED = "received"
    CANCELLED = "cancelled"

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_no = Column(String(50), unique=True, nullable=False, index=True) # PO/2026-27/0001
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier_invoice_no = Column(String(50), nullable=True)
    invoice_date = Column(Date, nullable=False)
    total_amount_paise = Column(BigInteger, nullable=False, default=0)
    status = Column(Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.RECEIVED)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier = relationship("Supplier")
    creator = relationship("User")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    input_qty = Column(Numeric(14, 4), nullable=False)                # e.g. 60.0000 kg
    input_unit = Column(String(20), nullable=False)                    # 'kg', 'l', 'piece'
    qty_base = Column(Numeric(14, 4), nullable=False)                  # In base unit: 60000.0000 g
    rate_paise_per_unit = Column(BigInteger, nullable=False)           # e.g. 4500 paise per kg (Rs 45/kg)
    total_amount_paise = Column(BigInteger, nullable=False)            # e.g. 270000 paise (Rs 2,700)

    purchase = relationship("Purchase", back_populates="items")
    raw_material = relationship("RawMaterial")

class InvoiceStatus(str, enum.Enum):
    POSTED = "posted"
    CANCELLED = "cancelled"

class Invoice(Base):
    """
    NON-NEGOTIABLE RULE 3:
    Posted invoices cannot be edited or deleted.
    They are cancelled by a credit note.
    Invoice numbers follow financial year, e.g. TN/2026-27/0001.
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True) # TN/2026-27/0001
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.POSTED)
    subtotal_paise = Column(BigInteger, nullable=False)
    cgst_paise = Column(BigInteger, nullable=False, default=0)
    sgst_paise = Column(BigInteger, nullable=False, default=0)
    igst_paise = Column(BigInteger, nullable=False, default=0)
    total_paise = Column(BigInteger, nullable=False)
    pdf_path = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order")
    customer = relationship("Customer")
    creator = relationship("User")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_packets = Column(Integer, nullable=False)
    unit_price_paise = Column(BigInteger, nullable=False)
    subtotal_paise = Column(BigInteger, nullable=False)
    cgst_paise = Column(BigInteger, nullable=False, default=0)
    sgst_paise = Column(BigInteger, nullable=False, default=0)
    igst_paise = Column(BigInteger, nullable=False, default=0)
    total_paise = Column(BigInteger, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

class CreditNote(Base):
    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    credit_note_no = Column(String(50), unique=True, nullable=False, index=True) # CN/2026-27/0001
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    reason = Column(Text, nullable=False)
    total_paise = Column(BigInteger, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice = relationship("Invoice")
    creator = relationship("User")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String(50), unique=True, nullable=False, index=True) # REC/2026-27/0001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)                         # e.g. 400000 = Rs 4,000
    payment_mode = Column(String(30), nullable=False, default="cash")        # cash, upi, neft_rtgs, cheque
    reference_no = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("Customer")
    creator = relationship("User")
