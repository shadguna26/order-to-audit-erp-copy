from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.billing import Invoice, InvoiceStatus, Purchase, Payment
from app.models.sales import Order, OrderItem
from app.models.master import Customer, Product, Supplier
from app.models.production import ProductionRun, ProductionRunItem
from app.models.stock import StockLedger, StockItemType, StockLocationType
from app.services.ledger_service import get_all_stock_summary
from app.services.billing_service import get_customer_outstanding_paise

def get_sales_register(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    query = db.query(Invoice).filter(Invoice.status == InvoiceStatus.POSTED)
    if start_date:
        query = query.filter(func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Invoice.created_at) <= end_date)

    invoices = query.order_by(desc(Invoice.id)).all()
    results = []
    for inv in invoices:
        results.append({
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "invoice_date": inv.created_at.strftime("%Y-%m-%d"),
            "customer_name": inv.customer.name,
            "customer_gstin": inv.customer.gstin or "Unregistered",
            "state": inv.customer.state,
            "subtotal_paise": inv.subtotal_paise,
            "subtotal_rs": f"{inv.subtotal_paise / 100:.2f}",
            "cgst_paise": inv.cgst_paise,
            "cgst_rs": f"{inv.cgst_paise / 100:.2f}",
            "sgst_paise": inv.sgst_paise,
            "sgst_rs": f"{inv.sgst_paise / 100:.2f}",
            "igst_paise": inv.igst_paise,
            "igst_rs": f"{inv.igst_paise / 100:.2f}",
            "total_paise": inv.total_paise,
            "total_rs": f"{inv.total_paise / 100:.2f}"
        })
    return results

