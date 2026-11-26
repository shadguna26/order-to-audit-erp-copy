import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.models.master import (
    BOM,
    BOMItem,
    BaseUnitType,
    MaterialType,
    PriceList,
    Product,
    RawMaterial,
)
from app.models.production import ProductionRun
from app.models.sales import OrderItem
from app.models.billing import InvoiceItem
from app.models.stock import (
    StockDocType,
    StockDirection,
    StockItemType,
    StockLedger,
    StockLocationType,
)
from app.schemas.master import (
    BOMDetail,
    BOMItemDetail,
    ProductCreate,
    ProductDuplicateRequest,
    ProductResponse,
    ProductUpdate,
    RawMaterialCreate,
    RawMaterialResponse,
    RawMaterialUpdate,
    compute_pack_size_g,
)
from app.services.audit_service import log_audit_event
from app.services.ledger_service import get_item_stock_balance, record_stock_movement

router = APIRouter(tags=["Products & Raw Materials"])


def _auto_product_code(db: Session, name: str, pack_val: Decimal, pack_unit: str) -> str:
    slug = re.sub(r"[^A-Z0-9]", "", name.upper())[:4] or "SNK"
    size_str = f"{int(pack_val)}{pack_unit.upper()}" if pack_val == int(pack_val) else f"{pack_val}{pack_unit.upper()}"
    base = f"FG-{slug}-{size_str}"
    candidate = base
    idx = 1
    while db.query(Product).filter(Product.code == candidate).first():
        idx += 1
        candidate = f"{base}-{idx}"
    return candidate


def _auto_material_code(db: Session, name: str, mat_type: MaterialType) -> str:
    prefix = "PKG" if mat_type == MaterialType.PACKAGING else "RM"
    slug = re.sub(r"[^A-Z0-9]", "", name.upper())[:6] or "MAT"
    base = f"{prefix}-{slug}"
    candidate = base
    idx = 1
    while db.query(RawMaterial).filter(RawMaterial.code == candidate).first():
        idx += 1
        candidate = f"{base}-{idx}"
    return candidate


def _serialize_product(db: Session, product: Product) -> ProductResponse:
    balance = int(
        get_item_stock_balance(
            db,
            item_type=StockItemType.FINISHED_GOODS,
            item_id=product.id,
            location_type=StockLocationType.FINISHED,
        )
    )
    active_bom = (
        db.query(BOM)
        .filter(BOM.product_id == product.id, BOM.is_active == True)
        .order_by(BOM.id.desc())
        .first()
    )
    bom_detail = None
    if active_bom:
        bom_items = []
        for item in active_bom.items:
            rm = item.raw_material
            bom_items.append(
                BOMItemDetail(
                    id=item.id,
                    raw_material_id=item.raw_material_id,
                    raw_material_code=rm.code if rm else "",
                    raw_material_name=rm.name if rm else "",
                    material_type=rm.type.value if rm else "raw",
                    standard_qty_base=item.standard_qty_base,
                    base_unit=item.base_unit,
                )
            )
        bom_detail = BOMDetail(
            id=active_bom.id,
            name=active_bom.name,
            batch_size_packets=active_bom.batch_size_packets,
            expected_yield_packets=active_bom.expected_yield_packets,
            tolerance_pct=active_bom.tolerance_pct,
            items=bom_items,
        )

    return ProductResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        name_ta=product.name_ta,
        voice_aliases=product.voice_aliases,
        category=product.category,
        hsn_code=product.hsn_code,
        gst_rate_pct=product.gst_rate_pct,
        pack_size_g=product.pack_size_g,
        pack_size_value=product.pack_size_value,
        pack_size_unit=product.pack_size_unit,
        packets_per_carton=product.packets_per_carton,
        selling_price_paise=product.selling_price_paise,
        shelf_life_days=product.shelf_life_days,
        reorder_level_packets=product.reorder_level_packets,
        base_unit=product.base_unit,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        balance_packets=balance,
        bom=bom_detail,
    )


# ---------------------------------------------------------------------------
# RAW MATERIALS
# ---------------------------------------------------------------------------

@router.get("/raw-materials", response_model=List[RawMaterialResponse])
def list_raw_materials(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(RawMaterial)
    if not include_inactive:
        q = q.filter(RawMaterial.is_active == True)
    return q.order_by(RawMaterial.id.asc()).all()


@router.post("/raw-materials", response_model=RawMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_raw_material(
    rm_in: RawMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER])),
):
    code = (rm_in.code or "").strip().upper() or _auto_material_code(db, rm_in.name, rm_in.type)
    if db.query(RawMaterial).filter(RawMaterial.code == code).first():
        raise HTTPException(status_code=400, detail=f"Raw material code '{code}' already exists")

    rm = RawMaterial(
        code=code,
        name=rm_in.name.strip(),
        type=rm_in.type,
        base_unit=rm_in.base_unit,
        unit_conversions=rm_in.unit_conversions,
        reorder_level_base=rm_in.reorder_level_base,
        is_active=True,
    )
    db.add(rm)
    db.flush()

    if rm_in.opening_stock_base and rm_in.opening_stock_base > 0:
        loc = StockLocationType.PACKAGING if rm.type == MaterialType.PACKAGING else StockLocationType.RAW
        record_stock_movement(
            db=db,
            item_type=StockItemType.RAW_MATERIAL,
            item_id=rm.id,
            location_type=loc,
            direction=StockDirection.IN,
            qty_base=rm_in.opening_stock_base,
            base_unit=rm.base_unit,
            unit_cost_paise=rm_in.opening_unit_cost_paise,
            source_doc_type=StockDocType.OPENING_BALANCE,
            source_doc_id=rm.id,
            created_by=current_user.id,
            batch_no=rm_in.batch_no,
            expiry_date=rm_in.expiry_date,
        )

    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="raw_materials",
        record_id=rm.id,
        action="INSERT",
        new_values={"code": rm.code, "name": rm.name, "type": rm.type.value, "base_unit": rm.base_unit.value},
    )
    db.commit()
    db.refresh(rm)
    return rm


@router.put("/raw-materials/{rm_id}", response_model=RawMaterialResponse)
def update_raw_material(
    rm_id: int,
    rm_in: RawMaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER])),
):
    rm = db.query(RawMaterial).filter(RawMaterial.id == rm_id).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Raw material not found")

    old_vals = {"name": rm.name, "type": rm.type.value, "reorder_level_base": str(rm.reorder_level_base), "is_active": rm.is_active}
    for field in ("name", "type", "base_unit", "unit_conversions", "reorder_level_base", "is_active"):
        val = getattr(rm_in, field)
        if val is not None:
            setattr(rm, field, val)

    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="raw_materials",
        record_id=rm.id,
        action="UPDATE",
        old_values=old_vals,
        new_values={"name": rm.name, "type": rm.type.value, "reorder_level_base": str(rm.reorder_level_base), "is_active": rm.is_active},
    )
    db.commit()
    db.refresh(rm)
    return rm


# ---------------------------------------------------------------------------
# PRODUCTS & RECIPES (BOM)
# ---------------------------------------------------------------------------

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    include_inactive: bool = Query(False),
    updated_since: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Product)
    if not include_inactive:
        q = q.filter(Product.is_active == True)
    if updated_since:
        q = q.filter(Product.updated_at >= updated_since)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            or_(
                Product.name.ilike(like),
                Product.name_ta.ilike(like),
                Product.code.ilike(like),
                Product.voice_aliases.ilike(like),
            )
        )
    products = q.order_by(Product.id.asc()).all()
    return [_serialize_product(db, p) for p in products]


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _serialize_product(db, product)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    code = (prod_in.code or "").strip().upper() or _auto_product_code(
        db, prod_in.name, prod_in.pack_size_value, prod_in.pack_size_unit
    )
    if db.query(Product).filter(Product.code == code).first():
        raise HTTPException(status_code=400, detail=f"Product code '{code}' already exists")

    pack_size_g = compute_pack_size_g(prod_in.pack_size_value, prod_in.pack_size_unit)

    product = Product(
        code=code,
        name=prod_in.name.strip(),
        name_ta=prod_in.name_ta.strip() if prod_in.name_ta else None,
        voice_aliases=prod_in.voice_aliases.strip() if prod_in.voice_aliases else None,
        category=prod_in.category,
        hsn_code=prod_in.hsn_code,
        gst_rate_pct=prod_in.gst_rate_pct,
        pack_size_g=pack_size_g,
        pack_size_value=prod_in.pack_size_value,
        pack_size_unit=prod_in.pack_size_unit.strip(),
        packets_per_carton=prod_in.packets_per_carton,
        selling_price_paise=prod_in.selling_price_paise,
        shelf_life_days=prod_in.shelf_life_days,
        reorder_level_packets=prod_in.reorder_level_packets,
        base_unit=BaseUnitType.PIECE,
        is_active=prod_in.is_active,
    )
    db.add(product)
    db.flush()

    # Effective-dated price list entry for retailer & distributor
    now_utc = datetime.now(timezone.utc)
    db.add(PriceList(product_id=product.id, customer_type="retailer", price_paise=prod_in.selling_price_paise, effective_from=now_utc))
    db.add(PriceList(product_id=product.id, customer_type="distributor", price_paise=prod_in.selling_price_paise, effective_from=now_utc))

    # Optional BOM
    if prod_in.bom_items:
        bom = BOM(
            product_id=product.id,
            name=prod_in.bom_name or f"Standard Batch ({prod_in.expected_yield_packets} pkts)",
            batch_size_packets=prod_in.expected_yield_packets,
            expected_yield_packets=prod_in.expected_yield_packets,
            is_active=True,
        )
        db.add(bom)
        db.flush()
        for item in prod_in.bom_items:
            rm = db.query(RawMaterial).filter(RawMaterial.id == item.raw_material_id).first()
            if not rm:
                raise HTTPException(status_code=404, detail=f"Raw material {item.raw_material_id} not found")
            db.add(
                BOMItem(
                    bom_id=bom.id,
                    raw_material_id=rm.id,
                    standard_qty_base=item.standard_qty_base,
                    base_unit=item.base_unit or rm.base_unit,
                )
            )

    # Optional opening stock -> append-only stock_ledger
    if prod_in.opening_stock_packets and prod_in.opening_stock_packets > 0:
        record_stock_movement(
            db=db,
            item_type=StockItemType.FINISHED_GOODS,
            item_id=product.id,
            location_type=StockLocationType.FINISHED,
            direction=StockDirection.IN,
            qty_base=Decimal(prod_in.opening_stock_packets),
            base_unit=BaseUnitType.PIECE,
            unit_cost_paise=Decimal("0"),
            source_doc_type=StockDocType.OPENING_BALANCE,
            source_doc_id=product.id,
            created_by=current_user.id,
            batch_no=prod_in.batch_no,
            expiry_date=prod_in.expiry_date,
        )

    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="products",
        record_id=product.id,
        action="INSERT",
        new_values={
            "code": product.code,
            "name": product.name,
            "selling_price_paise": product.selling_price_paise,
            "gst_rate_pct": str(product.gst_rate_pct),
            "hsn_code": product.hsn_code,
        },
    )
    db.commit()
    db.refresh(product)
    return _serialize_product(db, product)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_vals = {
        "name": product.name,
        "selling_price_paise": product.selling_price_paise,
        "gst_rate_pct": str(product.gst_rate_pct),
        "hsn_code": product.hsn_code,
        "is_active": product.is_active,
    }

    for field in (
        "name",
        "name_ta",
        "voice_aliases",
        "category",
        "packets_per_carton",
        "selling_price_paise",
        "gst_rate_pct",
        "hsn_code",
        "shelf_life_days",
        "reorder_level_packets",
        "is_active",
    ):
        val = getattr(prod_in, field)
        if val is not None:
            setattr(product, field, val)

    if prod_in.pack_size_value is not None or prod_in.pack_size_unit is not None:
        val = prod_in.pack_size_value if prod_in.pack_size_value is not None else product.pack_size_value
        unit = prod_in.pack_size_unit if prod_in.pack_size_unit is not None else product.pack_size_unit
        product.pack_size_value = val
        product.pack_size_unit = unit
        product.pack_size_g = compute_pack_size_g(val, unit)

    effective_from = prod_in.effective_from or datetime.now(timezone.utc)
    if prod_in.selling_price_paise is not None and prod_in.selling_price_paise != old_vals["selling_price_paise"]:
        db.add(
            PriceList(
                product_id=product.id,
                customer_type="retailer",
                price_paise=prod_in.selling_price_paise,
                effective_from=effective_from,
            )
        )
        db.add(
            PriceList(
                product_id=product.id,
                customer_type="distributor",
                price_paise=prod_in.selling_price_paise,
                effective_from=effective_from,
            )
        )

    # Optional BOM update
    if prod_in.bom_items is not None:
        existing_bom = (
            db.query(BOM)
            .filter(BOM.product_id == product.id, BOM.is_active == True)
            .order_by(BOM.id.desc())
            .first()
        )
        yield_pkts = prod_in.expected_yield_packets or (existing_bom.expected_yield_packets if existing_bom else 200)
        if existing_bom:
            existing_bom.expected_yield_packets = yield_pkts
            existing_bom.batch_size_packets = yield_pkts
            db.query(BOMItem).filter(BOMItem.bom_id == existing_bom.id).delete()
            target_bom = existing_bom
        else:
            target_bom = BOM(
                product_id=product.id,
                name=f"Standard Batch ({yield_pkts} pkts)",
                batch_size_packets=yield_pkts,
                expected_yield_packets=yield_pkts,
                is_active=True,
            )
            db.add(target_bom)
            db.flush()

        for item in prod_in.bom_items:
            rm = db.query(RawMaterial).filter(RawMaterial.id == item.raw_material_id).first()
            if not rm:
                raise HTTPException(status_code=404, detail=f"Raw material {item.raw_material_id} not found")
            db.add(
                BOMItem(
                    bom_id=target_bom.id,
                    raw_material_id=rm.id,
                    standard_qty_base=item.standard_qty_base,
                    base_unit=item.base_unit or rm.base_unit,
                )
            )

    new_vals = {
        "name": product.name,
        "selling_price_paise": product.selling_price_paise,
        "gst_rate_pct": str(product.gst_rate_pct),
        "hsn_code": product.hsn_code,
        "is_active": product.is_active,
        "effective_from": effective_from.isoformat(),
    }
    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="products",
        record_id=product.id,
        action="UPDATE",
        old_values=old_vals,
        new_values=new_vals,
    )
    db.commit()
    db.refresh(product)
    return _serialize_product(db, product)


