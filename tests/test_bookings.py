"""Tests for /api/bookings/* endpoints."""

from datetime import date, timedelta

TODAY = date.today()
PICKUP = (TODAY + timedelta(days=7)).isoformat()
RETURN = (TODAY + timedelta(days=14)).isoformat()

BOOKING_PAYLOAD = {
    "pickup_date": PICKUP,
    "return_date": RETURN,
    "pickup_location": "Entebbe Airport",
    "dropoff_location": "Bwindi",
    "passenger_count": 2,
    "special_requests": "Open roof preferred",
}


class TestCreateBooking:
    def test_customer_can_create_booking(self, client, customer, verified_vehicle):
        headers, _ = customer
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle},
        )
        assert r.status_code in (200, 201)
        data = r.json()
        assert "booking_id" in data or "id" in data
        assert "client_secret" in data or "booking_reference" in data

    def test_unauthenticated_cannot_book(self, client, verified_vehicle):
        r = client.post(
            "/api/bookings/", json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle}
        )
        assert r.status_code in (401, 403)

    def test_owner_cannot_book_own_vehicle(self, client, owner, verified_vehicle):
        headers, _ = owner
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle},
        )
        assert r.status_code in (403, 400)

    def test_booking_nonexistent_vehicle(self, client, customer):
        headers, _ = customer
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": "99999999"},
        )
        assert r.status_code == 404

    def test_return_before_pickup_rejected(self, client, customer, verified_vehicle):
        headers, _ = customer
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={
                **BOOKING_PAYLOAD,
                "vehicle_id": verified_vehicle,
                "pickup_date": RETURN,
                "return_date": PICKUP,
            },
        )
        assert r.status_code in (400, 422)

    def test_pickup_in_past_rejected(self, client, customer, verified_vehicle):
        headers, _ = customer
        past = (TODAY - timedelta(days=1)).isoformat()
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={
                **BOOKING_PAYLOAD,
                "vehicle_id": verified_vehicle,
                "pickup_date": past,
            },
        )
        assert r.status_code in (400, 422)


class TestListBookings:
    def test_customer_sees_own_bookings(self, client, customer, verified_vehicle):
        headers, _ = customer
        client.post(
            "/api/bookings/",
            headers=headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle},
        )
        r = client.get("/api/bookings/", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_customer_cannot_see_others_bookings(
        self, client, customer, verified_vehicle
    ):
        from tests.conftest import _auth_headers, _register

        _register(
            client, "cust2@test.com", "password123", "Cust Two", phone="+256705000001"
        )
        headers2 = _auth_headers(client, "cust2@test.com", "password123")
        r = client.get("/api/bookings/", headers=headers2)
        assert r.status_code == 200
        assert r.json() == []

    def test_unauthenticated_cannot_list(self, client):
        r = client.get("/api/bookings/")
        assert r.status_code in (401, 403)


class TestOwnerBookings:
    def test_owner_sees_bookings_for_their_vehicles(
        self, client, owner, customer, verified_vehicle
    ):
        customer_headers, _ = customer
        owner_headers, _ = owner
        client.post(
            "/api/bookings/",
            headers=customer_headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle},
        )
        r = client.get("/api/bookings/owner", headers=owner_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_customer_cannot_access_owner_bookings(self, client, customer):
        headers, _ = customer
        r = client.get("/api/bookings/owner", headers=headers)
        assert r.status_code == 403


class TestCancelBooking:
    def test_customer_can_cancel_pending_booking(
        self, client, customer, verified_vehicle
    ):
        headers, _ = customer
        create = client.post(
            "/api/bookings/",
            headers=headers,
            json={**BOOKING_PAYLOAD, "vehicle_id": verified_vehicle},
        )
        booking_id = create.json().get("booking_id") or create.json().get("id")
        r = client.patch(f"/api/bookings/{booking_id}/cancel", headers=headers)
        assert r.status_code == 200

    def test_cannot_cancel_nonexistent_booking(self, client, customer):
        headers, _ = customer
        r = client.patch("/api/bookings/99999999/cancel", headers=headers)
        assert r.status_code == 404
