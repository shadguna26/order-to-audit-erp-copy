import pytest
from datetime import date
from app.models.master import Customer, Product, Supplier
from app.models.sales import Order, OrderStatus
from app.models.billing import Invoice

def test_reports_and_dashboard_workflow(client, db):
    # 1. Logins
    acct_token = client.post("/api/v1/auth/login", data={"username": "accountant", "password": "acct123"}).json()["access_token"]
    owner_token = client.post("/api/v1/auth/login", data={"username": "owner", "password": "owner123"}).json()["access_token"]
    sales_token = client.post("/api/v1/auth/login", data={"username": "salesman_a", "password": "sales123"}).json()["access_token"]

    acct_hdr = {"Authorization": f"Bearer {acct_token}"}
    owner_hdr = {"Authorization": f"Bearer {owner_token}"}
    sales_hdr = {"Authorization": f"Bearer {sales_token}"}

    # Salesman should receive 403 Forbidden on reports
    sales_forbidden = client.get("/api/v1/reports/sales-register", headers=sales_hdr)
    assert sales_forbidden.status_code == 403

    # 2. Accountant can access Sales Register (empty or with posted invoices)
    sales_reg = client.get("/api/v1/reports/sales-register", headers=acct_hdr)
    assert sales_reg.status_code == 200

    # 3. Test CSV export of Sales Register
    sales_csv = client.get("/api/v1/reports/sales-register?format=csv", headers=acct_hdr)
    assert sales_csv.status_code == 200
    assert "Invoice No,Date,Customer" in sales_csv.text

    # 4. Test Excel export of Sales Register
    sales_excel = client.get("/api/v1/reports/sales-register?format=excel", headers=acct_hdr)
    assert sales_excel.status_code == 200
    assert sales_excel.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(sales_excel.content) > 100

    # 5. GST Summary Report (GSTR-1 / 3B shape)
    gst_res = client.get("/api/v1/reports/gst-summary", headers=acct_hdr)
    assert gst_res.status_code == 200
    gst_data = gst_res.json()
    assert "intra_state_supplies" in gst_data
    assert "inter_state_supplies" in gst_data
    assert "totals" in gst_data

    # 6. Purchase Register (JSON and CSV)
    pur_res = client.get("/api/v1/reports/purchase-register", headers=acct_hdr)
    assert pur_res.status_code == 200

    pur_csv = client.get("/api/v1/reports/purchase-register?format=csv", headers=acct_hdr)
    assert pur_csv.status_code == 200
    assert "Purchase No,Invoice Date,Supplier" in pur_csv.text

    # 7. Outstanding Ageing Report
    ageing_res = client.get("/api/v1/reports/ageing-report", headers=acct_hdr)
    assert ageing_res.status_code == 200

    ageing_excel = client.get("/api/v1/reports/ageing-report?format=excel", headers=acct_hdr)
    assert ageing_excel.status_code == 200

    # 8. Owner Dashboard
    dash_res = client.get("/api/v1/dashboard/owner", headers=owner_hdr)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "today_orders" in dash_data
    assert "inventory" in dash_data
    assert "variance_alerts" in dash_data
    assert "cost_per_packet_history" in dash_data
    assert "receivables" in dash_data
