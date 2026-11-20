from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.sales import Order, OrderStatus
from app.schemas.sales import (
    OrderCreate,
    OrderResponse,
    StockCoverageResponse
)
from app.services.order_service import (
    check_order_stock_coverage,
    create_customer_order
)
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/orders", tags=["Orders & Sales"])

@router.get("/check-stock/{product_id}", response_model=StockCoverageResponse)
def check_stock(
    product_id: int,
    quantity: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    NON-NEGOTIABLE BUSINESS LOGIC:
    Order stock check: show whether finished-goods stock covers each order line.
    On shortage, say e.g. 'Only 88 packets in stock. Short by 32.'
    and suggest number of batches to produce.
    """
    return check_order_stock_coverage(db, product_id=product_id, requested_packets=quantity)

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def submit_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SALESMAN, UserRole.ADMIN, UserRole.OWNER]))
):
    """Salesman submits order for customer."""
    try:
        order = create_customer_order(
            db=db,
            customer_id=order_in.customer_id,
            salesman_id=current_user.id,
            items=[item.model_dump() for item in order_in.items],
            notes=order_in.notes
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[OrderResponse])
def list_orders(
    status_filter: OrderStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order)
    # Salesman can only see their own orders
    if current_user.role == UserRole.SALESMAN:
        query = query.filter(Order.salesman_id == current_user.id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    return query.order_by(Order.id.desc()).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.SALESMAN and order.salesman_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view other salesmen's orders")
    return order

@router.post("/{order_id}/approve", response_model=OrderResponse)
def approve_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """Admin or Owner approves incoming sales order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail=f"Cannot approve order in status {order.status.value}")

    old_status = order.status.value
    order.status = OrderStatus.APPROVED

    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="orders",
        record_id=order.id,
        action="UPDATE",
        old_values={"status": old_status},
        new_values={"status": "approved"}
    )
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/reject", response_model=OrderResponse)
def reject_order(
    order_id: int,
    reason: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail=f"Cannot reject order in status {order.status.value}")

    order.status = OrderStatus.REJECTED
    order.rejection_reason = reason
    db.commit()
    db.refresh(order)
    return order
