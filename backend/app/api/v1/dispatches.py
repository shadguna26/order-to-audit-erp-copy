from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.sales import Dispatch
from app.schemas.sales import DispatchCreate, DispatchResponse
from app.services.billing_service import record_dispatch_for_invoice

router = APIRouter(prefix="/dispatches", tags=["Dispatch & Delivery"])

@router.post("", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def create_dispatch(
    dispatch_in: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """
    NON-NEGOTIABLE RULE 6:
    Stock movements for dispatch happen at dispatch, not at order time.
    Posts finished goods OUT movement to stock_ledger.
    """
    try:
        dispatch = record_dispatch_for_invoice(
            db=db,
            invoice_id=dispatch_in.invoice_id,
            vehicle_no=dispatch_in.vehicle_no,
            driver_phone=dispatch_in.driver_phone,
            notes=dispatch_in.notes,
            user_id=current_user.id
        )
        return dispatch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[DispatchResponse])
def list_dispatches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Dispatch).order_by(Dispatch.id.desc()).all()
