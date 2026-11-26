import urllib.parse
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.business import Business
from app.models.master import Customer, BaseUnitType
from app.models.sales import Order, OrderStatus, Dispatch
from app.models.billing import Invoice, InvoiceItem, InvoiceStatus, CreditNote, Payment
from app.models.stock import StockItemType, StockLocationType, StockDirection, StockDocType
from app.services.sequence_service import generate_document_sequence
from app.services.ledger_service import record_stock_movement
from app.services.audit_service import log_audit_event
from app.config import settings

def create_invoice_for_order(
    db: Session,
    order_id: int,
    user_id: int,
    business_id: int = 1,
) -> Invoice:
    """
    NON-NEGOTIABLE RULE 3:
    Posted invoices cannot be edited or deleted. They are cancelled by a credit note.
    Invoice numbers follow financial year, e.g. TN/2026-27/0001.
    """
    order = db.query(Order).filter(Order.id == order_id, Order.business_id == business_id).first()
    if not order:
        raise ValueError("Order not found")

    if order.status != OrderStatus.APPROVED:
        raise ValueError(f"Cannot invoice order with status '{order.status.value}'. Order must be approved first.")

    business = db.query(Business).filter(Business.id == business_id).first()
    inv_prefix = (business.invoice_prefix if business and business.invoice_prefix else "TN")

    invoice_no = generate_document_sequence(
        db,
        model_class=Invoice,
        no_column=Invoice.invoice_no,
        prefix=inv_prefix,
        business_id=business_id,
    )

    subtotal_paise = sum(item.subtotal_paise for item in order.items)
    cgst_paise = sum(item.cgst_paise for item in order.items)
    sgst_paise = sum(item.sgst_paise for item in order.items)
    igst_paise = sum(item.igst_paise for item in order.items)
    total_paise = sum(item.total_paise for item in order.items)

    invoice = Invoice(
        business_id=business_id,
        invoice_no=invoice_no,
        order_id=order.id,
        customer_id=order.customer_id,
        status=InvoiceStatus.POSTED,
        subtotal_paise=subtotal_paise,
        cgst_paise=cgst_paise,
        sgst_paise=sgst_paise,
        igst_paise=igst_paise,
        total_paise=total_paise,
        created_by=user_id
    )
    db.add(invoice)
    db.flush()

    for item in order.items:
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item.product_id,
            quantity_packets=item.quantity_packets,
            unit_price_paise=item.unit_price_paise,
            hsn_code=item.product.hsn_code if item.product else None,
            gst_rate_pct=item.tax_rate_pct,
            subtotal_paise=item.subtotal_paise,
            cgst_paise=item.cgst_paise,
            sgst_paise=item.sgst_paise,
            igst_paise=item.igst_paise,
            total_paise=item.total_paise
        )
        db.add(inv_item)

    order.status = OrderStatus.INVOICED

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="invoices",
        record_id=invoice.id,
        action="INSERT",
        new_values={
            "invoice_no": invoice.invoice_no,
            "order_id": order.id,
            "total_paise": total_paise
        }
    )

    db.commit()
    db.refresh(invoice)
    return invoice

