"""Tests for user management and RBAC â€” roles, permissions, authorization checks."""


class TestUserManagement:
    """Tests for user CRUD operations."""

    def test_list_users(self, client, auth_headers):
        """Test listing users."""
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "users" in data
        assert data["total"] >= 1

    def test_create_user(self, client, auth_headers):
        """Test creating a new user."""
        response = client.post(
            "/api/users",
            json={
                "email": "newuser@test.com",
                "password": "TestUser@123",
                "full_name": "Test User",
                "phone": "+1234567890",
                "role_names": ["viewer"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "newuser@test.com"
        assert data["full_name"] == "Test User"
        assert "viewer" in data["roles"]

    def test_create_duplicate_user(self, client, auth_headers):
        """Test creating a user with an existing email."""
        response = client.post(
            "/api/users",
            json={
                "email": "admin@dataflow.io",
                "password": "TestUser@123",
                "full_name": "Duplicate Admin",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_create_user_weak_password(self, client, auth_headers):
        """Test creating a user with a weak password."""
        response = client.post(
            "/api/users",
            json={
                "email": "weak@test.com",
                "password": "weak",
                "full_name": "Weak User",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_get_user(self, client, auth_headers):
        """Test getting a specific user."""
        # First create a user
        create_resp = client.post(
            "/api/users",
            json={
                "email": "getme@test.com",
                "password": "TestUser@123",
                "full_name": "Get Me",
            },
            headers=auth_headers,
        )
        user_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "getme@test.com"

    def test_get_nonexistent_user(self, client, auth_headers):
        """Test getting a user that doesn't exist."""
        response = client.get("/api/users/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_user(self, client, auth_headers):
        """Test updating a user."""
        create_resp = client.post(
            "/api/users",
            json={
                "email": "updateme@test.com",
                "password": "TestUser@123",
                "full_name": "Update Me",
            },
            headers=auth_headers,
        )
        user_id = create_resp.json()["data"]["id"]

        response = client.put(
            f"/api/users/{user_id}",
            json={
                "full_name": "Updated Name",
                "phone": "+9876543210",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+9876543210"

    def test_delete_user(self, client, auth_headers):
        """Test soft deleting a user."""
        create_resp = client.post(
            "/api/users",
            json={
                "email": "deleteme@test.com",
                "password": "TestUser@123",
                "full_name": "Delete Me",
            },
            headers=auth_headers,
        )
        user_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify user is gone from listings
        get_resp = client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_assign_roles(self, client, auth_headers):
        """Test assigning roles to a user."""
        create_resp = client.post(
            "/api/users",
            json={
                "email": "roleuser@test.com",
                "password": "TestUser@123",
                "full_name": "Role User",
            },
            headers=auth_headers,
        )
        user_id = create_resp.json()["data"]["id"]

        response = client.post(
            f"/api/users/{user_id}/roles", json=["analyst", "viewer"], headers=auth_headers
        )
        assert response.status_code == 200


class TestRoleManagement:
    """Tests for role CRUD operations."""

    def test_list_roles(self, client, auth_headers):
        """Test listing all roles."""
        response = client.get("/api/roles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 10  # 10 default roles

        role_names = [r["name"] for r in data]
        assert "super_admin" in role_names
        assert "viewer" in role_names
        assert "org_admin" in role_names

    def test_create_role(self, client, auth_headers):
        """Test creating a custom role."""
        response = client.post(
            "/api/roles",
            json={
                "name": "custom_role",
                "display_name": "Custom Role",
                "description": "A custom role for testing",
                "permission_names": ["dashboard.read", "report.read"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "custom_role"
        assert "dashboard.read" in data["permissions"]
        assert "report.read" in data["permissions"]

    def test_create_duplicate_role(self, client, auth_headers):
        """Test creating a role with an existing name."""
        response = client.post(
            "/api/roles",
            json={
                "name": "viewer",
                "display_name": "Duplicate Viewer",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_update_role(self, client, auth_headers):
        """Test updating a role."""
        create_resp = client.post(
            "/api/roles",
            json={
                "name": "updaterole",
                "display_name": "Update Role",
                "permission_names": ["dashboard.read"],
            },
            headers=auth_headers,
        )
        role_id = create_resp.json()["data"]["id"]

        response = client.put(
            f"/api/roles/{role_id}",
            json={
                "display_name": "Updated Role Name",
                "permission_names": ["dashboard.read", "analytics.view"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["display_name"] == "Updated Role Name"
        assert "analytics.view" in data["permissions"]

    def test_delete_custom_role(self, client, auth_headers):
        """Test deleting a custom role."""
        create_resp = client.post(
            "/api/roles",
            json={
                "name": "deleterole",
                "display_name": "Delete Role",
            },
            headers=auth_headers,
        )
        role_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/roles/{role_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_cannot_delete_system_role(self, client, auth_headers):
        """Test that system roles cannot be deleted."""
        roles_resp = client.get("/api/roles", headers=auth_headers)
        roles = roles_resp.json()["data"]
        super_admin_role = [r for r in roles if r["name"] == "super_admin"][0]

        response = client.delete(f"/api/roles/{super_admin_role['id']}", headers=auth_headers)
        assert response.status_code == 403


class TestPermissionListing:
    """Tests for permission listing."""

    def test_list_permissions(self, client, auth_headers):
        """Test listing all permissions."""
        response = client.get("/api/roles/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 20  # At least 20 default permissions

        perm_names = [p["name"] for p in data]
        assert "users.create" in perm_names
        assert "pipelines.execute" in perm_names
        assert "dashboard.read" in perm_names


class TestAuthorization:
    """Tests for permission-based authorization."""

    def test_no_token_returns_401(self, client):
        """Test that endpoints without token return 401."""
        response = client.get("/api/users")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Test that invalid tokens return 401."""
        response = client.get("/api/users", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401

    def test_viewer_cannot_create_users(self, client, auth_headers):
        """Test that a viewer role user cannot create users (403)."""
        # Create a viewer user
        create_resp = client.post(
            "/api/users",
            json={
                "email": "viewer@test.com",
                "password": "TestUser@123",
                "full_name": "Viewer User",
                "role_names": ["viewer"],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 200

        # Login as viewer
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "viewer@test.com",
                "password": "TestUser@123",
            },
        )
        assert login_resp.status_code == 200
        viewer_token = login_resp.json()["data"]["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        # Try to create a user â€” should be forbidden
        response = client.post(
            "/api/users",
            json={
                "email": "another@test.com",
                "password": "TestUser@123",
                "full_name": "Another User",
            },
            headers=viewer_headers,
        )
        assert response.status_code == 403

    def test_data_engineer_can_view_dashboard(self, client, auth_headers):
        """Test that a dept_manager role user has dashboard.read permission."""
        create_resp = client.post(
            "/api/users",
            json={
                "email": "engineer@test.com",
                "password": "TestUser@123",
                "full_name": "Engineer User",
                "role_names": ["dept_manager"],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 200

        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "engineer@test.com",
                "password": "TestUser@123",
            },
        )
        eng_data = login_resp.json()["data"]
        assert "dashboard.read" in eng_data["user"]["permissions"]
        assert "pipelines.execute" in eng_data["user"]["permissions"]

    def test_auditor_can_view_audit(self, client, auth_headers):
        """Test that an org_admin role user has audit.view permission."""
        create_resp = client.post(
            "/api/users",
            json={
                "email": "auditor@test.com",
                "password": "TestUser@123",
                "full_name": "Auditor User",
                "role_names": ["org_admin"],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 200

        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "auditor@test.com",
                "password": "TestUser@123",
            },
        )
        aud_data = login_resp.json()["data"]
        assert "audit.view" in aud_data["user"]["permissions"]
