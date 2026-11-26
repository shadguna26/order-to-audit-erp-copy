import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.billing import Invoice, CreditNote
from app.schemas.billing import (
    InvoiceResponse,
    CreditNoteCreate,
    CreditNoteResponse
)
from app.services.billing_service import (
    create_invoice_for_order,
    cancel_invoice_with_credit_note,
    generate_whatsapp_share_url
)
from app.services.pdf_service import generate_invoice_pdf, generate_credit_note_pdf

router = APIRouter(prefix="/invoices", tags=["Invoicing & Billing"])

@router.post("/from-order/{order_id}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def generate_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """
    NON-NEGOTIABLE RULE 3:
    Create posted tax invoice for approved order.
    Invoice numbers follow financial year, e.g. TN/2026-27/0001.
    """
    try:
        invoice = create_invoice_for_order(db=db, order_id=order_id, user_id=current_user.id)
        res = InvoiceResponse.model_validate(invoice)
        res.whatsapp_share_url = generate_whatsapp_share_url(invoice)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).order_by(Invoice.id.desc()).all()
    results = []
    for inv in invoices:
        r = InvoiceResponse.model_validate(inv)
        r.whatsapp_share_url = generate_whatsapp_share_url(inv)
        results.append(r)
    return results

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    res = InvoiceResponse.model_validate(invoice)
    res.whatsapp_share_url = generate_whatsapp_share_url(invoice)
    return res

@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT]))
):
    """Returns commercial GST Tax Invoice PDF."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_bytes = generate_invoice_pdf(invoice)
    clean_no = re.sub(r'[/\\:*?"<>|]', '-', invoice.invoice_no)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{clean_no}.pdf"',
            "Cache-Control": "no-store",
        }
    )

@router.get("/credit-notes/{credit_note_id}/pdf")
def download_credit_note_pdf(
    credit_note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT]))
):
    """Returns GST Credit Note PDF."""
    cn = db.query(CreditNote).filter(CreditNote.id == credit_note_id).first()
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    invoice = db.query(Invoice).filter(Invoice.id == cn.invoice_id).first()
    pdf_bytes = generate_credit_note_pdf(cn, invoice)
    clean_no = re.sub(r'[/\\:*?"<>|]', '-', cn.credit_note_no)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{clean_no}.pdf"',
            "Cache-Control": "no-store",
        }
    )

@router.post("/cancel", response_model=CreditNoteResponse)
def cancel_invoice(
    cn_in: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """
    NON-NEGOTIABLE RULE 3:
    Posted invoices cannot be edited or deleted. They are cancelled by a credit note.
    """
    try:
        cn = cancel_invoice_with_credit_note(
            db=db,
            invoice_id=cn_in.invoice_id,
            reason=cn_in.reason,
            user_id=current_user.id
        )
        return cn
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
