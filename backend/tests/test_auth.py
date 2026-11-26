from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings, settings
from app.models.audit import AuditLog
from app.models.auth import OTPRequest, RefreshToken, User, UserRole
from app.services.otp_service import generate_otp_code, hash_otp, normalize_mobile, verify_otp_hash
from tests.conftest import otp_login


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Sri Lakshmi Snacks"
    assert data["state_code"] == "33"


def test_mobile_normalisation():
    assert normalize_mobile("9876543210") == "+919876543210"
    assert normalize_mobile("09876543210") == "+919876543210"
    assert normalize_mobile("919876543210") == "+919876543210"
    assert normalize_mobile("+91 98765-43210") == "+919876543210"
    assert normalize_mobile("+919000000001") == "+919000000001"

    for invalid in ["", "12345", "5123456789", "+14155552671", "9876543210123", "abcdefghij"]:
        with pytest.raises(ValueError):
            normalize_mobile(invalid)


def test_otp_hash_and_constant_time_compare():
    mobile = "+919000000001"
    code = generate_otp_code()
    assert len(code) == 6 and code.isdigit()

    digest = hash_otp(mobile, code)
    assert digest != code
    assert len(digest) == 64  # SHA-256 hex digest

    assert verify_otp_hash(mobile, code, digest) is True
    assert verify_otp_hash(mobile, "000000" if code != "000000" else "111111", digest) is False
    assert verify_otp_hash("+919000000002", code, digest) is False


def test_otp_expiry(client: TestClient, db):
    mobile = "+919000000003"
    req_res = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert req_res.status_code == 200
    code = req_res.json()["demo_code"]

    otp_row = db.query(OTPRequest).filter(OTPRequest.mobile == mobile).order_by(OTPRequest.id.desc()).first()
    otp_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    ver_res = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": code})
    assert ver_res.status_code == 401
    assert ver_res.json()["detail"] == "Invalid or expired OTP"


def test_otp_max_attempts_lockout(client: TestClient, db):
    mobile = "+919000000003"
    req_res = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert req_res.status_code == 200
    real_code = req_res.json()["demo_code"]
    wrong_code = "000000" if real_code != "000000" else "999999"

    for attempt in range(1, 5):
        res = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": wrong_code})
        assert res.status_code == 401, f"Attempt {attempt} expected 401"

    # 5th wrong try triggers lockout
    res_5 = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": wrong_code})
    assert res_5.status_code == 429

    # Even the correct OTP is now rejected
    res_after = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": real_code})
    assert res_after.status_code == 401

    lockout_log = db.query(AuditLog).filter(AuditLog.table_name == "auth", AuditLog.action == "lockout").first()
    assert lockout_log is not None


def test_otp_single_use(client: TestClient):
    mobile = "+919000000003"
    req_res = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    code = req_res.json()["demo_code"]

    first_verify = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": code})
    assert first_verify.status_code == 200

    second_verify = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "otp": code})
    assert second_verify.status_code == 401
    assert second_verify.json()["detail"] == "Invalid or expired OTP"


def test_otp_resend_cooldown(client: TestClient):
    mobile = "+919000000003"
    first = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert second.status_code == 429


def test_otp_hourly_limit(client: TestClient, db):
    mobile = "+919000000003"
    for i in range(5):
        res = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
        assert res.status_code == 200, f"Send {i+1} failed: {res.text}"
        # Backdate created_at by 60s to bypass 30s cooldown while staying within 1 hour
        latest = db.query(OTPRequest).filter(OTPRequest.mobile == mobile).order_by(OTPRequest.id.desc()).first()
        latest.created_at = datetime.now(timezone.utc) - timedelta(seconds=60)
        db.commit()

    sixth = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert sixth.status_code == 429


def test_identical_response_for_unknown_numbers(client: TestClient):
    reg_req = client.post("/api/v1/auth/otp/request", json={"mobile": "+919000000003"})
    unk_req = client.post("/api/v1/auth/otp/request", json={"mobile": "+919876500000"})

    assert reg_req.status_code == unk_req.status_code == 200
    assert reg_req.json()["message"] == unk_req.json()["message"]

    reg_ver = client.post("/api/v1/auth/otp/verify", json={"mobile": "+919000000003", "otp": "000000"})
    unk_ver = client.post("/api/v1/auth/otp/verify", json={"mobile": "+919876500000", "otp": "000000"})
    assert reg_ver.status_code == unk_ver.status_code == 401
    assert reg_ver.json()["detail"] == unk_ver.json()["detail"] == "Invalid or expired OTP"

    # Even with the demo_code for an unknown number, verify fails with the exact same message
    unk_code = unk_req.json()["demo_code"]
    unk_ver_code = client.post("/api/v1/auth/otp/verify", json={"mobile": "+919876500000", "otp": unk_code})
    assert unk_ver_code.status_code == 401
    assert unk_ver_code.json()["detail"] == "Invalid or expired OTP"


def test_role_in_token_and_backend_enforcement(client: TestClient):
    # No self-signup
    assert client.post("/api/v1/auth/register", json={}).status_code == 404

    roles_mobiles = [
        ("+919000000001", UserRole.OWNER),
        ("+919000000002", UserRole.ADMIN),
        ("+919000000003", UserRole.SALESMAN),
        ("+919000000005", UserRole.PRODUCTION),
        ("+919000000006", UserRole.ACCOUNTANT),
    ]
    tokens = {}
    for mobile, expected_role in roles_mobiles:
        data = otp_login(client, mobile)
        tokens[expected_role] = data["access_token"]
        payload = jwt.decode(data["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == expected_role.value
        assert isinstance(payload["user_id"], int)
        assert data["expires_in"] == 900

    # Salesman cannot view user roster or create users
    assert client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {tokens[UserRole.SALESMAN]}"}).status_code == 403
    assert client.post(
        "/api/v1/auth/users",
        json={"mobile": "+919876543219", "full_name": "Unauthorized Add", "role": "salesman"},
        headers={"Authorization": f"Bearer {tokens[UserRole.SALESMAN]}"},
    ).status_code == 403

    # Accountant cannot create orders (read-only)
    assert client.post(
        "/api/v1/orders",
        json={"customer_id": 1, "items": [{"product_id": 1, "quantity_packets": 10}]},
        headers={"Authorization": f"Bearer {tokens[UserRole.ACCOUNTANT]}"},
    ).status_code == 403

    # Admin can add, re-role, and view users
    create_res = client.post(
        "/api/v1/auth/users",
        json={"mobile": "9876543219", "full_name": "K. Selvam", "role": "salesman"},
        headers={"Authorization": f"Bearer {tokens[UserRole.ADMIN]}"},
    )
    assert create_res.status_code == 201
    new_user = create_res.json()
    assert new_user["mobile"] == "+919876543219"

    rerole_res = client.patch(
        f"/api/v1/auth/users/{new_user['id']}",
        json={"role": "production"},
        headers={"Authorization": f"Bearer {tokens[UserRole.ADMIN]}"},
    )
    assert rerole_res.status_code == 200
    assert rerole_res.json()["role"] == "production"


def test_refresh_rotation_and_reuse_detection(client: TestClient, db):
    login_data = otp_login(client, "+919000000003")
    old_cookie = client.cookies.get("refresh_token")
    assert old_cookie is not None

    # First refresh succeeds and rotates cookie
    ref1 = client.post("/api/v1/auth/refresh")
    assert ref1.status_code == 200
    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie is not None
    assert new_cookie != old_cookie

    # Presenting the old (already rotated) refresh token triggers reuse detection and revokes all user tokens
    client.cookies.set("refresh_token", old_cookie)
    reuse_res = client.post("/api/v1/auth/refresh")
    assert reuse_res.status_code == 401

    # Even the new token is now revoked for that user
    user = db.query(User).filter(User.mobile == "+919000000003").first()
    active_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).count()
    assert active_tokens == 0

    client.cookies.set("refresh_token", new_cookie)
    after_reuse = client.post("/api/v1/auth/refresh")
    assert after_reuse.status_code == 401


def test_deactivated_user_cannot_refresh(client: TestClient, db):
    # Log in as salesman_b in one client session, capture refresh cookie
    sales_login = otp_login(client, "+919000000004")
    sales_cookie = client.cookies.get("refresh_token")
    sales_user_id = sales_login["user"]["id"]

    # Log in as admin and deactivate salesman_b
    admin_login = otp_login(client, "+919000000002")
    deact_res = client.patch(
        f"/api/v1/auth/users/{sales_user_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_login['access_token']}"},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # All refresh tokens for salesman_b must be revoked immediately
    active_count = db.query(RefreshToken).filter(RefreshToken.user_id == sales_user_id, RefreshToken.revoked_at.is_(None)).count()
    assert active_count == 0

    # Refresh with salesman_b's old cookie fails
    client.cookies.set("refresh_token", sales_cookie)
    ref_res = client.post("/api/v1/auth/refresh")
    assert ref_res.status_code in (401, 403)


def test_startup_refuses_production_demo_mode():
    with pytest.raises(ValueError, match="DEMO_MODE"):
        Settings(ENVIRONMENT="production", DEMO_MODE=True)

    # Production with DEMO_MODE=False is allowed
    prod_settings = Settings(ENVIRONMENT="production", DEMO_MODE=False)
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.DEMO_MODE is False


def test_audit_log_auth_events(client: TestClient, db):
    otp_login(client, "+919000000003")
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    actions = [
        row.action
        for row in db.query(AuditLog).filter(AuditLog.table_name == "auth").all()
    ]
    assert "otp_requested" in actions
    assert "login_success" in actions
    assert "logout" in actions

    sample = db.query(AuditLog).filter(AuditLog.table_name == "auth", AuditLog.action == "login_success").first()
    assert sample.new_values["mobile"].startswith("+91XXXXXX")
    assert "ip" in sample.new_values
    assert "user_agent" in sample.new_values
    assert "time" in sample.new_values