def record_dispatch_for_invoice(
    db: Session,
    invoice_id: int,
    vehicle_no: Optional[str],
    driver_phone: Optional[str],
    notes: Optional[str],
    user_id: int,
    business_id: int = 1,
) -> Dispatch:
    """
    NON-NEGOTIABLE RULE 6:
    Stock movements for dispatch happen at dispatch, not at order time.
    Posts finished goods OUT movement to stock_ledger.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.business_id == business_id).first()
    if not invoice:
        raise ValueError("Invoice not found")

    order = invoice.order
    if order.status == OrderStatus.DISPATCHED:
        raise ValueError("Order has already been dispatched")

    dispatch_no = generate_document_sequence(
        db,
        model_class=Dispatch,
        no_column=Dispatch.dispatch_no,
        prefix="DSP",
        business_id=business_id,
    )

    dispatch = Dispatch(
        business_id=business_id,
        dispatch_no=dispatch_no,
        order_id=order.id,
        invoice_id=invoice.id,
        vehicle_no=vehicle_no,
        driver_phone=driver_phone,
        notes=notes,
        created_by=user_id
    )
    db.add(dispatch)
    db.flush()

    # NON-NEGOTIABLE RULE 6: Post OUT movements for each finished good
    for item in invoice.items:
        record_stock_movement(
            db=db,
            item_type=StockItemType.FINISHED_GOODS,
            item_id=item.product_id,
            location_type=StockLocationType.FINISHED,
            direction=StockDirection.OUT,
            qty_base=Decimal(item.quantity_packets),
            base_unit=BaseUnitType.PIECE,
            unit_cost_paise=Decimal(item.unit_price_paise),
            source_doc_type=StockDocType.DISPATCH,
            source_doc_id=dispatch.id,
            created_by=user_id,
            batch_no=dispatch.dispatch_no,
            business_id=business_id,
        )

    order.status = OrderStatus.DISPATCHED

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="dispatches",
        record_id=dispatch.id,
        action="INSERT",
        new_values={
            "dispatch_no": dispatch.dispatch_no,
            "invoice_no": invoice.invoice_no,
            "items_count": len(invoice.items)
        }
    )

    db.commit()
    db.refresh(dispatch)
    return dispatch

def cancel_invoice_with_credit_note(
    db: Session,
    invoice_id: int,
    reason: str,
    user_id: int,
    business_id: int = 1,
) -> CreditNote:
    """
    NON-NEGOTIABLE RULE 3:
    Posted invoices cannot be edited or deleted. They are cancelled by a credit note.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.business_id == business_id).first()
    if not invoice:
        raise ValueError("Invoice not found")

    if invoice.status == InvoiceStatus.CANCELLED:
        raise ValueError("Invoice is already cancelled")

    cn_no = generate_document_sequence(
        db,
        model_class=CreditNote,
        no_column=CreditNote.credit_note_no,
        prefix="CN",
        business_id=business_id,
    )

    credit_note = CreditNote(
        business_id=business_id,
        credit_note_no=cn_no,
        invoice_id=invoice.id,
        reason=reason,
        total_paise=invoice.total_paise,
        created_by=user_id
    )
    db.add(credit_note)

    invoice.status = InvoiceStatus.CANCELLED

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="invoices",
        record_id=invoice.id,
        action="CANCEL",
        old_values={"status": "posted"},
        new_values={"status": "cancelled", "credit_note_no": cn_no, "reason": reason}
    )

    db.commit()
    db.refresh(credit_note)
    return credit_note

def record_customer_payment(
    db: Session,
    customer_id: int,
    amount_paise: int,
    payment_mode: str,
    reference_no: Optional[str],
    notes: Optional[str],
    user_id: int,
    business_id: int = 1,
) -> Payment:
    """
    BENCHMARK STEP 7:
    Records customer payment and reflects immediately on ledger / outstanding.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.business_id == business_id).first()
    if not customer:
        raise ValueError("Customer not found")

    payment_no = generate_document_sequence(
        db,
        model_class=Payment,
        no_column=Payment.payment_no,
        prefix="REC",
        business_id=business_id,
    )

    payment = Payment(
        business_id=business_id,
        payment_no=payment_no,
        customer_id=customer_id,
        amount_paise=amount_paise,
        payment_mode=payment_mode,
        reference_no=reference_no,
        notes=notes,
        created_by=user_id
    )
    db.add(payment)
    db.flush()

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="payments",
        record_id=payment.id,
        action="INSERT",
        new_values={
            "payment_no": payment.payment_no,
            "customer": customer.name,
            "amount_paise": amount_paise
        }
    )

    db.commit()
    db.refresh(payment)
    return payment

def get_customer_outstanding_paise(db: Session, customer_id: int, business_id: int = 1) -> int:
    """
    Computes real-time customer balance:
    Total Posted Invoices - Total Active Credit Notes - Total Payments
    """
    total_invoiced = db.query(func.coalesce(func.sum(Invoice.total_paise), 0)).filter(
        Invoice.business_id == business_id,
        Invoice.customer_id == customer_id,
        Invoice.status == InvoiceStatus.POSTED
    ).scalar() or 0

    total_paid = db.query(func.coalesce(func.sum(Payment.amount_paise), 0)).filter(
        Payment.business_id == business_id,
        Payment.customer_id == customer_id
    ).scalar() or 0

    return int(total_invoiced - total_paid)

def generate_whatsapp_share_url(invoice: Invoice, company_name: Optional[str] = None) -> str:
    """
    Generates wa.me click-to-chat share URL for customer WhatsApp updates.
    """
    phone = (invoice.customer.phone or "").replace("+", "").replace(" ", "").replace("-", "")
    cust_name = invoice.customer.name
    total_rs = f"{invoice.total_paise / 100:.2f}"
    brand = company_name or settings.COMPANY_NAME
    text = (
        f"Namaskaram {cust_name}, your invoice {invoice.invoice_no} for Rs {total_rs} "
        f"from {brand} has been generated. Thank you!"
    )
    encoded = urllib.parse.quote(text)
    return f"https://wa.me/{phone}?text={encoded}"
