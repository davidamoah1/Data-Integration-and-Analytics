"""Tests for audit log endpoints."""


class TestAuditLogs:
    """Tests for audit log retrieval."""

    def test_list_audit_logs(self, client, auth_headers):
        """Test listing audit logs (should have entries from login activity)."""
        # Login to generate audit entries
        client.post(
            "/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )

        response = client.get("/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "logs" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_list_audit_logs_pagination(self, client, auth_headers):
        """Test audit log pagination."""
        response = client.get("/audit/logs?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_list_security_logs(self, client, auth_headers):
        """Test listing security logs."""
        response = client.get("/audit/security", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "logs" in data

    def test_list_system_logs(self, client, auth_headers):
        """Test listing system logs."""
        response = client.get("/audit/system", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "logs" in data

    def test_audit_requires_permission(self, client, auth_headers):
        """Test that audit endpoints require audit.view permission."""
        # Create a viewer user (no audit.view permission)
        client.post(
            "/users",
            json={
                "email": "viewer2@test.com",
                "password": "TestUser@123",
                "full_name": "Viewer Two",
                "role_names": ["viewer"],
            },
            headers=auth_headers,
        )

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "viewer2@test.com",
                "password": "TestUser@123",
            },
        )
        viewer_token = login_resp.json()["data"]["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        response = client.get("/audit/logs", headers=viewer_headers)
        assert response.status_code == 403
