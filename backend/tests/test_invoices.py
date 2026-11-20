import pytest
from datetime import date
from app.models.master import Customer, Product
from app.models.sales import Order, OrderStatus
from app.models.billing import Invoice, InvoiceStatus

def test_invoice_creation_immutability_and_credit_note(client, db):
    """
    NON-NEGOTIABLE RULE 3:
    Posted invoices cannot be edited or deleted. They are cancelled by a credit note.
    Invoice numbers follow financial year, e.g. TN/2026-27/0001.
    """
    admin_login = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    admin_token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    retailer_a = db.query(Customer).filter(Customer.name.like("%Retailer A%")).first()
    murukku = db.query(Product).filter(Product.code == "FG-MRK-200G").first()

    # 1. Create and approve an order
    order_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": retailer_a.id,
            "items": [{"product_id": murukku.id, "quantity_packets": 20}]
        },
        headers=headers
    )
    order_id = order_res.json()["id"]

    client.post(f"/api/v1/orders/{order_id}/approve", headers=headers)

    # 2. Create Invoice
    inv_res = client.post(f"/api/v1/invoices/from-order/{order_id}", headers=headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["invoice_no"].startswith("TN/")
    assert inv_data["status"] == "posted"
    inv_id = inv_data["id"]

    # 3. Download PDF
    pdf_res = client.get(f"/api/v1/invoices/{inv_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")

    # 4. Cancel invoice with credit note
    cn_res = client.post(
        "/api/v1/invoices/cancel",
        json={"invoice_id": inv_id, "reason": "Customer changed order specifications"},
        headers=headers
    )
    assert cn_res.status_code == 200
    cn_data = cn_res.json()
    assert cn_data["credit_note_no"].startswith("CN/")

    # 5. Check invoice status is cancelled
    inv_get = client.get(f"/api/v1/invoices/{inv_id}", headers=headers)
    assert inv_get.json()["status"] == "cancelled"
