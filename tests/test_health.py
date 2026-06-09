"""Tests for health check and public page routes."""


class TestHealthCheck:
    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_returns_ok_status(self, client):
        r = client.get("/api/health")
        assert r.json()["status"] == "ok"

    def test_health_includes_version(self, client):
        r = client.get("/api/health")
        assert "version" in r.json()


class TestPublicPages:
    def test_index_page_loads(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_login_page_loads(self, client):
        r = client.get("/login")
        assert r.status_code == 200

    def test_register_page_loads(self, client):
        r = client.get("/register")
        assert r.status_code == 200

    def test_how_it_works_page_loads(self, client):
        r = client.get("/how-it-works")
        assert r.status_code == 200

    def test_about_page_loads(self, client):
        r = client.get("/about")
        assert r.status_code == 200

    def test_vehicles_listing_page_loads(self, client):
        r = client.get("/vehicles")
        assert r.status_code == 200

    def test_owner_login_page_loads(self, client):
        r = client.get("/owner/login")
        assert r.status_code == 200

    def test_nonexistent_page_returns_404(self, client):
        r = client.get("/this-page-does-not-exist")
        assert r.status_code == 404
