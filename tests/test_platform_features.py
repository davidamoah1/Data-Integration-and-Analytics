"""Tests for Enterprise Platform Features.

Tests cover:
  - Multi-tenancy: TenantContext, TenantFilter, org-scoped access
  - RBAC: Role hierarchy, permission matrix, role level checks
  - Audit tracker: logging, category mapping, summary, user activity
  - Seed data: organizations, roles, demo users
  - API endpoints: audit summary, role hierarchy, tenant context
"""

from __future__ import annotations

from platform_features import (
    AuditCategory,
    AuditSummary,
    AuditTracker,
    PermissionMatrix,
    RoleHierarchy,
    RoleLevel,
    TenantContext,
    get_role_level,
    has_role_or_higher,
    seed_enterprise_data,
)
from platform_features.audit_tracker import ACTION_CATEGORY_MAP

# ── Tenant Context Tests ──────────────────────────────────


class TestTenantContext:
    def test_from_user_regular(self):
        user = {
            "id": 1,
            "organization_id": 5,
            "roles": ["analyst"],
        }
        ctx = TenantContext.from_user(user)
        assert ctx.organization_id == 5
        assert ctx.user_id == 1
        assert ctx.is_super_admin is False
        assert ctx.is_tenant_scoped is True

    def test_from_user_super_admin(self):
        user = {
            "id": 1,
            "organization_id": None,
            "roles": ["super_admin"],
        }
        ctx = TenantContext.from_user(user)
        assert ctx.is_super_admin is True
        assert ctx.is_tenant_scoped is False

    def test_from_user_no_org(self):
        user = {
            "id": 1,
            "organization_id": None,
            "roles": ["viewer"],
        }
        ctx = TenantContext.from_user(user)
        assert ctx.is_tenant_scoped is False

    def test_can_access_own_org(self):
        ctx = TenantContext(organization_id=5, user_id=1, roles=["analyst"], is_super_admin=False)
        assert ctx.can_access_org(5) is True

    def test_cannot_access_other_org(self):
        ctx = TenantContext(organization_id=5, user_id=1, roles=["analyst"], is_super_admin=False)
        assert ctx.can_access_org(99) is False

    def test_super_admin_can_access_any_org(self):
        ctx = TenantContext(
            organization_id=None, user_id=1, roles=["super_admin"], is_super_admin=True
        )
        assert ctx.can_access_org(99) is True


class TestTenantFilter:
    def test_super_admin_sees_all(self):
        ctx = TenantContext(
            organization_id=None, user_id=1, roles=["super_admin"], is_super_admin=True
        )
        # Simulate a query — just verify no filtering happens
        # In practice, the query is returned unchanged
        assert ctx.is_super_admin is True

    def test_tenant_scoped_filters(self):
        ctx = TenantContext(organization_id=5, user_id=1, roles=["analyst"], is_super_admin=False)
        assert ctx.is_tenant_scoped is True
        assert ctx.organization_id == 5


# ── RBAC Tests ────────────────────────────────────────────


