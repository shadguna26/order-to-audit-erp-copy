import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seeds.seed import seed_database

TEST_DB_PATH = "test_snack_erp.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def otp_login(client: TestClient, mobile: str) -> dict:
    """Helper for tests to authenticate via mobile + OTP (DEMO_MODE)."""
    req_res = client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert req_res.status_code == 200, req_res.text
    demo_code = req_res.json().get("demo_code")
    assert demo_code, "DEMO_MODE must return demo_code in tests"
    ver_res = client.post(
        "/api/v1/auth/otp/verify",
        json={"mobile": mobile, "otp": demo_code, "device_label": "pytest-client"},
    )
    assert ver_res.status_code == 200, ver_res.text
    return ver_res.json()
