"""RBAC Enhancements — Role Hierarchy and Permission Matrix.

Defines the 5 enterprise roles requested:
  - Super Admin (level 100) — full system access
  - Organization Admin (level 80) — manage org users and data
  - Manager (level 60) — manage department operations
  - Analyst (level 40) — analyze data and create reports
  - Viewer (level 20) — read-only access

Maps to existing roles in the system:
  - super_admin → Super Admin
  - org_admin → Organization Admin
  - dept_manager → Manager
  - data_analyst / business_analyst → Analyst
  - viewer → Viewer

Provides:
  - RoleHierarchy: Role levels and inheritance
  - PermissionMatrix: What each role can do
  - has_role_or_higher: Check if user has a role at or above a level
"""

from __future__ import annotations

from enum import IntEnum


class RoleLevel(IntEnum):
    """Role hierarchy levels (higher = more access)."""

    VIEWER = 20
    ANALYST = 40
    MANAGER = 60
    ORG_ADMIN = 80
    SUPER_ADMIN = 100


# Maps role names to levels
ROLE_HIERARCHY: dict[str, int] = {
    "super_admin": RoleLevel.SUPER_ADMIN,
    "org_owner": RoleLevel.SUPER_ADMIN,
    "org_admin": RoleLevel.ORG_ADMIN,
    "dept_manager": RoleLevel.MANAGER,
    "manager": RoleLevel.MANAGER,
    "data_analyst": RoleLevel.ANALYST,
    "business_analyst": RoleLevel.ANALYST,
    "analyst": RoleLevel.ANALYST,
    "data_engineer": RoleLevel.ANALYST,
    "executive": RoleLevel.MANAGER,
    "dept_officer": RoleLevel.VIEWER,
    "auditor": RoleLevel.ANALYST,
    "viewer": RoleLevel.VIEWER,
}


# Permission matrix: role → set of permission strings
PERMISSION_MATRIX: dict[str, set[str]] = {
    "super_admin": {"*"},  # All permissions
    "org_admin": {
        "users.create", "users.read", "users.edit", "users.delete", "users.manage",
        "roles.read",
        "pipelines.create", "pipelines.execute", "pipelines.view",
        "etl.import", "etl.export",
        "dashboard.view", "dashboard.manage",
        "reports.generate", "reports.export", "reports.view",
        "datasets.upload", "datasets.delete", "datasets.view",
        "analytics.view", "analytics.manage", "analytics.export",
        "ai.use",
        "organizations.manage", "departments.manage",
        "audit.view",
        "sessions.manage",
        "profile.update",
        "notifications.manage",
    },
    "manager": {
        "users.read",
        "pipelines.view",
        "etl.import", "etl.export",
        "dashboard.view", "dashboard.manage",
        "reports.generate", "reports.export", "reports.view",
        "datasets.upload", "datasets.view",
        "analytics.view", "analytics.export",
        "ai.use",
        "departments.manage",
        "profile.update",
    },
    "analyst": {
        "dashboard.view",
        "reports.generate", "reports.export", "reports.view",
        "datasets.view",
        "analytics.view", "analytics.export",
        "ai.use",
        "etl.export",
        "profile.update",
    },
    "viewer": {
        "dashboard.view",
        "reports.view",
        "datasets.view",
        "analytics.view",
        "profile.update",
    },
}


# Aliases: maps the user's requested role names to existing system roles
ROLE_ALIASES: dict[str, str] = {
    "super_admin": "super_admin",
    "organization_admin": "org_admin",
    "analyst": "data_analyst",
    "manager": "dept_manager",
    "viewer": "viewer",
}


class RoleHierarchy:
    """Role hierarchy utilities."""

    @staticmethod
    def get_level(role_name: str) -> int:
        """Get the hierarchy level for a role name."""
        return ROLE_HIERARCHY.get(role_name, 0)

    @staticmethod
    def get_highest_role(roles: list[str]) -> str | None:
        """Get the highest-level role from a list."""
        if not roles:
            return None
        return max(roles, key=lambda r: ROLE_HIERARCHY.get(r, 0))

    @staticmethod
    def is_at_least(role_name: str, min_level: RoleLevel) -> bool:
        """Check if a role is at or above the given level."""
        return ROLE_HIERARCHY.get(role_name, 0) >= min_level

    @staticmethod
    def can_manage(manager_role: str, target_role: str) -> bool:
        """Check if a manager role can manage a target role."""
        manager_level = ROLE_HIERARCHY.get(manager_role, 0)
        target_level = ROLE_HIERARCHY.get(target_role, 0)
        return manager_level > target_level

    @staticmethod
    def get_display_name(role_name: str) -> str:
        """Get a human-readable display name for a role."""
        display_names = {
            "super_admin": "Super Admin",
            "org_owner": "Organization Owner",
            "org_admin": "Organization Admin",
            "dept_manager": "Manager",
            "manager": "Manager",
            "data_analyst": "Analyst",
            "business_analyst": "Business Analyst",
            "analyst": "Analyst",
            "data_engineer": "Data Engineer",
            "executive": "Executive",
            "dept_officer": "Department Officer",
            "auditor": "Auditor",
            "viewer": "Viewer",
        }
        return display_names.get(role_name, role_name.replace("_", " ").title())

    @staticmethod
    def all_roles() -> list[dict]:
        """Get all roles with their levels."""
        return sorted(
            [
                {"name": name, "level": level, "display_name": RoleHierarchy.get_display_name(name)}
                for name, level in ROLE_HIERARCHY.items()
            ],
            key=lambda r: r["level"],
            reverse=True,
        )


class PermissionMatrix:
    """Permission matrix utilities."""

    @staticmethod
    def get_permissions(role_name: str) -> set[str]:
        """Get all permissions for a role."""
        if role_name in PERMISSION_MATRIX:
            return PERMISSION_MATRIX[role_name]
        # Check aliases
        alias = ROLE_ALIASES.get(role_name)
        if alias and alias in PERMISSION_MATRIX:
            return PERMISSION_MATRIX[alias]
        return set()

    @staticmethod
    def has_permission(role_name: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        perms = PermissionMatrix.get_permissions(role_name)
        return "*" in perms or permission in perms

    @staticmethod
    def user_has_permission(roles: list[str], permission: str) -> bool:
        """Check if a user with given roles has a permission."""
        for role in roles:
            if PermissionMatrix.has_permission(role, permission):
                return True
        return False

    @staticmethod
    def get_role_permissions_summary() -> dict[str, list[str]]:
        """Get a summary of all roles and their permissions."""
        return {
            role: sorted(perms) if perms != {"*"} else ["* (all permissions)"]
            for role, perms in PERMISSION_MATRIX.items()
        }


def get_role_level(role_name: str) -> int:
    """Convenience function to get a role's level."""
    return RoleHierarchy.get_level(role_name)


def has_role_or_higher(roles: list[str], min_role: str) -> bool:
    """Check if user has a role at or above the given role's level."""
    min_level = ROLE_HIERARCHY.get(min_role, 0)
    for role in roles:
        if ROLE_HIERARCHY.get(role, 0) >= min_level:
            return True
    return False
