"""Tests for /api/admin/* endpoints."""

import pytest

VEHICLE_PAYLOAD = {
    "make": "Nissan",
    "model": "Patrol",
    "year": 2019,
    "color": "Silver",
    "registration_plate": "UAB 001A",
    "vehicle_type": "suv",
    "transmission": "automatic",
    "fuel_type": "petrol",
    "passenger_capacity": 5,
    "has_ac": True,
    "is_4wd": True,
    "base_daily_rate_ugx": 700000,
    "service_area": "Entebbe",
}


class TestVehicleVerification:
    def _pending_vehicle(self, client, owner_headers, plate="UAB 010A"):
        r = client.post(
            "/api/vehicles/",
            headers=owner_headers,
            json={**VEHICLE_PAYLOAD, "registration_plate": plate},
        )
        assert r.status_code == 201
        return r.json()["id"]

    def test_admin_can_list_pending_vehicles(self, client, admin, owner):
        admin_headers, _ = admin
        owner_headers, _ = owner
        self._pending_vehicle(client, owner_headers, "UAB 011A")
        r = client.get("/api/admin/verifications/pending", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_can_approve_vehicle(self, client, admin, owner):
        admin_headers, _ = admin
        owner_headers, _ = owner
        vid = self._pending_vehicle(client, owner_headers, "UAB 012A")
        r = client.patch(
            f"/api/admin/verifications/{vid}/approve", headers=admin_headers
        )
        assert r.status_code == 200
        assert r.json()["status"] == "verified"

    def test_admin_can_reject_vehicle(self, client, admin, owner):
        admin_headers, _ = admin
        owner_headers, _ = owner
        vid = self._pending_vehicle(client, owner_headers, "UAB 013A")
        r = client.patch(
            f"/api/admin/verifications/{vid}/reject",
            headers=admin_headers,
            json={"reason": "Poor vehicle condition"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_customer_cannot_access_verifications(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/verifications/pending", headers=headers)
        assert r.status_code == 403

    def test_owner_cannot_access_verifications(self, client, owner):
        headers, _ = owner
        r = client.get("/api/admin/verifications/pending", headers=headers)
        assert r.status_code == 403


class TestUserManagement:
    def test_admin_can_list_users(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_can_filter_users_by_role(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/users?role=customer", headers=headers)
        assert r.status_code == 200
        for u in r.json():
            assert u["role"] == "customer"

    def test_admin_can_suspend_user(self, client, admin, customer):
        admin_headers, _ = admin
        customer_headers, _ = customer
        me = client.get("/api/users/me", headers=customer_headers).json()
        r = client.patch(f"/api/admin/users/{me['id']}/suspend", headers=admin_headers)
        assert r.status_code == 200

    def test_customer_cannot_list_users(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 403


class TestBookingManagement:
    def test_admin_can_list_all_bookings(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/bookings", headers=headers)
        assert r.status_code == 200
        data = r.json()
        # Response is paginated: {"total": N, "page": 1, "page_size": 20, "bookings": [...]}
        assert "bookings" in data or isinstance(data, list)
        bookings = data["bookings"] if isinstance(data, dict) else data
        assert isinstance(bookings, list)

    def test_admin_can_filter_bookings_by_status(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/bookings?status=pending_payment", headers=headers)
        assert r.status_code == 200

    def test_customer_cannot_access_admin_bookings(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/bookings", headers=headers)
        assert r.status_code == 403


class TestAnalytics:
    def test_admin_can_get_stats(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/stats", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_users" in data or "users" in data

    def test_admin_can_get_analytics_overview(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/analytics/overview", headers=headers)
        assert r.status_code == 200

    def test_admin_can_get_booking_analytics(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/analytics/bookings?days=7", headers=headers)
        assert r.status_code == 200

    def test_admin_can_get_revenue_analytics(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/analytics/revenue?days=7", headers=headers)
        assert r.status_code == 200

    def test_customer_cannot_access_analytics(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/stats", headers=headers)
        assert r.status_code == 403
