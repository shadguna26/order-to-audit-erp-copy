from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.master import Product, BOM, BOMItem, RawMaterial, MaterialType, BaseUnitType
from app.models.stock import StockLedger, StockItemType, StockLocationType, StockDirection, StockDocType
from app.models.production import ProductionRun, ProductionRunItem, ProductionOverhead
from app.services.costing_service import calculate_weighted_average_cost
from app.services.sequence_service import generate_document_sequence
from app.services.ledger_service import record_stock_movement
from app.services.audit_service import log_audit_event
from app.services.unit_service import format_base_quantity_for_display

def get_bom_prefill_details(db: Session, bom_id: int, planned_batches: int = 1) -> Dict[str, Any]:
    """
    Pre-fills BOM issue quantities based on batch count.
    User selects product and batch count; system pre-fills BOM issue quantities.
    """
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not bom:
        raise ValueError("BOM not found")

    planned_output = bom.expected_yield_packets * planned_batches
    items_data = []

    for item in bom.items:
        rm = item.raw_material
        std_qty = item.standard_qty_base * Decimal(planned_batches)
        wac = calculate_weighted_average_cost(db, rm.id)
        disp_val, disp_unit = format_base_quantity_for_display(std_qty, rm.base_unit)

        items_data.append({
            "raw_material_id": rm.id,
            "code": rm.code,
            "name": rm.name,
            "type": rm.type.value,
            "standard_qty_base": std_qty,
            "base_unit": rm.base_unit.value,
            "display_quantity": disp_val,
            "display_unit": disp_unit,
            "unit_cost_wac_paise": wac
        })

    return {
        "bom_id": bom.id,
        "product_id": bom.product_id,
        "product_name": bom.product.name,
        "batch_size_packets": bom.batch_size_packets,
        "planned_batches": planned_batches,
        "planned_output_packets": planned_output,
        "tolerance_pct": bom.tolerance_pct,
        "items": items_data
    }

