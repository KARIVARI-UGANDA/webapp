"""Tests for /api/kyc/* endpoints."""
import pytest


class TestKycStatus:
    def test_customer_can_get_kyc_status(self, client, customer):
        headers, _ = customer
        r = client.get("/api/kyc/me", headers=headers)
        assert r.status_code == 200

    def test_unauthenticated_cannot_get_kyc(self, client):
        r = client.get("/api/kyc/me")
        assert r.status_code in (401, 403)


class TestKycSubmission:
    def test_customer_can_submit_kyc(self, client, customer):
        headers, _ = customer
        r = client.post("/api/kyc/me/submit", headers=headers, json={
            "document_type": "passport",
            "document_number": "A12345678",
            "document_front_url": "https://example.com/passport_front.jpg",
        })
        assert r.status_code in (200, 201)

    def test_kyc_with_back_url(self, client, customer):
        headers, _ = customer
        r = client.post("/api/kyc/me/submit", headers=headers, json={
            "document_type": "national_id",
            "document_number": "CM123456789",
            "document_front_url": "https://example.com/id_front.jpg",
            "document_back_url": "https://example.com/id_back.jpg",
        })
        assert r.status_code in (200, 201)

    def test_invalid_document_type_rejected(self, client, customer):
        headers, _ = customer
        r = client.post("/api/kyc/me/submit", headers=headers, json={
            "document_type": "selfie",
            "document_number": "X99",
            "document_front_url": "https://example.com/selfie.jpg",
        })
        assert r.status_code == 422

    def test_missing_front_url_rejected(self, client, customer):
        headers, _ = customer
        r = client.post("/api/kyc/me/submit", headers=headers, json={
            "document_type": "passport",
            "document_number": "A12345678",
        })
        assert r.status_code == 422

    def test_unauthenticated_cannot_submit_kyc(self, client):
        r = client.post("/api/kyc/me/submit", json={
            "document_type": "passport",
            "document_number": "A12345678",
            "document_front_url": "https://example.com/front.jpg",
        })
        assert r.status_code in (401, 403)


class TestAdminKycReview:
    def test_admin_can_list_pending_kyc(self, client, admin):
        headers, _ = admin
        r = client.get("/api/admin/kyc/manual-review", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_customer_cannot_access_kyc_review(self, client, customer):
        headers, _ = customer
        r = client.get("/api/admin/kyc/manual-review", headers=headers)
        assert r.status_code == 403
