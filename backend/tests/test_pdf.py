"""
Part A: PDF endpoint tests.
Tests that:
  1. An authorised admin/owner can download the invoice PDF.
  2. The response is application/pdf, starts with %PDF, uses attachment disposition.
  3. The filename contains no slashes.
  4. An unauthorised user (salesman) gets 403.
"""
import pytest
from tests.conftest import otp_login

# Seed data: admin = +919000000002, owner = +919000000001, salesman = +919000000003


def _create_invoice(client, admin_token: str) -> int:
    """Create order -> approve -> invoice. Returns invoice id."""
    # Place order (salesman role, but admin can also place)
    order_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": 1,
            "items": [{"product_id": 1, "quantity_packets": 10}],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert order_res.status_code == 201, order_res.text
    order_id = order_res.json()["id"]

    # Approve
    app_res = client.post(
        f"/api/v1/orders/{order_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert app_res.status_code == 200, app_res.text

    # Create invoice
    inv_res = client.post(
        f"/api/v1/invoices/from-order/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert inv_res.status_code == 201, inv_res.text
    return inv_res.json()["id"]


def test_invoice_pdf_download_admin(client, db):
    """Admin can download a PDF; response is valid and uses attachment disposition."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    res = client.get(
        f"/api/v1/invoices/{inv_id}/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "application/pdf"
    assert res.content[:4] == b"%PDF", "Response body must start with PDF magic bytes"

    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd, f"Expected 'attachment' in Content-Disposition, got: {cd!r}"
    assert "/" not in cd, f"Filename must not contain a slash, got: {cd!r}"
    assert "cache-control" in res.headers, "Cache-Control header must be present"
    assert "no-store" in res.headers["cache-control"].lower()


def test_invoice_pdf_download_owner(client, db):
    """Owner can also download invoice PDF."""
    owner_token = otp_login(client, "+919000000001")["access_token"]
    admin_token = otp_login(client, "+919000000002")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    res = client.get(
        f"/api/v1/invoices/{inv_id}/pdf",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 200
    assert res.content[:4] == b"%PDF"


def test_invoice_pdf_forbidden_salesman(client, db):
    """Salesman cannot access invoice PDF (reports/billing are admin-only)."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    sales_token = otp_login(client, "+919000000003")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    res = client.get(
        f"/api/v1/invoices/{inv_id}/pdf",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert res.status_code == 403, f"Expected 403 for salesman, got {res.status_code}"


def test_invoice_pdf_unauthenticated(client, db):
    """Unauthenticated requests must be rejected with 401 or 403."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    res = client.get(f"/api/v1/invoices/{inv_id}/pdf")
    assert res.status_code in (401, 403), f"Expected 401/403 without token, got {res.status_code}"


def test_invoice_pdf_filename_no_slash(client, db):
    """Filename in Content-Disposition must not contain slashes (invoice numbers like TN/2026-27/0001)."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    res = client.get(
        f"/api/v1/invoices/{inv_id}/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    cd = res.headers.get("content-disposition", "")
    # Extract only the filename part after 'filename='
    filename_part = cd.split("filename=")[-1].strip('"').strip("'")
    assert "/" not in filename_part, f"Filename must not contain /: {filename_part!r}"
    assert "\\" not in filename_part, f"Filename must not contain backslash: {filename_part!r}"
    assert filename_part.endswith(".pdf") and "-" in filename_part


def test_credit_note_pdf_and_report_export_headers(client, db):
    """Credit note PDF and report exports return attachment disposition and Cache-Control no-store."""
    admin_token = otp_login(client, "+919000000002")["access_token"]
    inv_id = _create_invoice(client, admin_token)

    cn_res = client.post(
        "/api/v1/invoices/cancel",
        json={"invoice_id": inv_id, "reason": "Damaged goods"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert cn_res.status_code == 200, cn_res.text
    cn_id = cn_res.json()["id"]

    pdf_res = client.get(
        f"/api/v1/invoices/credit-notes/{cn_id}/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pdf_res.status_code == 200, pdf_res.text
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"
    assert "attachment" in pdf_res.headers.get("content-disposition", "")
    assert "/" not in pdf_res.headers.get("content-disposition", "")
    assert "no-store" in pdf_res.headers.get("cache-control", "").lower()

    csv_res = client.get(
        "/api/v1/reports/sales-register?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert csv_res.status_code == 200
    assert "attachment" in csv_res.headers.get("content-disposition", "")
    assert "no-store" in csv_res.headers.get("cache-control", "").lower()
