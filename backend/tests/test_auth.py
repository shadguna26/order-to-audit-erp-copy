import pytest
from fastapi.testclient import TestClient
from app.models.auth import UserRole
from app.models.stock import StockLedger, StockItemType, StockDirection
from app.models.master import RawMaterial, Product

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Sri Lakshmi Snacks"
    assert data["state_code"] == "33"

def test_user_logins_all_five_roles(client: TestClient):
    """
    NON-NEGOTIABLE RULE 5:
    Role-based access: salesman, admin, production, accountant (read-only), owner.
    Verify logins and token issuance for all 5 roles.
    """
    credentials = [
        ("owner", "owner123", UserRole.OWNER),
        ("admin", "admin123", UserRole.ADMIN),
        ("salesman_a", "sales123", UserRole.SALESMAN),
        ("salesman_b", "sales123", UserRole.SALESMAN),
        ("production", "prod123", UserRole.PRODUCTION),
        ("accountant", "acct123", UserRole.ACCOUNTANT),
    ]

    for username, password, expected_role in credentials:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        assert response.status_code == 200, f"Failed for {username}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == expected_role.value
        assert data["username"] == username

def test_invalid_login(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_rbac_user_roster_access(client: TestClient):
    """
    Verify RBAC enforcement:
    Admin/Owner can access /api/v1/auth/users.
    Salesman/Production/Accountant get 403 Forbidden.
    """
    # 1. Salesman login
    sales_login = client.post("/api/v1/auth/login", data={"username": "salesman_a", "password": "sales123"})
    sales_token = sales_login.json()["access_token"]

    sales_res = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {sales_token}"}
    )
    assert sales_res.status_code == 403
    assert "Access denied" in sales_res.json()["detail"]

    # 2. Accountant login (read-only accountant should not see user roster)
    acct_login = client.post("/api/v1/auth/login", data={"username": "accountant", "password": "acct123"})
    acct_token = acct_login.json()["access_token"]

    acct_res = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {acct_token}"}
    )
    assert acct_res.status_code == 403

    # 3. Admin login -> 200 OK
    admin_login = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    admin_token = admin_login.json()["access_token"]

    admin_res = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == 200
    users = admin_res.json()
    assert len(users) >= 6

def test_seed_opening_stock_ledger(db):
    """
    NON-NEGOTIABLE RULE 1:
    A single append-only stock_ledger table is the source of truth.
    Verify opening stock entries exist in stock_ledger.
    """
    entries = db.query(StockLedger).all()
    assert len(entries) >= 6

    # Verify flour opening stock = 100,000 g (100 kg)
    flour = db.query(RawMaterial).filter(RawMaterial.code == "RM-FLOUR").first()
    flour_entry = db.query(StockLedger).filter(
        StockLedger.item_type == StockItemType.RAW_MATERIAL,
        StockLedger.item_id == flour.id,
        StockLedger.direction == StockDirection.IN
    ).first()
    assert flour_entry is not None
    assert flour_entry.qty_base == 100000.0

    # Verify finished Murukku 200g opening stock = 50 packets
    murukku = db.query(Product).filter(Product.code == "FG-MRK-200G").first()
    murukku_entry = db.query(StockLedger).filter(
        StockLedger.item_type == StockItemType.FINISHED_GOODS,
        StockLedger.item_id == murukku.id,
        StockLedger.direction == StockDirection.IN
    ).first()
    assert murukku_entry is not None
    assert murukku_entry.qty_base == 50.0
