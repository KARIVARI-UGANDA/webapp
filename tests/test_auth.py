"""Tests for /api/auth/* endpoints."""
import pytest
from tests.conftest import _register, _login, _auth_headers


class TestSignup:
    def test_customer_signup_success(self, client):
        r = _register(client, "new@test.com", "password123", "New User")
        assert r.status_code == 201
        data = r.json()
        assert data["role"] == "customer"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_owner_signup_success(self, client):
        r = _register(client, "owner2@test.com", "password123", "Owner User", role="owner", phone="+256703000001")
        assert r.status_code == 201
        assert r.json()["role"] == "owner"

    def test_duplicate_email_rejected(self, client):
        _register(client, "dup@test.com", "password123", "First")
        r = _register(client, "dup@test.com", "password123", "Second")
        assert r.status_code in (400, 409)

    def test_short_password_rejected(self, client):
        r = _register(client, "short@test.com", "abc", "Short Pass")
        assert r.status_code == 422

    def test_invalid_email_rejected(self, client):
        r = _register(client, "not-an-email", "password123", "Bad Email")
        assert r.status_code == 422

    def test_invalid_role_rejected(self, client):
        r = client.post("/api/auth/signup", json={
            "email": "role@test.com",
            "password": "password123",
            "full_name": "Role Test",
            "phone_number": "+256700111222",
            "role": "superuser",
        })
        assert r.status_code == 422

    def test_missing_required_fields(self, client):
        r = client.post("/api/auth/signup", json={"email": "x@x.com"})
        assert r.status_code == 422


class TestLogin:
    def test_valid_login(self, client):
        _register(client, "login@test.com", "password123", "Login User")
        r = _login(client, "login@test.com", "password123")
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_wrong_password(self, client):
        _register(client, "wrongpw@test.com", "password123", "Wrong PW")
        r = _login(client, "wrongpw@test.com", "wrongpassword")
        assert r.status_code == 401

    def test_unknown_email(self, client):
        r = _login(client, "nobody@test.com", "password123")
        assert r.status_code == 401

    def test_token_type_is_bearer(self, client):
        _register(client, "bearer@test.com", "password123", "Bearer Test")
        r = _login(client, "bearer@test.com", "password123")
        assert r.json()["token_type"] == "bearer"


class TestMe:
    def test_get_me(self, client, customer):
        headers, info = customer
        r = client.get("/api/auth/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == info["email"]

    def test_get_me_unauthenticated(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code in (401, 403)

    def test_get_me_invalid_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer bogus.token.here"})
        assert r.status_code == 401


class TestRefreshToken:
    def test_refresh_issues_new_access_token(self, client):
        _register(client, "refresh@test.com", "password123", "Refresh User")
        login = _login(client, "refresh@test.com", "password123").json()
        r = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_invalid_refresh_token_rejected(self, client):
        r = client.post("/api/auth/refresh", json={"refresh_token": "invalid.token"})
        assert r.status_code == 401


class TestLogout:
    def test_logout_success(self, client):
        _register(client, "logout@test.com", "password123", "Logout User")
        login = _login(client, "logout@test.com", "password123").json()
        r = client.post("/api/auth/logout", json={"refresh_token": login["refresh_token"]})
        assert r.status_code == 200

    def test_refresh_after_logout_fails(self, client):
        # Use the signup token directly — only one refresh token exists so logout revokes it cleanly
        signup = _register(client, "loggedout@test.com", "password123", "Logged Out").json()
        rt = signup["refresh_token"]
        client.post("/api/auth/logout", json={"refresh_token": rt})
        r = client.post("/api/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 401


class TestPasswordReset:
    def test_forgot_password_known_email(self, client):
        _register(client, "reset@test.com", "password123", "Reset User")
        r = client.post("/api/auth/forgot-password", json={"email": "reset@test.com"})
        assert r.status_code == 200

    def test_forgot_password_unknown_email(self, client):
        # Should return 200 to not leak email existence
        r = client.post("/api/auth/forgot-password", json={"email": "ghost@test.com"})
        assert r.status_code == 200
