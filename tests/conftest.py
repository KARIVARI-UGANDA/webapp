"""
Shared fixtures for all pytest tests.
Each test gets a completely fresh in-memory SQLite database for full isolation.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models as _orm_models  # noqa: F401  registers all ORM classes with Base.metadata before create_all
from app.database import get_db
from app.main import app
from app.models.base import Base

# ── Stripe mock — prevents real API calls in all tests ──────────────────────
_fake_intent = MagicMock()
_fake_intent.id = "pi_test_fake"
_fake_intent.client_secret = "pi_test_fake_secret_ci"
_fake_intent.status = "succeeded"

patch(
    "app.services.stripe_service.stripe.PaymentIntent.create",
    return_value=_fake_intent,
).start()


@pytest.fixture()
def client():
    """Fresh in-memory SQLite database per test — fully isolated."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


# ── Reusable user helpers ────────────────────────────────────────────────────


def _register(client, email, password, name, role="customer", phone=None):
    phone = phone or f"+256700{abs(hash(email)) % 1_000_000:06d}"
    r = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": name,
            "phone_number": phone,
            "role": role,
        },
    )
    return r


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r


def _auth_headers(client, email, password):
    r = _login(client, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def customer(client):
    """Registered + logged-in customer. Returns (headers, user_data)."""
    email, pw = "customer@test.com", "password123"
    _register(client, email, pw, "Test Customer")
    headers = _auth_headers(client, email, pw)
    return headers, {"email": email, "password": pw, "full_name": "Test Customer"}


@pytest.fixture()
def owner(client):
    """Registered + logged-in owner."""
    email, pw = "owner@test.com", "password123"
    _register(client, email, pw, "Test Owner", role="owner", phone="+256701000001")
    headers = _auth_headers(client, email, pw)
    return headers, {"email": email, "password": pw, "full_name": "Test Owner"}


@pytest.fixture()
def admin(client):
    """Registered + logged-in admin."""
    email, pw = "admin@test.com", "password123"
    _register(client, email, pw, "Test Admin", role="admin", phone="+256702000001")
    headers = _auth_headers(client, email, pw)
    return headers, {"email": email, "password": pw, "full_name": "Test Admin"}


@pytest.fixture()
def verified_vehicle(client, owner, admin):
    """A vehicle created by the owner and approved by admin."""
    owner_headers, _ = owner
    admin_headers, _ = admin

    r = client.post(
        "/api/vehicles/",
        headers=owner_headers,
        json={
            "make": "Toyota",
            "model": "Land Cruiser",
            "year": 2020,
            "color": "White",
            "registration_plate": "UAA 001A",
            "vehicle_type": "safari",
            "transmission": "automatic",
            "fuel_type": "diesel",
            "passenger_capacity": 7,
            "has_ac": True,
            "is_4wd": True,
            "base_daily_rate_ugx": 850000,
            "service_area": "Kampala",
        },
    )
    assert r.status_code == 201, r.text
    vehicle_id = r.json()["id"]

    a = client.patch(
        f"/api/admin/verifications/{vehicle_id}/approve", headers=admin_headers
    )
    assert a.status_code == 200, a.text

    return vehicle_id
