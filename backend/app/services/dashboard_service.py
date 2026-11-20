from datetime import date
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.sales import Order, OrderStatus
from app.models.billing import Invoice, InvoiceStatus
from app.models.production import ProductionRun, ProductionRunItem
from app.models.master import RawMaterial, Product
from app.services.ledger_service import get_all_stock_summary
from app.services.billing_service import get_customer_outstanding_paise
from app.models.master import Customer

def get_owner_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    NON-NEGOTIABLE OWNER DASHBOARD:
    Dashboard with:
    - Today's orders
    - Stock levels
    - Variance alerts
    - Cost per packet
    - Outstanding dues
    """
    today = date.today()

    # 1. Today's Orders
    today_orders = db.query(Order).filter(func.date(Order.created_at) == today).all()
    today_orders_count = len(today_orders)

    today_orders_value_paise = sum(
        sum(item.total_paise for item in o.items) for o in today_orders
    )

    # 2. Live Stock Levels
    stock_snapshot = get_all_stock_summary(db)
    low_stock_materials = [rm for rm in stock_snapshot["raw_and_packaging"] if rm["is_low_stock"]]

    # 3. Variance Alerts (Runs with yield variance or material variance outside tolerance)
    flagged_runs = db.query(ProductionRun).filter(ProductionRun.is_yield_flagged == True).order_by(desc(ProductionRun.id)).limit(5).all()

    flagged_items = db.query(ProductionRunItem).filter(ProductionRunItem.is_flagged == True).order_by(desc(ProductionRunItem.id)).limit(10).all()

    variance_alerts = []
    for run in flagged_runs:
        variance_alerts.append({
            "type": "YIELD_ALERT",
            "run_no": run.run_no,
            "product": run.product.name,
            "message": f"Yield variance {run.yield_variance_pct:.2f}% outside tolerance (Actual {run.actual_good_output_packets} vs Planned {run.planned_output_packets})"
        })

    for item in flagged_items:
        sign = "+" if item.variance_pct > 0 else ""
        diff_val = item.actual_qty_base - item.standard_qty_base
        variance_alerts.append({
            "type": "MATERIAL_ALERT",
            "run_no": item.production_run.run_no,
            "product": item.production_run.product.name,
            "material": item.raw_material.name,
            "message": f"{item.raw_material.name} usage variance {sign}{item.variance_pct:.2f}% ({diff_val:.1f} {item.base_unit} diff, about Rs {abs(item.variance_cost_paise)/100:.2f})"
        })

    # 4. Cost Per Packet (Latest completed production runs)
    latest_runs = db.query(ProductionRun).order_by(desc(ProductionRun.id)).limit(5).all()
    cost_summary = []
    for r in latest_runs:
        cost_summary.append({
            "run_no": r.run_no,
            "product_name": r.product.name,
            "date": r.created_at.strftime("%d-%m-%Y"),
            "good_output_packets": r.actual_good_output_packets,
            "material_cost_rs": f"{r.total_material_cost_paise / 100:.2f}",
            "overhead_cost_rs": f"{r.total_overhead_cost_paise / 100:.2f}",
            "cost_per_packet_paise": r.cost_per_packet_paise,
            "cost_per_packet_rs": f"{r.cost_per_packet_paise / 100:.2f}"
        })

    # 5. Outstanding Dues
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    debtors = []
    total_outstanding_paise = 0

    for cust in customers:
        bal = get_customer_outstanding_paise(db, cust.id)
        if bal > 0:
            total_outstanding_paise += bal
            debtors.append({
                "customer_id": cust.id,
                "customer_name": cust.name,
                "state": cust.state,
                "phone": cust.phone,
                "outstanding_paise": bal,
                "outstanding_rs": f"{bal / 100:.2f}"
            })

    # Sort top debtors descending
    debtors.sort(key=lambda d: d["outstanding_paise"], reverse=True)

    return {
        "today_orders": {
            "count": today_orders_count,
            "total_value_paise": today_orders_value_paise,
            "total_value_rs": f"{today_orders_value_paise / 100:.2f}"
        },
        "inventory": {
            "finished_goods": stock_snapshot["finished_goods"],
            "low_stock_materials": low_stock_materials
        },
        "variance_alerts": variance_alerts,
        "cost_per_packet_history": cost_summary,
        "receivables": {
            "total_outstanding_paise": total_outstanding_paise,
            "total_outstanding_rs": f"{total_outstanding_paise / 100:.2f}",
            "top_debtors": debtors[:5]
        }
    }
