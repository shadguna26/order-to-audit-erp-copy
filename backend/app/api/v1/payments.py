from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.billing import Payment
from app.models.master import Customer
from app.schemas.billing import (
    PaymentCreate,
    PaymentResponse,
    CustomerBalanceResponse
)
from app.services.billing_service import (
    record_customer_payment,
    get_customer_outstanding_paise
)

router = APIRouter(prefix="/payments", tags=["Payments & Collections"])

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def receive_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """
    BENCHMARK STEP 7:
    Record payment against customer account (paise integer).
    """
    try:
        payment = record_customer_payment(
            db=db,
            customer_id=payment_in.customer_id,
            amount_paise=payment_in.amount_paise,
            payment_mode=payment_in.payment_mode,
            reference_no=payment_in.reference_no,
            notes=payment_in.notes,
            user_id=current_user.id
        )
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[PaymentResponse])
def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Payment).order_by(Payment.id.desc()).all()

@router.get("/customer/{customer_id}/outstanding", response_model=CustomerBalanceResponse)
def get_customer_balance(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    outstanding = get_customer_outstanding_paise(db, customer_id)
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "outstanding_paise": outstanding,
        "credit_limit_paise": customer.credit_limit_paise
    }
