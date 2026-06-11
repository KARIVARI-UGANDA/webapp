"""Tests for authentication edge-cases, token security, and role isolation."""

from tests.conftest import _login, _register


class TestTokenSecurity:
    def test_tampered_token_rejected(self, client, customer):
        headers, _ = customer
        token = headers["Authorization"].split(" ")[1]
        # Flip last few chars
        bad_token = token[:-4] + "XXXX"
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert r.status_code == 401

    def test_empty_bearer_rejected(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer "})
        assert r.status_code in (401, 403)

    def test_wrong_scheme_rejected(self, client, customer):
        headers, _ = customer
        token = headers["Authorization"].split(" ")[1]
        r = client.get("/api/auth/me", headers={"Authorization": f"Basic {token}"})
        assert r.status_code in (401, 403)

    def test_owner_token_cannot_access_admin_routes(self, client, owner):
        headers, _ = owner
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 403

    def test_customer_token_cannot_access_admin_routes(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/users", headers=headers)
        assert r.status_code == 403

    def test_customer_token_cannot_create_vehicle(self, client, customer):
        headers, _ = customer
        r = client.post(
            "/api/vehicles/",
            headers=headers,
            json={
                "make": "Ford",
                "model": "Ranger",
                "year": 2022,
                "color": "Blue",
                "registration_plate": "UAD 001A",
                "vehicle_type": "suv",
                "transmission": "manual",
                "fuel_type": "diesel",
                "passenger_capacity": 4,
                "base_daily_rate_ugx": 500000,
            },
        )
        assert r.status_code == 403

    def test_suspended_user_cannot_login(self, client, admin):
        """After admin suspends a user, they cannot authenticate."""
        admin_headers, _ = admin
        # Register a new user to suspend
        _register(
            client,
            "suspend@test.com",
            "password123",
            "Suspend Me",
            phone="+256706000001",
        )
        login_data = _login(client, "suspend@test.com", "password123").json()
        user_headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        me = client.get("/api/users/me", headers=user_headers).json()

        # Admin suspends
        client.patch(f"/api/admin/users/{me['id']}/suspend", headers=admin_headers)

        # Suspended user's existing token should now be rejected
        r = client.get("/api/users/me", headers=user_headers)
        assert r.status_code in (401, 403)


class TestRoleIsolation:
    def test_owner_cannot_book_own_vehicle(self, client, owner, verified_vehicle):
        from datetime import date, timedelta

        headers, _ = owner
        today = date.today()
        r = client.post(
            "/api/bookings/",
            headers=headers,
            json={
                "vehicle_id": verified_vehicle,
                "pickup_date": (today + timedelta(days=5)).isoformat(),
                "return_date": (today + timedelta(days=8)).isoformat(),
                "pickup_location": "Kampala",
                "dropoff_location": "Entebbe",
                "passenger_count": 1,
            },
        )
        # Owner booking their own vehicle is blocked at the app level
        assert r.status_code in (400, 403)

    def test_customer_cannot_approve_vehicles(self, client, customer, owner):
        customer_headers, _ = customer
        owner_headers, _ = owner
        create = client.post(
            "/api/vehicles/",
            headers=owner_headers,
            json={
                "make": "Honda",
                "model": "CR-V",
                "year": 2020,
                "color": "Grey",
                "registration_plate": "UAD 100A",
                "vehicle_type": "suv",
                "transmission": "automatic",
                "fuel_type": "petrol",
                "passenger_capacity": 5,
                "base_daily_rate_ugx": 450000,
            },
        )
        vid = create.json()["id"]
        r = client.patch(
            f"/api/admin/verifications/{vid}/approve", headers=customer_headers
        )
        assert r.status_code == 403

    def test_unauthenticated_cannot_reach_protected_routes(self, client):
        protected = [
            ("GET", "/api/users/me"),
            ("GET", "/api/bookings/"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/kyc/me"),
            ("GET", "/api/reviews/me"),
        ]
        for method, url in protected:
            r = client.request(method, url)
            assert r.status_code in (401, 403), (
                f"{method} {url} returned {r.status_code}"
            )
