from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.production import ProductionRun
from app.schemas.production import (
    BOMPrefillResponse,
    ProductionRunCreate,
    ProductionRunResponse,
    ProductionOverheadCreate
)
from app.services.production_service import (
    get_bom_prefill_details,
    execute_production_run,
    add_overheads_to_run
)

router = APIRouter(prefix="/production", tags=["Production & Manufacturing"])

@router.get("/prefill/{bom_id}", response_model=BOMPrefillResponse)
def get_bom_prefill(
    bom_id: int,
    batches: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User selects product and batch count; system pre-fills BOM issue quantities.
    """
    try:
        return get_bom_prefill_details(db, bom_id=bom_id, planned_batches=batches)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/runs", response_model=ProductionRunResponse, status_code=status.HTTP_201_CREATED)
def create_production_run(
    run_in: ProductionRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER]))
):
    """
    BENCHMARK STEPS 2 & 3:
    Executes a production run:
    - Pre-filled BOM vs actual issues.
    - Yield variance and material variance calculations with tolerance alerts.
    - Material absorption with Weighted Average Cost.
    - Atomic posting to append-only stock_ledger and audit_log.
    """
    try:
        run = execute_production_run(
            db=db,
            product_id=run_in.product_id,
            bom_id=run_in.bom_id,
            planned_batches=run_in.planned_batches,
            actual_good_output_packets=run_in.actual_good_output_packets,
            actual_damaged_pouches=run_in.actual_damaged_pouches,
            actual_cartons_used=run_in.actual_cartons_used,
            issued_items=[item.model_dump() for item in run_in.issued_items],
            overheads=[oh.model_dump() for oh in run_in.overheads],
            created_by=current_user.id
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/runs/{run_id}/overheads", response_model=ProductionRunResponse)
def add_run_overheads(
    run_id: int,
    overheads: List[ProductionOverheadCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER]))
):
    """
    BENCHMARK STEP 8:
    Add labour Rs 1,200 and gas/power Rs 600 to the run; show cost per packet.
    """
    try:
        run = add_overheads_to_run(
            db=db,
            run_id=run_id,
            overheads=[oh.model_dump() for oh in overheads],
            user_id=current_user.id
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/runs", response_model=List[ProductionRunResponse])
def list_production_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ProductionRun).order_by(ProductionRun.id.desc()).all()

@router.get("/runs/{run_id}", response_model=ProductionRunResponse)
def get_production_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(ProductionRun).filter(ProductionRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return run
