"""Tests for /api/reviews/* endpoints."""

import pytest


class TestCreateReview:
    def _make_confirmed_booking(
        self, client, customer_headers, owner_headers, admin_headers
    ):
        """Helper: vehicle → approve → book → manually confirm booking status."""
        from datetime import date, timedelta

        from tests.conftest import _auth_headers, _register

        # Create and approve vehicle
        r = client.post(
            "/api/vehicles/",
            headers=owner_headers,
            json={
                "make": "Toyota",
                "model": "Prado",
                "year": 2021,
                "color": "Black",
                "registration_plate": "UAC 001A",
                "vehicle_type": "safari",
                "transmission": "automatic",
                "fuel_type": "diesel",
                "passenger_capacity": 5,
                "has_ac": True,
                "is_4wd": True,
                "base_daily_rate_ugx": 600000,
                "service_area": "Kampala",
            },
        )
        vid = r.json()["id"]
        client.patch(f"/api/admin/verifications/{vid}/approve", headers=admin_headers)

        # Book it
        today = date.today()
        booking = client.post(
            "/api/bookings/",
            headers=customer_headers,
            json={
                "vehicle_id": vid,
                "pickup_date": (today + timedelta(days=3)).isoformat(),
                "return_date": (today + timedelta(days=5)).isoformat(),
                "pickup_location": "Kampala",
                "dropoff_location": "Jinja",
                "passenger_count": 2,
            },
        )
        return booking.json().get("booking_id") or booking.json().get("id"), vid

    def test_cannot_review_pending_payment_booking(
        self, client, customer, owner, admin
    ):
        customer_headers, _ = customer
        owner_headers, _ = owner
        admin_headers, _ = admin
        booking_id, vid = self._make_confirmed_booking(
            client, customer_headers, owner_headers, admin_headers
        )
        # Booking is still pending_payment — review should fail
        owner_me = client.get("/api/users/me", headers=owner_headers).json()
        r = client.post(
            "/api/reviews/",
            headers=customer_headers,
            json={
                "booking_id": booking_id,
                "reviewee_id": owner_me["id"],
                "review_target": "trip",
                "overall_rating": 5,
                "review_text": "Great trip!",
            },
        )
        assert r.status_code in (400, 403, 422)

    def test_unauthenticated_cannot_review(self, client):
        r = client.post(
            "/api/reviews/",
            json={
                "booking_id": "some-id",
                "reviewee_id": "some-id",
                "review_target": "trip",
                "overall_rating": 5,
            },
        )
        assert r.status_code in (401, 403)

    def test_invalid_rating_rejected(self, client, customer):
        headers, _ = customer
        r = client.post(
            "/api/reviews/",
            headers=headers,
            json={
                "booking_id": "x",
                "reviewee_id": "y",
                "review_target": "trip",
                "overall_rating": 6,
            },
        )
        assert r.status_code == 422


class TestListReviews:
    def test_public_reviews_accessible_unauthenticated(self, client):
        r = client.get("/api/reviews/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_my_reviews_requires_auth(self, client):
        r = client.get("/api/reviews/me")
        assert r.status_code in (401, 403)

    def test_customer_can_get_own_reviews(self, client, customer):
        headers, _ = customer
        r = client.get("/api/reviews/me", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_reviews_by_booking_id(self, client, customer):
        headers, _ = customer
        r = client.get("/api/reviews/booking/nonexistent-id", headers=headers)
        assert r.status_code in (200, 404)
