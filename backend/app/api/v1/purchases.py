from typing import List
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.billing import Purchase, PurchaseItem, PurchaseStatus
from app.models.master import RawMaterial, Supplier, MaterialType
from app.models.stock import StockItemType, StockLocationType, StockDirection, StockDocType
from app.schemas.purchases import PurchaseCreate, PurchaseResponse
from app.services.sequence_service import generate_document_sequence
from app.services.unit_service import convert_to_base_unit
from app.services.ledger_service import record_stock_movement
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/purchases", tags=["Purchases & Inward Goods"])

@router.post("", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    purchase_in: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER]))
):
    """
    BENCHMARK STEP 1:
    Record incoming raw material/packaging purchase.
    Atomically updates:
    1. purchases & purchase_items
    2. stock_ledger (IN movement with unit cost valuation in base units)
    3. audit_log
    """
    supplier = db.query(Supplier).filter(Supplier.id == purchase_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    purchase_no = generate_document_sequence(
        db,
        model_class=Purchase,
        no_column=Purchase.purchase_no,
        prefix="PO",
        target_date=purchase_in.invoice_date
    )

    purchase = Purchase(
        purchase_no=purchase_no,
        supplier_id=purchase_in.supplier_id,
        supplier_invoice_no=purchase_in.supplier_invoice_no,
        invoice_date=purchase_in.invoice_date,
        status=PurchaseStatus.RECEIVED,
        created_by=current_user.id
    )
    db.add(purchase)
    db.flush()

    total_purchase_amount_paise = 0
    audit_items_data = []

    for item_in in purchase_in.items:
        rm = db.query(RawMaterial).filter(RawMaterial.id == item_in.raw_material_id).first()
        if not rm:
            raise HTTPException(status_code=404, detail=f"Raw Material with id {item_in.raw_material_id} not found")

        # Convert input quantity to base unit (e.g. 60 kg -> 60,000 g)
        qty_base = convert_to_base_unit(
            quantity=item_in.input_qty,
            from_unit=item_in.input_unit,
            target_base_unit=rm.base_unit
        )

        # Calculate line item total in paise:
        # e.g. 60 kg * 4500 paise/kg = 270,000 paise (Rs 2,700)
        line_total_paise = int(item_in.input_qty * Decimal(item_in.rate_paise_per_unit))
        total_purchase_amount_paise += line_total_paise

        # Unit cost valuation per base unit in paise (e.g. 270,000 paise / 60,000 g = 4.5000 paise/g)
        unit_cost_base_paise = (Decimal(line_total_paise) / qty_base).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if qty_base > 0 else Decimal("0.0000")

        p_item = PurchaseItem(
            purchase_id=purchase.id,
            raw_material_id=rm.id,
            input_qty=item_in.input_qty,
            input_unit=item_in.input_unit.strip().lower(),
            qty_base=qty_base,
            rate_paise_per_unit=item_in.rate_paise_per_unit,
            total_amount_paise=line_total_paise
        )
        db.add(p_item)

        # Determine location type: raw material store vs packaging store
        loc_type = StockLocationType.PACKAGING if rm.type == MaterialType.PACKAGING else StockLocationType.RAW

        # NON-NEGOTIABLE RULE 1: Append-only write to stock_ledger
        record_stock_movement(
            db=db,
            item_type=StockItemType.RAW_MATERIAL,
            item_id=rm.id,
            location_type=loc_type,
            direction=StockDirection.IN,
            qty_base=qty_base,
            base_unit=rm.base_unit,
            unit_cost_paise=unit_cost_base_paise,
            source_doc_type=StockDocType.PURCHASE,
            source_doc_id=purchase.id,
            created_by=current_user.id
        )

        audit_items_data.append({
            "raw_material": rm.code,
            "input_qty": str(item_in.input_qty),
            "input_unit": item_in.input_unit,
            "qty_base": str(qty_base),
            "total_paise": line_total_paise
        })

    purchase.total_amount_paise = total_purchase_amount_paise

    # Audit log entry
    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="purchases",
        record_id=purchase.id,
        action="INSERT",
        new_values={
            "purchase_no": purchase.purchase_no,
            "total_paise": total_purchase_amount_paise,
            "items": audit_items_data
        }
    )

    db.commit()
    db.refresh(purchase)
    return purchase

@router.get("", response_model=List[PurchaseResponse])
def list_purchases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Purchase).order_by(Purchase.id.desc()).all()

@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase
