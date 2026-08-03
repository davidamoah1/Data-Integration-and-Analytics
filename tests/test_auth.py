"""Tests for authentication endpoints — login, logout, refresh, password management."""


class TestLogin:
    """Tests for the login endpoint."""

    def test_login_success(self, client):
        """Test successful login with correct credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == "admin@dataflow.io"
        assert "super_admin" in data["data"]["user"]["roles"]

    def test_login_wrong_password(self, client):
        """Test login with incorrect password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "WrongPassword1!",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with email that doesn't exist."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nobody@nowhere.com",
                "password": "SomePassword1!",
            },
        )
        assert response.status_code == 401

    def test_login_remember_me(self, client):
        """Test login with remember_me flag."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
                "remember_me": True,
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    def test_login_invalid_payload(self, client):
        """Test login with missing fields."""
        response = client.post("/api/auth/login", json={"email": "admin@dataflow.io"})
        assert response.status_code == 422


class TestTokenRefresh:
    """Tests for the token refresh endpoint."""

    def test_refresh_token_success(self, client):
        """Test refreshing an access token."""
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        """Test refreshing with an invalid token."""
        response = client.post("/api/auth/refresh", json={"refresh_token": "invalid-token"})
        assert response.status_code == 401


class TestLogout:
    """Tests for the logout endpoint."""

    def test_logout_success(self, client):
        """Test successful logout."""
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
        assert response.status_code == 200

        # Verify token is revoked
        refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401


class TestChangePassword:
    """Tests for the change password endpoint."""

    def test_change_password_success(self, client, auth_headers):
        """Test changing password with correct current password."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Admin@12345",
                "new_password": "NewPassword@123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify old password no longer works
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        assert login_resp.status_code == 401

        # Verify new password works
        login_resp = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "NewPassword@123",
            },
        )
        assert login_resp.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "WrongPassword1!",
                "new_password": "NewPassword@123",
            },
            headers=auth_headers,
        )
        assert response.status_code == 401

    def test_change_password_weak(self, client, auth_headers):
        """Test changing to a weak password (should fail validation)."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Admin@12345",
                "new_password": "weak",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestForgotResetPassword:
    """Tests for forgot password and reset password flow."""

    def test_forgot_password(self, client):
        """Test requesting a password reset."""
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": "admin@dataflow.io",
            },
        )
        assert response.status_code == 200

    def test_forgot_password_nonexistent(self, client):
        """Test requesting reset for nonexistent email (should still return 200)."""
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": "nobody@nowhere.com",
            },
        )
        assert response.status_code == 200


class TestProfile:
    """Tests for profile endpoints."""

    def test_get_profile(self, client, auth_headers):
        """Test getting the current user's profile."""
        response = client.get("/api/auth/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "admin@dataflow.io"
        assert data["full_name"] == "System Administrator"
        assert "super_admin" in data["roles"]
        assert "permissions" in data

    def test_get_profile_no_auth(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/auth/profile")
        assert response.status_code == 401

    def test_update_profile(self, client, auth_headers):
        """Test updating profile."""
        response = client.put(
            "/api/auth/profile",
            json={
                "phone": "+1234567890",
                "language": "es",
                "timezone": "America/New_York",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["phone"] == "+1234567890"
        assert data["language"] == "es"
        assert data["timezone"] == "America/New_York"


class TestSessions:
    """Tests for session management."""

    def test_get_sessions(self, client, auth_headers):
        """Test getting active sessions."""
        # Login to create a session
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        response = client.get("/api/auth/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1


class TestLoginHistory:
    """Tests for login history."""

    def test_get_login_history(self, client, auth_headers):
        """Test getting login history."""
        # Login to create history
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        response = client.get("/api/auth/login-history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1


class TestSignup:
    """Tests for the public signup endpoint."""

    def test_signup_success(self, client):
        """Test successful self-registration."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@test.com",
                "password": "StrongPass1!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "newuser@test.com"
        assert data["data"]["full_name"] == "New User"

    def test_signup_with_org(self, client):
        """Test signup with organization creation."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "orgadmin@test.com",
                "password": "StrongPass1!",
                "full_name": "Org Admin",
                "organization_name": "Test Company Inc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["organization_id"] is not None

    def test_signup_duplicate_email(self, client):
        """Test signup with existing email fails."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "admin@dataflow.io",
                "password": "StrongPass1!",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 409

    def test_signup_weak_password(self, client):
        """Test signup with weak password fails."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weakpass@test.com",
                "password": "weak",
                "full_name": "Weak Pass User",
            },
        )
        assert response.status_code == 422
