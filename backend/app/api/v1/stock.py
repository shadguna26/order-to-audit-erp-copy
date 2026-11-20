from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.stock import StockItemType, StockLocationType
from app.schemas.stock import FullStockSummaryResponse, StockMovementResponse
from app.services.ledger_service import (
    get_all_stock_summary,
    get_item_ledger_history,
    get_item_stock_balance
)

router = APIRouter(prefix="/stock", tags=["Stock & Ledger"])

@router.get("/summary", response_model=FullStockSummaryResponse)
def get_stock_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns current stock balances for all raw materials, packaging, and finished goods.
    Balances are dynamically computed as SUMs of the append-only stock_ledger.
    """
    return get_all_stock_summary(db)

@router.get("/ledger", response_model=List[StockMovementResponse])
def get_ledger(
    item_type: StockItemType = Query(...),
    item_id: int = Query(...),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    NON-NEGOTIABLE RULE 1:
    Clicking any stock number opens its ledger showing every movement and source document.
    """
    return get_item_ledger_history(db, item_type=item_type, item_id=item_id, limit=limit)