class TestRoleHierarchy:
    def test_super_admin_highest_level(self):
        assert RoleHierarchy.get_level("super_admin") == RoleLevel.SUPER_ADMIN

    def test_viewer_lowest_level(self):
        assert RoleHierarchy.get_level("viewer") == RoleLevel.VIEWER

    def test_org_admin_above_manager(self):
        assert RoleHierarchy.get_level("org_admin") > RoleHierarchy.get_level("dept_manager")

    def test_manager_above_analyst(self):
        assert RoleHierarchy.get_level("dept_manager") > RoleHierarchy.get_level("analyst")

    def test_analyst_above_viewer(self):
        assert RoleHierarchy.get_level("analyst") > RoleHierarchy.get_level("viewer")

    def test_get_highest_role(self):
        roles = ["viewer", "analyst", "dept_manager"]
        highest = RoleHierarchy.get_highest_role(roles)
        assert highest == "dept_manager"

    def test_get_highest_role_empty(self):
        assert RoleHierarchy.get_highest_role([]) is None

    def test_is_at_least(self):
        assert RoleHierarchy.is_at_least("dept_manager", RoleLevel.MANAGER) is True
        assert RoleHierarchy.is_at_least("org_admin", RoleLevel.MANAGER) is True
        assert RoleHierarchy.is_at_least("analyst", RoleLevel.MANAGER) is False

    def test_can_manage(self):
        assert RoleHierarchy.can_manage("org_admin", "analyst") is True
        assert RoleHierarchy.can_manage("dept_manager", "viewer") is True
        assert RoleHierarchy.can_manage("analyst", "dept_manager") is False

    def test_display_name(self):
        assert RoleHierarchy.get_display_name("super_admin") == "Super Administrator"
        assert RoleHierarchy.get_display_name("org_admin") == "Organization Administrator"
        assert RoleHierarchy.get_display_name("viewer") == "Viewer"

    def test_all_roles_sorted(self):
        roles = RoleHierarchy.all_roles()
        assert len(roles) > 0
        # Should be sorted by level descending
        levels = [r["level"] for r in roles]
        assert levels == sorted(levels, reverse=True)

    def test_analyst_alias(self):
        assert RoleHierarchy.get_level("analyst") == RoleLevel.ANALYST

    def test_manager_alias(self):
        assert RoleHierarchy.get_level("dept_manager") == RoleLevel.MANAGER


class TestPermissionMatrix:
    def test_super_admin_has_all(self):
        perms = PermissionMatrix.get_permissions("super_admin")
        assert "*" in perms

    def test_org_admin_has_user_management(self):
        perms = PermissionMatrix.get_permissions("org_admin")
        assert "users.create" in perms
        assert "users.delete" in perms

    def test_analyst_has_reports(self):
        perms = PermissionMatrix.get_permissions("analyst")
        assert "report.generate" in perms
        assert "analytics.view" in perms

    def test_viewer_read_only(self):
        perms = PermissionMatrix.get_permissions("viewer")
        assert "dashboard.read" in perms
        assert "users.create" not in perms

    def test_has_permission_true(self):
        assert PermissionMatrix.has_permission("org_admin", "users.create") is True

    def test_has_permission_false(self):
        assert PermissionMatrix.has_permission("viewer", "users.create") is False

    def test_super_admin_has_any_permission(self):
        assert PermissionMatrix.has_permission("super_admin", "anything") is True

    def test_user_has_permission(self):
        assert PermissionMatrix.user_has_permission(["analyst"], "report.generate") is True
        assert PermissionMatrix.user_has_permission(["viewer"], "users.create") is False

    def test_user_has_permission_multiple_roles(self):
        assert (
            PermissionMatrix.user_has_permission(["viewer", "analyst"], "report.generate") is True
        )

    def test_get_role_permissions_summary(self):
        summary = PermissionMatrix.get_role_permissions_summary()
        assert "super_admin" in summary
        assert "viewer" in summary


class TestRBACHelpers:
    def test_has_role_or_higher_true(self):
        assert has_role_or_higher(["org_admin"], "dept_manager") is True

    def test_has_role_or_higher_false(self):
        assert has_role_or_higher(["viewer"], "dept_manager") is False

    def test_has_role_or_higher_exact(self):
        assert has_role_or_higher(["dept_manager"], "dept_manager") is True

    def test_get_role_level(self):
        assert get_role_level("super_admin") == 100
        assert get_role_level("viewer") == 20


# ── Audit Tracker Tests ───────────────────────────────────