def get_gst_summary_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Returns GST Report in GSTR-1 / GSTR-3B shape:
    - Intra-State Supplies (Tamil Nadu - CGST + SGST)
    - Inter-State Supplies (IGST)
    - Aggregate Taxable Value, CGST, SGST, IGST, Total Tax
    """
    invoices = get_sales_register(db, start_date=start_date, end_date=end_date)

    intra_taxable = 0
    intra_cgst = 0
    intra_sgst = 0

    inter_taxable = 0
    inter_igst = 0

    for inv in invoices:
        if inv["igst_paise"] == 0:
            intra_taxable += inv["subtotal_paise"]
            intra_cgst += inv["cgst_paise"]
            intra_sgst += inv["sgst_paise"]
        else:
            inter_taxable += inv["subtotal_paise"]
            inter_igst += inv["igst_paise"]

    total_taxable = intra_taxable + inter_taxable
    total_tax = intra_cgst + intra_sgst + inter_igst

    return {
        "period": {
            "start_date": str(start_date or "All time"),
            "end_date": str(end_date or "All time")
        },
        "intra_state_supplies": {
            "state": "Tamil Nadu (33)",
            "taxable_value_paise": intra_taxable,
            "taxable_value_rs": f"{intra_taxable / 100:.2f}",
            "cgst_paise": intra_cgst,
            "cgst_rs": f"{intra_cgst / 100:.2f}",
            "sgst_paise": intra_sgst,
            "sgst_rs": f"{intra_sgst / 100:.2f}",
            "total_tax_paise": intra_cgst + intra_sgst,
            "total_tax_rs": f"{(intra_cgst + intra_sgst) / 100:.2f}"
        },
        "inter_state_supplies": {
            "taxable_value_paise": inter_taxable,
            "taxable_value_rs": f"{inter_taxable / 100:.2f}",
            "igst_paise": inter_igst,
            "igst_rs": f"{inter_igst / 100:.2f}",
            "total_tax_paise": inter_igst,
            "total_tax_rs": f"{inter_igst / 100:.2f}"
        },
        "totals": {
            "total_taxable_paise": total_taxable,
            "total_taxable_rs": f"{total_taxable / 100:.2f}",
            "total_cgst_paise": intra_cgst,
            "total_cgst_rs": f"{intra_cgst / 100:.2f}",
            "total_sgst_paise": intra_sgst,
            "total_sgst_rs": f"{intra_sgst / 100:.2f}",
            "total_igst_paise": inter_igst,
            "total_igst_rs": f"{inter_igst / 100:.2f}",
            "total_tax_paise": total_tax,
            "total_tax_rs": f"{total_tax / 100:.2f}"
        }
    }

def get_purchase_register(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    query = db.query(Purchase)
    if start_date:
        query = query.filter(Purchase.invoice_date >= start_date)
    if end_date:
        query = query.filter(Purchase.invoice_date <= end_date)

    purchases = query.order_by(desc(Purchase.id)).all()
    results = []
    for p in purchases:
        results.append({
            "id": p.id,
            "purchase_no": p.purchase_no,
            "invoice_date": p.invoice_date.strftime("%Y-%m-%d"),
            "supplier_name": p.supplier.name,
            "supplier_invoice_no": p.supplier_invoice_no or "-",
            "items_count": len(p.items),
            "total_amount_paise": p.total_amount_paise,
            "total_amount_rs": f"{p.total_amount_paise / 100:.2f}",
            "status": p.status.value
        })
    return results

def get_outstanding_ageing_report(db: Session) -> List[Dict[str, Any]]:
    """
    Outstanding with ageing buckets:
    0-30 days, 31-60 days, 61-90 days, 90+ days.
    """
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    today = date.today()
    report = []

    for cust in customers:
        outstanding = get_customer_outstanding_paise(db, cust.id)
        if outstanding <= 0:
            continue

        # Fetch posted unpaid invoices for this customer
        invoices = db.query(Invoice).filter(
            Invoice.customer_id == cust.id,
            Invoice.status == InvoiceStatus.POSTED
        ).order_by(desc(Invoice.created_at)).all()

        bucket_0_30 = 0
        bucket_31_60 = 0
        bucket_61_90 = 0
        bucket_90_plus = 0

        remaining_to_allocate = outstanding

        for inv in invoices:
            if remaining_to_allocate <= 0:
                break
            age_days = (today - inv.created_at.date()).days
            amount = min(inv.total_paise, remaining_to_allocate)
            remaining_to_allocate -= amount

            if age_days <= 30:
                bucket_0_30 += amount
            elif age_days <= 60:
                bucket_31_60 += amount
            elif age_days <= 90:
                bucket_61_90 += amount
            else:
                bucket_90_plus += amount

        report.append({
            "customer_id": cust.id,
            "customer_name": cust.name,
            "state": cust.state,
            "phone": cust.phone,
            "total_outstanding_paise": outstanding,
            "total_outstanding_rs": f"{outstanding / 100:.2f}",
            "bucket_0_30_paise": bucket_0_30,
            "bucket_0_30_rs": f"{bucket_0_30 / 100:.2f}",
            "bucket_31_60_paise": bucket_31_60,
            "bucket_31_60_rs": f"{bucket_31_60 / 100:.2f}",
            "bucket_61_90_paise": bucket_61_90,
            "bucket_61_90_rs": f"{bucket_61_90 / 100:.2f}",
            "bucket_90_plus_paise": bucket_90_plus,
            "bucket_90_plus_rs": f"{bucket_90_plus / 100:.2f}",
        })
    return report

def get_production_runs_report(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    query = db.query(ProductionRun)
    if start_date:
        query = query.filter(func.date(ProductionRun.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(ProductionRun.created_at) <= end_date)

    runs = query.order_by(desc(ProductionRun.id)).all()
    results = []
    for r in runs:
        results.append({
            "id": r.id,
            "run_no": r.run_no,
            "date": r.created_at.strftime("%Y-%m-%d"),
            "product_name": r.product.name,
            "planned_output": r.planned_output_packets,
            "actual_good_output": r.actual_good_output_packets,
            "damaged_pouches": r.actual_damaged_pouches,
            "cartons_used": r.actual_cartons_used,
            "yield_variance_pct": f"{r.yield_variance_pct:.2f}%",
            "is_yield_flagged": r.is_yield_flagged,
            "material_cost_rs": f"{r.total_material_cost_paise / 100:.2f}",
            "overhead_cost_rs": f"{r.total_overhead_cost_paise / 100:.2f}",
            "cost_per_packet_rs": f"{r.cost_per_packet_paise / 100:.2f}"
        })
    return results
