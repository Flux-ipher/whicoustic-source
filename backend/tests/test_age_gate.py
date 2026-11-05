"""
Automated tests for Whicoustic Compliance & Signup Age Gate (Milestone 2).
Validates that:
1. Pydantic schema rejects registration with age < 17 and accepts age >= 17.
2. API endpoint POST /api/v1/auth/register returns 422 for age < 17 with compliance error message.
3. API endpoint POST /api/v1/auth/register succeeds (200) for age >= 17 and persists dob in database.
4. Exact boundary age testing (16 years 364 days blocked, 17 years 0 days allowed).
"""

import sys
import os
from datetime import date, timedelta
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse
from app.api.v1.auth import router as auth_router

COMPLIANCE_ERROR_MSG = (
    "Users must be at least 17 years old to register on Whicoustic in compliance with digital biometric licensing regulations."
)


# ---------------------------------------------------------------------------
# Test Fixtures & In-Memory DB
# ---------------------------------------------------------------------------
def _create_test_app():
    """Build a lightweight FastAPI app including auth router for isolated route testing."""
    test_app = FastAPI(title="Whicoustic Auth Test")
    test_app.include_router(auth_router, prefix="/api/v1")

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _get_test_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    test_app.dependency_overrides[get_db] = _get_test_db
    return test_app, TestingSession


# ---------------------------------------------------------------------------
# 1. Pydantic Schema Validation Tests
# ---------------------------------------------------------------------------
def test_user_create_rejects_underage():
    """Test that UserCreate schema raises ValueError for age < 17."""
    today = date.today()
    # 15 years old
    dob_15 = today - timedelta(days=int(15 * 365.25))

    caught = False
    try:
        UserCreate(
            username="underage_user",
            email="underage@whicoustic.com",
            password="SecurePassword123!",
            dob=dob_15
        )
    except ValidationError as e:
        caught = True
        assert COMPLIANCE_ERROR_MSG in str(e), f"Expected compliance error message, got: {e}"

    assert caught, "Expected ValidationError when age < 17, but none was raised"


def test_user_create_rejects_one_day_before_17th_birthday():
    """Test boundary: exactly 1 day before turning 17 must be blocked."""
    today = date.today()
    # 17 years minus 1 day (16 years and 364 days)
    dob_almost_17 = date(today.year - 17, today.month, today.day) + timedelta(days=1)

    caught = False
    try:
        UserCreate(
            username="almost_17",
            email="almost17@whicoustic.com",
            password="SecurePassword123!",
            dob=dob_almost_17
        )
    except ValidationError as e:
        caught = True
        assert COMPLIANCE_ERROR_MSG in str(e), f"Expected compliance error message, got: {e}"

    assert caught, "Expected ValidationError when age is 16y 364d, but none was raised"


def test_user_create_accepts_age_17_and_above():
    """Test that UserCreate schema accepts age >= 17."""
    today = date.today()
    # Exactly 17 years old
    dob_17 = date(today.year - 17, today.month, today.day)
    # 25 years old
    dob_25 = date(today.year - 25, today.month, today.day)

    user_17 = UserCreate(
        username="user_17",
        email="user17@whicoustic.com",
        password="SecurePassword123!",
        dob=dob_17
    )
    assert user_17.dob == dob_17

    user_25 = UserCreate(
        username="user_25",
        email="user25@whicoustic.com",
        password="SecurePassword123!",
        dob=dob_25
    )
    assert user_25.dob == dob_25


def test_user_create_requires_dob():
    """Test that UserCreate rejects missing or None dob."""
    caught = False
    try:
        UserCreate(
            username="no_dob",
            email="nodob@whicoustic.com",
            password="SecurePassword123!"
        )
    except ValidationError:
        caught = True

    assert caught, "Expected ValidationError when dob is omitted, but none was raised"