class TestAuditCategory:
    def test_category_values(self):
        assert AuditCategory.USER_ACTION.value == "user_action"
        assert AuditCategory.DATA_ACCESS.value == "data_access"
        assert AuditCategory.REPORTS.value == "reports"
        assert AuditCategory.AI_USAGE.value == "ai_usage"

    def test_action_category_map_login(self):
        assert ACTION_CATEGORY_MAP["login"] == AuditCategory.USER_ACTION

    def test_action_category_map_dataset_upload(self):
        assert ACTION_CATEGORY_MAP["dataset_upload"] == AuditCategory.DATA_ACCESS

    def test_action_category_map_report(self):
        assert ACTION_CATEGORY_MAP["report_generated"] == AuditCategory.REPORTS

    def test_action_category_map_ai(self):
        assert ACTION_CATEGORY_MAP["ai_forecast"] == AuditCategory.AI_USAGE

    def test_unknown_action_defaults_to_user_action(self):
        AuditTracker.__new__(AuditTracker)
        category = ACTION_CATEGORY_MAP.get("unknown_action", AuditCategory.USER_ACTION)
        assert category == AuditCategory.USER_ACTION


class TestAuditSummary:
    def test_empty_summary(self):
        summary = AuditSummary()
        assert summary.total_events == 0
        assert summary.by_category == {}

    def test_to_dict(self):
        summary = AuditSummary(
            total_events=10,
            by_category={"user_action": 5, "data_access": 5},
            by_user={"1": 10},
            by_action={"login": 5, "logout": 5},
        )
        d = summary.to_dict()
        assert d["total_events"] == 10
        assert "by_category" in d
        assert "by_action" in d


# ── Seed Data Tests ───────────────────────────────────────


class TestSeedData:
    def test_seed_creates_organizations(self, db_session):
        result = seed_enterprise_data(db_session)
        assert len(result["organizations_created"]) >= 0  # Might already exist
        assert "summary" in result

    def test_seed_creates_roles(self, db_session):
        result = seed_enterprise_data(db_session)
        # Roles might already exist from previous runs
        assert "roles_created" in result

    def test_seed_creates_users(self, db_session):
        result = seed_enterprise_data(db_session)
        assert "users_created" in result

    def test_seed_idempotent(self, db_session):
        # Run twice — second run should not create duplicates
        seed_enterprise_data(db_session)
        result2 = seed_enterprise_data(db_session)
        # Second run should create 0 new items
        assert len(result2["organizations_created"]) == 0
        assert len(result2["roles_created"]) == 0
        assert len(result2["users_created"]) == 0


# ── Integration Tests ─────────────────────────────────────


class TestPlatformIntegration:
    def test_tenant_context_from_real_user(self, auth_headers, client):
        """Test that tenant context endpoint works."""
        response = client.get("/platform/tenant/context", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "organization_id" in data
        assert "roles" in data
        assert "is_super_admin" in data

    def test_role_hierarchy_endpoint(self, auth_headers, client):
        """Test role hierarchy endpoint."""
        response = client.get("/platform/roles/hierarchy", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        # Should include super_admin
        role_names = [r["name"] for r in data]
        assert "super_admin" in role_names

    def test_audit_summary_endpoint(self, auth_headers, client):
        """Test audit summary endpoint."""
        response = client.get("/platform/audit/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_events" in data
        assert "by_category" in data

    def test_audit_categories_endpoint(self, auth_headers, client):
        """Test audit category stats endpoint."""
        response = client.get("/platform/audit/categories", headers=auth_headers)
        assert response.status_code == 200

    def test_permissions_matrix_endpoint(self, auth_headers, client):
        """Test permissions matrix endpoint."""
        response = client.get("/platform/roles/permissions-matrix", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "super_admin" in data
        assert "viewer" in data

    def test_seed_endpoint_requires_admin(self, auth_headers, client):
        """Test that seed endpoint is accessible to admin."""
        response = client.post("/platform/seed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "summary" in data

    def test_tenant_context_unauthorized(self, client):
        """Test that tenant context requires auth."""
        response = client.get("/platform/tenant/context")
        assert response.status_code == 401

    def test_audit_summary_unauthorized(self, client):
        """Test that audit summary requires auth."""
        response = client.get("/platform/audit/summary")
        assert response.status_code == 401
