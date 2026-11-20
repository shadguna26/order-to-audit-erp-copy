import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.planning_service import get_production_plan_from_pending_orders

def test_production_planning_from_approved_orders(client: TestClient, db: Session):
    # Obtain salesman and admin tokens
    salesman_res = client.post("/api/v1/auth/login", data={"username": "salesman_a", "password": "sales123"})
    salesman_token = salesman_res.json()["access_token"]

    admin_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    admin_token = admin_res.json()["access_token"]

    # Opening stock of Murukku 200g is 50 packets
    # Let's create an order for 250 packets (shortfall = 200 packets, exactly 1 batch of 200)
    order_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": 1,
            "items": [{"product_id": 1, "quantity_packets": 250, "unit_price_rs": 50.0}]
        },
        headers={"Authorization": f"Bearer {salesman_token}"}
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # Before approval, plan has no approved demand
    plan_before = get_production_plan_from_pending_orders(db)
    assert len(plan_before) == 0

    # Admin approves the order
    approve_res = client.post(
        f"/api/v1/orders/{order_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert approve_res.status_code == 200

    # Now check plan via API
    plan_res = client.get(
        "/api/v1/production/plan-from-orders",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert len(plan_data) == 1

    item = plan_data[0]
    assert item["product_id"] == 1
    assert item["approved_demand_packets"] == 250
    assert item["current_stock_packets"] == 50
    assert item["net_shortfall_packets"] == 200
    assert item["batches_to_produce"] == 1
    assert "To fulfil approved orders, make 1 batch" in item["recommendation"]

    # Check required materials
    assert len(item["required_materials"]) > 0
    flour_mat = next(m for m in item["required_materials"] if m["code"] == "RM-FLOUR")
    assert flour_mat["qty_needed_base"] == 40000.0  # 40 kg
