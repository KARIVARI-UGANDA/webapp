"""Tests for /api/users/* endpoints."""
from tests.conftest import _register, _auth_headers


class TestGetProfile:
    def test_get_own_profile(self, client, customer):
        headers, info = customer
        r = client.get("/api/users/me", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == info["email"]
        assert data["full_name"] == info["full_name"]

    def test_profile_requires_auth(self, client):
        r = client.get("/api/users/me")
        assert r.status_code in (401, 403)


class TestUpdateProfile:
    def test_update_full_name(self, client, customer):
        headers, _ = customer
        r = client.patch("/api/users/me", headers=headers, json={"full_name": "Updated Name"})
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"

    def test_update_preferred_language(self, client, customer):
        headers, _ = customer
        r = client.patch("/api/users/me", headers=headers, json={"preferred_language": "de"})
        assert r.status_code == 200
        assert r.json()["preferred_language"] == "de"

    def test_update_bio(self, client, customer):
        headers, _ = customer
        r = client.patch("/api/users/me", headers=headers, json={"bio": "Safari enthusiast."})
        assert r.status_code == 200
        assert r.json()["bio"] == "Safari enthusiast."

    def test_partial_update_preserves_other_fields(self, client, customer):
        headers, info = customer
        client.patch("/api/users/me", headers=headers, json={"bio": "Test bio"})
        r = client.get("/api/users/me", headers=headers)
        assert r.json()["email"] == info["email"]

    def test_update_requires_auth(self, client):
        r = client.patch("/api/users/me", json={"full_name": "No Auth"})
        assert r.status_code in (401, 403)


class TestChangePassword:
    def test_change_password_success(self, client):
        _register(client, "changepw@test.com", "OldPass123", "PW User")
        headers = _auth_headers(client, "changepw@test.com", "OldPass123")
        r = client.post("/api/users/me/change-password", headers=headers, json={
            "current_password": "OldPass123",
            "new_password": "NewPass456",
        })
        assert r.status_code == 200
        # Old password no longer works
        old = client.post("/api/auth/login", json={"email": "changepw@test.com", "password": "OldPass123"})
        assert old.status_code == 401
        # New password works
        new = client.post("/api/auth/login", json={"email": "changepw@test.com", "password": "NewPass456"})
        assert new.status_code == 200

    def test_wrong_current_password_rejected(self, client, customer):
        headers, _ = customer
        r = client.post("/api/users/me/change-password", headers=headers, json={
            "current_password": "wrongpassword",
            "new_password": "NewPass456",
        })
        assert r.status_code == 400

    def test_short_new_password_rejected(self, client, customer):
        headers, _ = customer
        r = client.post("/api/users/me/change-password", headers=headers, json={
            "current_password": "password123",
            "new_password": "abc",
        })
        assert r.status_code in (400, 422)


class TestGetUserById:
    def test_admin_can_get_any_user(self, client, customer, admin):
        customer_headers, _ = customer
        admin_headers, _ = admin
        me = client.get("/api/users/me", headers=customer_headers).json()
        r = client.get(f"/api/users/{me['id']}", headers=admin_headers)
        assert r.status_code == 200

    def test_customer_cannot_get_other_user(self, client, customer, owner):
        customer_headers, _ = customer
        owner_headers, _ = owner
        owner_me = client.get("/api/users/me", headers=owner_headers).json()
        r = client.get(f"/api/users/{owner_me['id']}", headers=customer_headers)
        assert r.status_code in (403, 404)