# ---------------------------------------------------------------------------
# 2. HTTP Route Integration Tests (POST /api/v1/auth/register)
# ---------------------------------------------------------------------------
def test_register_endpoint_blocks_underage():
    """Test that POST /api/v1/auth/register blocks age < 17 with HTTP 422 and compliance message."""
    app, SessionLocal = _create_test_app()
    client = TestClient(app)

    today = date.today()
    dob_15 = (today - timedelta(days=int(15 * 365.25))).isoformat()

    payload = {
        "username": "underage_creator",
        "email": "underage_creator@test.com",
        "password": "Password123!",
        "full_name": "Young Creator",
        "dob": dob_15
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    assert COMPLIANCE_ERROR_MSG in response.text, f"Compliance message missing in response: {response.text}"

    # Verify user record was NOT created in the database
    with SessionLocal() as db:
        user_in_db = db.query(User).filter(User.username == "underage_creator").first()
        assert user_in_db is None, "Underage user must not be persisted in database"


def test_register_endpoint_succeeds_and_persists_adult():
    """Test that POST /api/v1/auth/register succeeds with 200 for age >= 17 and persists dob."""
    app, SessionLocal = _create_test_app()
    client = TestClient(app)

    adult_dob_str = "1998-04-12"
    payload = {
        "username": "elena_rostova",
        "email": "elena.rostova@whicoustic.com",
        "password": "VaultPassword123!",
        "full_name": "Elena Rostova",
        "dob": adult_dob_str
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["username"] == "elena_rostova"
    assert data["email"] == "elena.rostova@whicoustic.com"
    assert data["dob"] == adult_dob_str
    assert "id" in data

    # Verify user record is genuinely persisted in database with correct dob
    with SessionLocal() as db:
        user_in_db = db.query(User).filter(User.username == "elena_rostova").first()
        assert user_in_db is not None, "Adult user must be persisted in database"
        assert user_in_db.dob == date(1998, 4, 12), f"Expected date(1998, 4, 12), got {user_in_db.dob}"
        assert user_in_db.full_name == "Elena Rostova"


def test_register_endpoint_exact_17th_birthday():
    """Test boundary: exactly 17 years old today must be accepted and persisted."""
    app, SessionLocal = _create_test_app()
    client = TestClient(app)

    today = date.today()
    dob_exact_17 = date(today.year - 17, today.month, today.day).isoformat()

    payload = {
        "username": "birthday_17",
        "email": "birthday17@test.com",
        "password": "Password123!",
        "full_name": "Seventeen Today",
        "dob": dob_exact_17
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200, f"Expected 200 on exact 17th birthday, got {response.status_code}: {response.text}"
    assert response.json()["dob"] == dob_exact_17

    with SessionLocal() as db:
        user_in_db = db.query(User).filter(User.username == "birthday_17").first()
        assert user_in_db is not None
        assert user_in_db.dob == date(today.year - 17, today.month, today.day)


if __name__ == "__main__":
    print("=====================================================================")
    print("RUNNING WHICOUSTIC COMPLIANCE & AGE GATE TEST SUITE (MILESTONE 2)")
    print("=====================================================================")
    test_user_create_rejects_underage()
    print("PASS: test_user_create_rejects_underage")
    test_user_create_rejects_one_day_before_17th_birthday()
    print("PASS: test_user_create_rejects_one_day_before_17th_birthday")
    test_user_create_accepts_age_17_and_above()
    print("PASS: test_user_create_accepts_age_17_and_above")
    test_user_create_requires_dob()
    print("PASS: test_user_create_requires_dob")
    test_register_endpoint_blocks_underage()
    print("PASS: test_register_endpoint_blocks_underage")
    test_register_endpoint_succeeds_and_persists_adult()
    print("PASS: test_register_endpoint_succeeds_and_persists_adult")
    test_register_endpoint_exact_17th_birthday()
    print("PASS: test_register_endpoint_exact_17th_birthday")
    print("=====================================================================")
    print("ALL 7 VERIFICATION CHECKS PASSED: Server & schema age gates verified!")
    print("=====================================================================")