def execute_production_run(
    db: Session,
    product_id: int,
    bom_id: int,
    planned_batches: int,
    actual_good_output_packets: int,
    actual_damaged_pouches: int,
    actual_cartons_used: int,
    issued_items: List[Dict[str, Any]],
    overheads: List[Dict[str, Any]],
    created_by: int
) -> ProductionRun:
    """
    BENCHMARK STEPS 2, 3, & 8:
    Executes a production run atomically:
    1. Computes yield variance vs tolerance.
    2. Computes material usage variances and rupee values.
    3. Calculates Weighted Average Cost (WAC) material absorption + overheads.
    4. Posts raw/packaging OUT rows and finished-goods IN row to the ledger atomically.
    5. Writes to audit_log.
    """
    bom = db.query(BOM).filter(BOM.id == bom_id, BOM.product_id == product_id).first()
    if not bom:
        raise ValueError("Valid BOM for product not found")

    planned_output = bom.expected_yield_packets * planned_batches

    # 1. Yield Variance Calculation: ((actual - planned) / planned) * 100
    yield_var_dec = (
        (Decimal(actual_good_output_packets) - Decimal(planned_output)) / Decimal(planned_output) * Decimal("100.0")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    is_yield_flagged = abs(yield_var_dec) > bom.tolerance_pct

    run_no = generate_document_sequence(
        db,
        model_class=ProductionRun,
        no_column=ProductionRun.run_no,
        prefix="PR"
    )

    run = ProductionRun(
        run_no=run_no,
        bom_id=bom.id,
        product_id=product_id,
        planned_batches=planned_batches,
        planned_output_packets=planned_output,
        actual_good_output_packets=actual_good_output_packets,
        actual_damaged_pouches=actual_damaged_pouches,
        actual_cartons_used=actual_cartons_used,
        yield_variance_pct=yield_var_dec,
        is_yield_flagged=is_yield_flagged,
        created_by=created_by
    )
    db.add(run)
    db.flush()

    total_material_cost_paise = Decimal("0.0")
    audit_materials = []

    # Map standard BOM quantities for comparison
    bom_std_map = {item.raw_material_id: item.standard_qty_base * Decimal(planned_batches) for item in bom.items}

    # 2. Process Raw Materials & Packaging Issues
    for issued in issued_items:
        rm_id = issued["raw_material_id"]
        actual_qty = Decimal(str(issued["actual_qty_base"]))

        rm = db.query(RawMaterial).filter(RawMaterial.id == rm_id).first()
        if not rm:
            raise ValueError(f"Raw material {rm_id} not found")

        std_qty = bom_std_map.get(rm_id, actual_qty)
        wac = calculate_weighted_average_cost(db, rm_id)

        # Variance %: ((actual - standard) / standard) * 100
        if std_qty > Decimal("0"):
            mat_var_pct = ((actual_qty - std_qty) / std_qty * Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            mat_var_pct = Decimal("0.00")

        # Rupee variance = (actual - standard) * wac in paise
        var_cost_paise = int(round((actual_qty - std_qty) * wac))
        is_mat_flagged = abs(mat_var_pct) > bom.tolerance_pct

        line_material_cost = actual_qty * wac
        total_material_cost_paise += line_material_cost

        run_item = ProductionRunItem(
            production_run_id=run.id,
            raw_material_id=rm.id,
            standard_qty_base=std_qty,
            actual_qty_base=actual_qty,
            base_unit=rm.base_unit.value,
            unit_cost_paise=wac,
            variance_pct=mat_var_pct,
            variance_cost_paise=var_cost_paise,
            is_flagged=is_mat_flagged
        )
        db.add(run_item)

        # NON-NEGOTIABLE RULE 1: Post OUT row to stock_ledger
        loc_type = StockLocationType.PACKAGING if rm.type == MaterialType.PACKAGING else StockLocationType.RAW
        record_stock_movement(
            db=db,
            item_type=StockItemType.RAW_MATERIAL,
            item_id=rm.id,
            location_type=loc_type,
            direction=StockDirection.OUT,
            qty_base=actual_qty,
            base_unit=rm.base_unit,
            unit_cost_paise=wac,
            source_doc_type=StockDocType.PRODUCTION_ISSUE,
            source_doc_id=run.id,
            created_by=created_by,
            batch_no=run.run_no
        )

        audit_materials.append({
            "code": rm.code,
            "standard_qty": str(std_qty),
            "actual_qty": str(actual_qty),
            "variance_pct": str(mat_var_pct),
            "variance_cost_paise": var_cost_paise,
            "flagged": is_mat_flagged
        })

    # 3. Process Overheads
    total_overhead_cost_paise = 0
    for oh in overheads:
        amount = int(oh["amount_paise"])
        total_overhead_cost_paise += amount
        overhead_entry = ProductionOverhead(
            production_run_id=run.id,
            overhead_type=oh["overhead_type"],
            amount_paise=amount,
            notes=oh.get("notes")
        )
        db.add(overhead_entry)

    total_run_cost = total_material_cost_paise + Decimal(total_overhead_cost_paise)
    cost_per_packet = int(round(total_run_cost / Decimal(actual_good_output_packets))) if actual_good_output_packets > 0 else 0

    run.total_material_cost_paise = int(round(total_material_cost_paise))
    run.total_overhead_cost_paise = total_overhead_cost_paise
    run.cost_per_packet_paise = cost_per_packet

    # 4. NON-NEGOTIABLE RULE 1: Post Finished Goods IN row to stock_ledger
    record_stock_movement(
        db=db,
        item_type=StockItemType.FINISHED_GOODS,
        item_id=product_id,
        location_type=StockLocationType.FINISHED,
        direction=StockDirection.IN,
        qty_base=Decimal(actual_good_output_packets),
        base_unit=BaseUnitType.PIECE,
        unit_cost_paise=Decimal(cost_per_packet),
        source_doc_type=StockDocType.PRODUCTION_OUTPUT,
        source_doc_id=run.id,
        created_by=created_by,
        batch_no=run.run_no
    )

    # 5. Audit Log
    log_audit_event(
        db=db,
        user_id=created_by,
        table_name="production_runs",
        record_id=run.id,
        action="INSERT",
        new_values={
            "run_no": run.run_no,
            "actual_output": actual_good_output_packets,
            "yield_variance_pct": str(yield_var_dec),
            "cost_per_packet_paise": cost_per_packet,
            "materials": audit_materials
        }
    )

    db.commit()
    db.refresh(run)
    return run

def add_overheads_to_run(
    db: Session,
    run_id: int,
    overheads: List[Dict[str, Any]],
    user_id: int
) -> ProductionRun:
    """
    BENCHMARK STEP 8:
    Add labour Rs 1,200 and gas/power Rs 600 to the run; show cost per packet.
    Updates the run's absorbed cost and writes to audit_log.
    """
    run = db.query(ProductionRun).filter(ProductionRun.id == run_id).first()
    if not run:
        raise ValueError("Production run not found")

    old_overhead_paise = run.total_overhead_cost_paise
    old_cost_per_packet = run.cost_per_packet_paise

    added_overhead_paise = 0
    for oh in overheads:
        amount = int(oh["amount_paise"])
        added_overhead_paise += amount
        entry = ProductionOverhead(
            production_run_id=run.id,
            overhead_type=oh["overhead_type"],
            amount_paise=amount,
            notes=oh.get("notes")
        )
        db.add(entry)

    run.total_overhead_cost_paise += added_overhead_paise
    total_run_cost = Decimal(run.total_material_cost_paise) + Decimal(run.total_overhead_cost_paise)
    run.cost_per_packet_paise = int(round(total_run_cost / Decimal(run.actual_good_output_packets)))

    # Update the finished goods ledger valuation entry for this run
    fg_entry = db.query(StockLedger).filter(
        StockLedger.source_doc_type == StockDocType.PRODUCTION_OUTPUT,
        StockLedger.source_doc_id == run.id
    ).first()
    if fg_entry:
        fg_entry.unit_cost_paise = run.cost_per_packet_paise

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="production_runs",
        record_id=run.id,
        action="UPDATE",
        old_values={"total_overhead_paise": old_overhead_paise, "cost_per_packet_paise": old_cost_per_packet},
        new_values={"total_overhead_paise": run.total_overhead_cost_paise, "cost_per_packet_paise": run.cost_per_packet_paise}
    )

    db.commit()
    db.refresh(run)
    return run