@router.post("/products/{product_id}/duplicate", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def duplicate_product(
    product_id: int,
    dup_in: ProductDuplicateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """
    Duplicate an existing product and copy its active BOM scaled by pack weight
    (e.g. 200 g -> 500 g scales raw material quantities by 2.5x while keeping piece packaging 1x per batch).
    """
    src = db.query(Product).filter(Product.id == product_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source product not found")

    new_pack_g = compute_pack_size_g(dup_in.pack_size_value, dup_in.pack_size_unit)
    src_pack_g = Decimal(str(src.pack_size_g or 200))
    scale_factor = new_pack_g / src_pack_g if src_pack_g > 0 else Decimal("1")

    code = (dup_in.code or "").strip().upper() or _auto_product_code(
        db, dup_in.name, dup_in.pack_size_value, dup_in.pack_size_unit
    )
    if db.query(Product).filter(Product.code == code).first():
        raise HTTPException(status_code=400, detail=f"Product code '{code}' already exists")

    default_price = dup_in.selling_price_paise
    if default_price is None:
        default_price = int((Decimal(src.selling_price_paise) * scale_factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    new_prod = Product(
        code=code,
        name=dup_in.name.strip(),
        name_ta=(dup_in.name_ta or src.name_ta),
        voice_aliases=src.voice_aliases,
        category=src.category,
        hsn_code=src.hsn_code,
        gst_rate_pct=src.gst_rate_pct,
        pack_size_g=new_pack_g,
        pack_size_value=dup_in.pack_size_value,
        pack_size_unit=dup_in.pack_size_unit.strip(),
        packets_per_carton=dup_in.packets_per_carton or src.packets_per_carton,
        selling_price_paise=default_price,
        shelf_life_days=src.shelf_life_days,
        reorder_level_packets=src.reorder_level_packets,
        base_unit=src.base_unit,
        is_active=True,
    )
    db.add(new_prod)
    db.flush()

    now_utc = datetime.now(timezone.utc)
    db.add(PriceList(product_id=new_prod.id, customer_type="retailer", price_paise=default_price, effective_from=now_utc))
    db.add(PriceList(product_id=new_prod.id, customer_type="distributor", price_paise=default_price, effective_from=now_utc))

    src_bom = (
        db.query(BOM)
        .filter(BOM.product_id == src.id, BOM.is_active == True)
        .order_by(BOM.id.desc())
        .first()
    )
    if src_bom:
        new_bom = BOM(
            product_id=new_prod.id,
            name=f"{new_prod.name} Batch ({src_bom.expected_yield_packets} pkts)",
            batch_size_packets=src_bom.batch_size_packets,
            expected_yield_packets=src_bom.expected_yield_packets,
            tolerance_pct=src_bom.tolerance_pct,
            is_active=True,
        )
        db.add(new_bom)
        db.flush()
        for item in src_bom.items:
            rm = item.raw_material
            # Scale raw ingredients (g/ml) by pack weight ratio; keep piece packaging (pouches/cartons) per-batch
            if rm and rm.base_unit == BaseUnitType.PIECE:
                scaled_qty = item.standard_qty_base
            else:
                scaled_qty = (Decimal(str(item.standard_qty_base)) * scale_factor).quantize(Decimal("0.0001"))
            db.add(
                BOMItem(
                    bom_id=new_bom.id,
                    raw_material_id=item.raw_material_id,
                    standard_qty_base=scaled_qty,
                    base_unit=item.base_unit,
                )
            )

    if dup_in.opening_stock_packets and dup_in.opening_stock_packets > 0:
        record_stock_movement(
            db=db,
            item_type=StockItemType.FINISHED_GOODS,
            item_id=new_prod.id,
            location_type=StockLocationType.FINISHED,
            direction=StockDirection.IN,
            qty_base=Decimal(dup_in.opening_stock_packets),
            base_unit=BaseUnitType.PIECE,
            unit_cost_paise=Decimal("0"),
            source_doc_type=StockDocType.OPENING_BALANCE,
            source_doc_id=new_prod.id,
            created_by=current_user.id,
            batch_no=dup_in.batch_no,
            expiry_date=dup_in.expiry_date,
        )

    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="products",
        record_id=new_prod.id,
        action="DUPLICATE",
        old_values={"source_product_id": src.id, "scale_factor": str(scale_factor)},
        new_values={"code": new_prod.code, "name": new_prod.name, "pack_size_g": str(new_pack_g)},
    )
    db.commit()
    db.refresh(new_prod)
    return _serialize_product(db, new_prod)


@router.delete("/products/{product_id}")
def delete_or_deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """
    Rule: products used in any transaction (orders, invoices, production runs, stock_ledger)
    cannot be deleted — they are deactivated instead (is_active = False).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    used_in_orders = db.query(OrderItem).filter(OrderItem.product_id == product_id).first() is not None
    used_in_invoices = db.query(InvoiceItem).filter(InvoiceItem.product_id == product_id).first() is not None
    used_in_prod = db.query(ProductionRun).filter(ProductionRun.product_id == product_id).first() is not None
    used_in_ledger = (
        db.query(StockLedger)
        .filter(StockLedger.item_type == StockItemType.FINISHED_GOODS, StockLedger.item_id == product_id)
        .first()
        is not None
    )

    if used_in_orders or used_in_invoices or used_in_prod or used_in_ledger:
        product.is_active = False
        log_audit_event(
            db=db,
            user_id=current_user.id,
            table_name="products",
            record_id=product.id,
            action="DEACTIVATE",
            old_values={"is_active": True},
            new_values={"is_active": False, "reason": "Product used in transactions"},
        )
        db.commit()
        return {
            "status": "deactivated",
            "deleted": False,
            "is_active": False,
            "message": "Product is used in transactions and was deactivated instead of deleted.",
        }

    # Unused product: safe to delete (including any unused BOMs & price list rows)
    db.query(PriceList).filter(PriceList.product_id == product_id).delete()
    db.query(BOM).filter(BOM.product_id == product_id).delete()
    db.delete(product)
    log_audit_event(
        db=db,
        user_id=current_user.id,
        table_name="products",
        record_id=product_id,
        action="DELETE",
        old_values={"code": product.code, "name": product.name},
    )
    db.commit()
    return {"status": "deleted", "deleted": True, "is_active": False}
