"""Regression tests for login performance optimizations.

These tests verify that the specific optimizations made during the
performance audit are functioning correctly:

1. Combined roles+permissions query returns same results as separate queries
2. Combined reset_failed_logins + update_last_login works correctly
3. Background tasks don't block login response (no _bg_context in response)
4. Login response doesn't include internal _bg_context field
5. Successful login resets failed_login_count and updates last_login_at
6. Failed login still increments failed_login_count and creates history
"""

from authentication.models import LoginHistory
from authentication.repositories import (
    UserRepository,
    UserRoleRepository,
)


class TestCombinedRolesPermissionsQuery:
    """Test the combined get_roles_and_permissions_for_user method."""

    def test_returns_both_roles_and_permissions(self, db_session):
        """Verify the combined query returns both roles and permissions."""
        repo = UserRoleRepository(db_session)
        # admin@dataflow.io is user id 1 (seeded super admin)
        roles, permissions = repo.get_roles_and_permissions_for_user(1)
        assert isinstance(roles, list)
        assert isinstance(permissions, list)
        assert "super_admin" in roles
        assert len(permissions) > 0

    def test_roles_match_separate_query(self, db_session):
        """Verify combined query roles match the separate get_roles_for_user."""
        repo = UserRoleRepository(db_session)
        separate_roles = set(repo.get_roles_for_user(1))
        combined_roles, _ = repo.get_roles_and_permissions_for_user(1)
        assert separate_roles == set(combined_roles)

    def test_permissions_match_separate_query(self, db_session):
        """Verify combined query permissions match get_all_permissions_for_user."""
        repo = UserRoleRepository(db_session)
        separate_perms = set(repo.get_all_permissions_for_user(1))
        _, combined_perms = repo.get_roles_and_permissions_for_user(1)
        assert separate_perms == set(combined_perms)

    def test_nonexistent_user_returns_empty(self, db_session):
        """Verify query returns empty lists for nonexistent user."""
        repo = UserRoleRepository(db_session)
        roles, permissions = repo.get_roles_and_permissions_for_user(99999)
        assert roles == []
        assert permissions == []


class TestCombinedResetAndLastLogin:
    """Test the combined reset_failed_logins_and_update_last_login method."""

    def test_resets_failed_count(self, db_session):
        """Verify failed_login_count is reset to 0."""
        repo = UserRepository(db_session)
        # First increment to set a non-zero count
        repo.increment_failed_login(1)
        user = repo.get_by_id(1)
        assert user.failed_login_count > 0

        # Now reset and update last login
        repo.reset_failed_logins_and_update_last_login(1)
        db_session.commit()

        user = repo.get_by_id(1)
        assert user.failed_login_count == 0
        assert user.locked_until is None

    def test_updates_last_login(self, db_session):
        """Verify last_login_at is updated."""
        repo = UserRepository(db_session)
        user_before = repo.get_by_id(1)
        old_last_login = user_before.last_login_at

        repo.reset_failed_logins_and_update_last_login(1)
        db_session.commit()

        user_after = repo.get_by_id(1)
        assert user_after.last_login_at is not None
        if old_last_login is not None:
            assert user_after.last_login_at >= old_last_login

    def test_clears_lock(self, db_session):
        """Verify locked_until is cleared."""
        repo = UserRepository(db_session)
        # Lock the user by incrementing past threshold
        from shared.security import ACCOUNT_LOCKOUT_THRESHOLD

        for _ in range(ACCOUNT_LOCKOUT_THRESHOLD):
            repo.increment_failed_login(1)
        db_session.commit()

        user = repo.get_by_id(1)
        assert user.locked_until is not None

        # Now reset
        repo.reset_failed_logins_and_update_last_login(1)
        db_session.commit()

        user = repo.get_by_id(1)
        assert user.locked_until is None


class TestLoginResponseShape:
    """Test that login response doesn't leak internal fields."""

    def test_no_bg_context_in_response(self, client):
        """Verify _bg_context is not included in the API response."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "_bg_context" not in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    def test_login_response_has_roles_and_permissions(self, client):
        """Verify login response includes roles and permissions in user object."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        assert response.status_code == 200
        user = response.json()["data"]["user"]
        assert "roles" in user
        assert "permissions" in user
        assert "super_admin" in user["roles"]
        assert len(user["permissions"]) > 0


class TestLoginSideEffects:
    """Test that login side effects occur correctly."""

    def test_successful_login_creates_session(self, client, db_session):
        """Verify a session record is created on successful login."""
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        from authentication.models import Session

        sessions = db_session.query(Session).filter(Session.user_id == 1).all()
        assert len(sessions) >= 1

    def test_successful_login_creates_history(self, client, db_session):
        """Verify a login history record is created on successful login."""
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "Admin@12345",
            },
        )
        histories = (
            db_session.query(LoginHistory)
            .filter(LoginHistory.user_id == 1, LoginHistory.success == True)  # noqa: E712
            .all()
        )
        assert len(histories) >= 1

    def test_failed_login_creates_failed_history(self, client, db_session):
        """Verify a failed login history record is created on failed login."""
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "WrongPassword1!",
            },
        )
        histories = (
            db_session.query(LoginHistory)
            .filter(LoginHistory.user_id == 1, LoginHistory.success == False)  # noqa: E712
            .all()
        )
        assert len(histories) >= 1

    def test_failed_login_does_not_create_session(self, client, db_session):
        """Verify no session is created on failed login."""
        from authentication.models import Session

        count_before = len(db_session.query(Session).filter(Session.user_id == 1).all())
        client.post(
            "/api/auth/login",
            json={
                "email": "admin@dataflow.io",
                "password": "WrongPassword1!",
            },
        )
        count_after = len(db_session.query(Session).filter(Session.user_id == 1).all())
        assert count_after == count_before
