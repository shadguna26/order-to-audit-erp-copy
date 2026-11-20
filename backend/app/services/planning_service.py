import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.master import Product, BOM, RawMaterial
from app.models.sales import Order, OrderItem, OrderStatus
from app.models.stock import StockItemType, StockLocationType
from app.services.ledger_service import get_item_stock_balance
from app.services.unit_service import format_base_quantity_for_display

def get_production_plan_from_pending_orders(db: Session) -> List[Dict[str, Any]]:
    """
    FEATURE: Production planning from pending orders:
    'To fulfil approved orders, make N batches'.
    Computes approved order quantities not yet dispatched, compares with current finished stock,
    and calculates batches required to produce along with required raw materials.
    """
    # 1. Sum up approved order requirements for each product
    approved_items = db.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity_packets).label("total_demand_packets")
    ).join(Order).filter(
        Order.status == OrderStatus.APPROVED
    ).group_by(OrderItem.product_id).all()

    plan = []
    for product_id, demand in approved_items:
        product = db.query(Product).filter(Product.id == product_id).first()
        bom = db.query(BOM).filter(BOM.product_id == product_id).first()
        if not product or not bom:
            continue

        demand_pkts = int(demand)
        current_stock = int(get_item_stock_balance(db, StockItemType.FINISHED_GOODS, product.id, StockLocationType.FINISHED))
        shortfall = max(0, demand_pkts - current_stock)

        batches_needed = 0
        if shortfall > 0 and bom.expected_yield_packets > 0:
            batches_needed = math.ceil(shortfall / bom.expected_yield_packets)

        # Materials needed for these batches
        required_materials = []
        if batches_needed > 0:
            for b_item in bom.items:
                rm = b_item.raw_material
                qty_needed = b_item.standard_qty_base * batches_needed
                curr_rm_stock = get_item_stock_balance(db, StockItemType.RAW_MATERIAL, rm.id)
                disp_needed, disp_unit = format_base_quantity_for_display(qty_needed, rm.base_unit)
                disp_stock, _ = format_base_quantity_for_display(curr_rm_stock, rm.base_unit)

                required_materials.append({
                    "raw_material_id": rm.id,
                    "code": rm.code,
                    "name": rm.name,
                    "qty_needed_base": qty_needed,
                    "display_needed": disp_needed,
                    "display_unit": disp_unit,
                    "current_stock_base": curr_rm_stock,
                    "display_current_stock": disp_stock,
                    "is_sufficient": curr_rm_stock >= qty_needed
                })

        plan.append({
            "product_id": product.id,
            "product_code": product.code,
            "product_name": product.name,
            "approved_demand_packets": demand_pkts,
            "current_stock_packets": current_stock,
            "net_shortfall_packets": shortfall,
            "batches_to_produce": batches_needed,
            "yield_per_batch": bom.expected_yield_packets,
            "estimated_output_packets": batches_needed * bom.expected_yield_packets,
            "recommendation": f"To fulfil approved orders, make {batches_needed} batch{'es' if batches_needed != 1 else ''} of {product.name}" if batches_needed > 0 else "Sufficient stock available",
            "required_materials": required_materials
        })

    return plan
