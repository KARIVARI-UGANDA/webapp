"""Tests for /api/vehicles/* endpoints."""
import pytest

VEHICLE_PAYLOAD = {
    "make": "Toyota",
    "model": "Land Cruiser",
    "year": 2020,
    "color": "White",
    "registration_plate": "UAA 100A",
    "vehicle_type": "safari",
    "transmission": "automatic",
    "fuel_type": "diesel",
    "passenger_capacity": 7,
    "has_ac": True,
    "is_4wd": True,
    "base_daily_rate_ugx": 850000,
    "service_area": "Kampala",
}


class TestCreateVehicle:
    def test_owner_can_create_vehicle(self, client, owner):
        headers, _ = owner
        r = client.post("/api/vehicles/", headers=headers, json=VEHICLE_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert data["make"] == "Toyota"
        assert data["status"] == "pending"

    def test_customer_cannot_create_vehicle(self, client, customer):
        headers, _ = customer
        r = client.post("/api/vehicles/", headers=headers, json=VEHICLE_PAYLOAD)
        assert r.status_code == 403

    def test_unauthenticated_cannot_create(self, client):
        r = client.post("/api/vehicles/", json=VEHICLE_PAYLOAD)
        assert r.status_code in (401, 403)

    def test_duplicate_plate_rejected(self, client, owner):
        headers, _ = owner
        client.post("/api/vehicles/", headers=headers, json=VEHICLE_PAYLOAD)
        r = client.post("/api/vehicles/", headers=headers, json=VEHICLE_PAYLOAD)
        assert r.status_code in (400, 409)

    def test_invalid_year_rejected(self, client, owner):
        headers, _ = owner
        bad = {**VEHICLE_PAYLOAD, "year": 1850, "registration_plate": "UAA 200A"}
        r = client.post("/api/vehicles/", headers=headers, json=bad)
        assert r.status_code == 422

    def test_zero_rate_rejected(self, client, owner):
        headers, _ = owner
        bad = {**VEHICLE_PAYLOAD, "base_daily_rate_ugx": 0, "registration_plate": "UAA 201A"}
        r = client.post("/api/vehicles/", headers=headers, json=bad)
        assert r.status_code == 422

    def test_negative_capacity_rejected(self, client, owner):
        headers, _ = owner
        bad = {**VEHICLE_PAYLOAD, "passenger_capacity": -1, "registration_plate": "UAA 202A"}
        r = client.post("/api/vehicles/", headers=headers, json=bad)
        assert r.status_code == 422


class TestListVehicles:
    def test_list_returns_only_verified(self, client, verified_vehicle):
        r = client.get("/api/vehicles/")
        assert r.status_code == 200
        vehicles = r.json()
        assert all(v["status"] == "verified" for v in vehicles)

    def test_list_unauthenticated_allowed(self, client):
        r = client.get("/api/vehicles/")
        assert r.status_code == 200

    def test_filter_by_vehicle_type(self, client, verified_vehicle):
        r = client.get("/api/vehicles/?vehicle_type=safari")
        assert r.status_code == 200
        for v in r.json():
            assert v["vehicle_type"] == "safari"

    def test_filter_by_min_seats(self, client, verified_vehicle):
        r = client.get("/api/vehicles/?min_seats=5")
        assert r.status_code == 200
        for v in r.json():
            assert v["passenger_capacity"] >= 5

    def test_filter_by_max_price(self, client, verified_vehicle):
        r = client.get("/api/vehicles/?max_price_ugx=1000000")
        assert r.status_code == 200
        for v in r.json():
            assert v["base_daily_rate_ugx"] <= 1000000

    def test_pagination(self, client, verified_vehicle):
        r = client.get("/api/vehicles/?page=1&page_size=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2


class TestGetVehicle:
    def test_get_verified_vehicle(self, client, verified_vehicle):
        r = client.get(f"/api/vehicles/{verified_vehicle}")
        assert r.status_code == 200
        assert r.json()["id"] == verified_vehicle

    def test_get_nonexistent_vehicle(self, client):
        r = client.get("/api/vehicles/99999999")
        assert r.status_code == 404


class TestUpdateVehicle:
    def test_owner_can_update_pending_vehicle(self, client, owner):
        headers, _ = owner
        create = client.post("/api/vehicles/", headers=headers, json={
            **VEHICLE_PAYLOAD, "registration_plate": "UAA 300A"
        })
        vid = create.json()["id"]
        r = client.patch(f"/api/vehicles/{vid}", headers=headers, json={"color": "Black"})
        assert r.status_code == 200
        assert r.json()["color"] == "Black"

    def test_owner_cannot_update_verified_vehicle(self, client, owner, verified_vehicle):
        headers, _ = owner
        r = client.patch(f"/api/vehicles/{verified_vehicle}", headers=headers, json={"color": "Red"})
        assert r.status_code in (403, 400)

    def test_other_owner_cannot_update(self, client, verified_vehicle):
        from tests.conftest import _register, _auth_headers
        _register(client, "owner3@test.com", "password123", "Other Owner",
                  role="owner", phone="+256704000001")
        headers = _auth_headers(client, "owner3@test.com", "password123")
        r = client.patch(f"/api/vehicles/{verified_vehicle}", headers=headers, json={"color": "Blue"})
        assert r.status_code in (403, 404)


class TestOwnerVehicles:
    def test_owner_can_list_own_vehicles(self, client, owner):
        headers, _ = owner
        client.post("/api/vehicles/", headers=headers, json={
            **VEHICLE_PAYLOAD, "registration_plate": "UAA 400A"
        })
        r = client.get("/api/vehicles/mine", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_customer_cannot_list_mine(self, client, customer):
        headers, _ = customer
        r = client.get("/api/vehicles/mine", headers=headers)
        assert r.status_code == 403


class TestDeleteVehicle:
    def test_owner_can_delete_pending_vehicle(self, client, owner):
        headers, _ = owner
        create = client.post("/api/vehicles/", headers=headers, json={
            **VEHICLE_PAYLOAD, "registration_plate": "UAA 500A"
        })
        vid = create.json()["id"]
        r = client.delete(f"/api/vehicles/{vid}", headers=headers)
        assert r.status_code in (200, 204)

    def test_owner_cannot_delete_verified_vehicle(self, client, owner, verified_vehicle):
        headers, _ = owner
        r = client.delete(f"/api/vehicles/{verified_vehicle}", headers=headers)
        assert r.status_code in (403, 400)
