from datetime import date
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.services.report_service import (
    get_sales_register,
    get_gst_summary_report,
    get_purchase_register,
    get_outstanding_ageing_report,
    get_production_runs_report
)
from app.services.export_service import generate_csv_string, generate_excel_bytes

router = APIRouter(prefix="/reports", tags=["Reports & Accountant Audit"])

# Non-negotiable: Role-based access: Accountant (read-only), Admin, Owner
ACCOUNTANT_ROLES = [UserRole.ACCOUNTANT, UserRole.ADMIN, UserRole.OWNER]

@router.get("/sales-register")
def sales_register(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json", description="'json', 'csv', 'excel'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTANT_ROLES))
):
    data = get_sales_register(db, start_date=start_date, end_date=end_date)
    headers = ["Invoice No", "Date", "Customer", "GSTIN", "State", "Subtotal (Rs)", "CGST (Rs)", "SGST (Rs)", "IGST (Rs)", "Total (Rs)"]

    if format == "csv":
        rows = [
            [d["invoice_no"], d["invoice_date"], d["customer_name"], d["customer_gstin"], d["state"], d["subtotal_rs"], d["cgst_rs"], d["sgst_rs"], d["igst_rs"], d["total_rs"]]
            for d in data
        ]
        csv_data = generate_csv_string(headers, rows)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Sales_Register.csv"})

    elif format == "excel":
        rows = [
            [d["invoice_no"], d["invoice_date"], d["customer_name"], d["customer_gstin"], d["state"], float(d["subtotal_rs"]), float(d["cgst_rs"]), float(d["sgst_rs"]), float(d["igst_rs"]), float(d["total_rs"])]
            for d in data
        ]
        excel_bytes = generate_excel_bytes("Sales Register", headers, rows)
        return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Sales_Register.xlsx"})

    return data

@router.get("/gst-summary")
def gst_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTANT_ROLES))
):
    """
    Returns GST Report in GSTR-1 / GSTR-3B shape.
    """
    return get_gst_summary_report(db, start_date=start_date, end_date=end_date)

@router.get("/purchase-register")
def purchase_register(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json", description="'json', 'csv', 'excel'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTANT_ROLES))
):
    data = get_purchase_register(db, start_date=start_date, end_date=end_date)
    headers = ["Purchase No", "Invoice Date", "Supplier", "Supplier Inv No", "Items", "Total (Rs)", "Status"]

    if format == "csv":
        rows = [
            [d["purchase_no"], d["invoice_date"], d["supplier_name"], d["supplier_invoice_no"], d["items_count"], d["total_amount_rs"], d["status"]]
            for d in data
        ]
        csv_data = generate_csv_string(headers, rows)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Purchase_Register.csv"})

    elif format == "excel":
        rows = [
            [d["purchase_no"], d["invoice_date"], d["supplier_name"], d["supplier_invoice_no"], d["items_count"], float(d["total_amount_rs"]), d["status"]]
            for d in data
        ]
        excel_bytes = generate_excel_bytes("Purchase Register", headers, rows)
        return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Purchase_Register.xlsx"})

    return data

@router.get("/ageing-report")
def ageing_report(
    format: str = Query("json", description="'json', 'csv', 'excel'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTANT_ROLES))
):
    """
    Outstanding with ageing: 0-30 days, 31-60 days, 61-90 days, 90+ days.
    """
    data = get_outstanding_ageing_report(db)
    headers = ["Customer", "State", "Phone", "Total (Rs)", "0-30 Days (Rs)", "31-60 Days (Rs)", "61-90 Days (Rs)", "90+ Days (Rs)"]

    if format == "csv":
        rows = [
            [d["customer_name"], d["state"], d["phone"], d["total_outstanding_rs"], d["bucket_0_30_rs"], d["bucket_31_60_rs"], d["bucket_61_90_rs"], d["bucket_90_plus_rs"]]
            for d in data
        ]
        csv_data = generate_csv_string(headers, rows)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Outstanding_Ageing.csv"})

    elif format == "excel":
        rows = [
            [d["customer_name"], d["state"], d["phone"], float(d["total_outstanding_rs"]), float(d["bucket_0_30_rs"]), float(d["bucket_31_60_rs"]), float(d["bucket_61_90_rs"]), float(d["bucket_90_plus_rs"])]
            for d in data
        ]
        excel_bytes = generate_excel_bytes("Ageing Report", headers, rows)
        return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Outstanding_Ageing.xlsx"})

    return data

@router.get("/production-report")
def production_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json", description="'json', 'csv', 'excel'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTANT_ROLES))
):
    data = get_production_runs_report(db, start_date=start_date, end_date=end_date)
    headers = ["Run No", "Date", "Product", "Planned (Pkts)", "Actual (Pkts)", "Damaged", "Cartons", "Yield Var %", "Material (Rs)", "Overheads (Rs)", "Cost/Pkt (Rs)"]

    if format == "csv":
        rows = [
            [d["run_no"], d["date"], d["product_name"], d["planned_output"], d["actual_good_output"], d["damaged_pouches"], d["cartons_used"], d["yield_variance_pct"], d["material_cost_rs"], d["overhead_cost_rs"], d["cost_per_packet_rs"]]
            for d in data
        ]
        csv_data = generate_csv_string(headers, rows)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Production_Report.csv"})

    elif format == "excel":
        rows = [
            [d["run_no"], d["date"], d["product_name"], d["planned_output"], d["actual_good_output"], d["damaged_pouches"], d["cartons_used"], d["yield_variance_pct"], float(d["material_cost_rs"]), float(d["overhead_cost_rs"]), float(d["cost_per_packet_rs"])]
            for d in data
        ]
        excel_bytes = generate_excel_bytes("Production Report", headers, rows)
        return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Production_Report.xlsx"})

    return data
