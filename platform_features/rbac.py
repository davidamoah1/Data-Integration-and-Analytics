"""RBAC Enhancements — Role Hierarchy and Permission Matrix.

Enterprise roles (9 total):
  Platform level:
    - super_admin (level 100) — full system access (backward compat)
    - platform_owner (level 100) — owns the platform
    - platform_admin (level 90) — manages platform operations
  Organization level:
    - org_admin (level 80) — manages an organization
    - analyst (level 50) — analyzes data, creates dashboards/reports
    - researcher (level 45) — uploads research datasets, statistical analysis
    - viewer (level 20) — read-only access
  Department level:
    - dept_manager (level 60) — manages a department
    - data_entry_officer (level 30) — uploads documents, smart data capture
  Personal level:
    - personal_user (level 10) — personal workspace only

Provides:
  - RoleHierarchy: Role levels and inheritance
  - PermissionMatrix: What each role can do
  - has_role_or_higher: Check if user has a role at or above a level
"""

from __future__ import annotations

from enum import IntEnum


class RoleLevel(IntEnum):
    """Role hierarchy levels (higher = more access)."""

    PERSONAL = 10
    VIEWER = 20
    DATA_ENTRY = 30
    RESEARCHER = 45
    ANALYST = 50
    MANAGER = 60
    ORG_ADMIN = 80
    PLATFORM_ADMIN = 90
    SUPER_ADMIN = 100


# Maps role names to levels
ROLE_HIERARCHY: dict[str, int] = {
    "super_admin": RoleLevel.SUPER_ADMIN,
    "platform_owner": RoleLevel.SUPER_ADMIN,
    "platform_admin": RoleLevel.PLATFORM_ADMIN,
    "org_admin": RoleLevel.ORG_ADMIN,
    "dept_manager": RoleLevel.MANAGER,
    "analyst": RoleLevel.ANALYST,
    "researcher": RoleLevel.RESEARCHER,
    "data_entry_officer": RoleLevel.DATA_ENTRY,
    "viewer": RoleLevel.VIEWER,
    "personal_user": RoleLevel.PERSONAL,
}


# Permission matrix: role → set of permission strings
PERMISSION_MATRIX: dict[str, set[str]] = {
    "super_admin": {"*"},
    "platform_owner": {"*"},
    "platform_admin": {"*"},
    "org_admin": {
        "organization.read", "organization.manage",
        "department.create", "department.manage", "department.read",
        "member.invite", "member.remove", "member.read", "member.manage",
        "role.assign", "role.revoke", "role.read",
        "users.create", "users.read", "users.edit", "users.delete", "users.manage",
        "dataset.create", "dataset.read", "dataset.update", "dataset.delete", "dataset.share", "dataset.export",
        "dashboard.create", "dashboard.read", "dashboard.update", "dashboard.delete", "dashboard.export", "dashboard.share",
        "report.generate", "report.read", "report.update", "report.delete", "report.export",
        "pipelines.create", "pipelines.execute", "pipelines.view", "pipelines.delete",
        "etl.import", "etl.export",
        "analytics.view", "analytics.manage", "analytics.export",
        "ai.use", "audit.view", "notifications.manage", "sessions.manage", "profile.update",
        "ml.read", "ml.write", "ml.execute", "ml.delete",
        "capture.upload", "capture.process", "capture.read",
        "workspace.create", "workspace.manage",
    },
    "dept_manager": {
        "organization.read", "department.read", "department.manage",
        "member.invite", "member.read", "role.read", "users.read",
        "dataset.create", "dataset.read", "dataset.update", "dataset.delete", "dataset.share", "dataset.export",
        "dashboard.create", "dashboard.read", "dashboard.update", "dashboard.export",
        "report.generate", "report.read", "report.export",
        "pipelines.create", "pipelines.execute", "pipelines.view",
        "etl.import", "etl.export", "analytics.view", "analytics.manage", "ai.use", "audit.view",
        "profile.update", "ml.read", "ml.execute",
        "capture.upload", "capture.process", "capture.read", "workspace.create", "workspace.manage",
    },
    "analyst": {
        "organization.read", "department.read", "member.read", "role.read", "users.read",
        "dataset.read", "dataset.update", "dataset.export", "dataset.share",
        "dashboard.create", "dashboard.read", "dashboard.update", "dashboard.export", "dashboard.share",
        "report.generate", "report.read", "report.update", "report.export",
        "pipelines.view", "etl.export", "analytics.view", "analytics.manage", "analytics.export", "ai.use",
        "profile.update", "ml.read", "ml.write", "ml.execute", "capture.read",
        "workspace.create", "workspace.manage",
    },
    "researcher": {
        "organization.read", "department.read", "member.read",
        "dataset.create", "dataset.read", "dataset.update", "dataset.export",
        "dashboard.create", "dashboard.read", "dashboard.export",
        "report.generate", "report.read", "report.export",
        "pipelines.view", "etl.import", "etl.export", "analytics.view", "analytics.export", "ai.use",
        "profile.update", "ml.read", "ml.execute",
        "capture.upload", "capture.read", "workspace.create",
    },
    "data_entry_officer": {
        "organization.read", "department.read",
        "dataset.create", "dataset.read", "dataset.update",
        "dashboard.read", "report.read", "etl.import",
        "profile.update", "capture.upload", "capture.process", "capture.read",
    },
    "viewer": {
        "organization.read", "member.read", "dataset.read",
        "dashboard.read", "report.read", "analytics.view", "profile.update",
    },
    "personal_user": {
        "dataset.create", "dataset.read", "dataset.update", "dataset.delete", "dataset.export",
        "dashboard.create", "dashboard.read", "dashboard.update", "dashboard.export",
        "report.generate", "report.read", "report.export",
        "analytics.view", "ai.use", "profile.update",
        "ml.read", "ml.execute", "capture.upload", "capture.read",
        "workspace.create", "workspace.manage",
    },
}


class RoleHierarchy:
    """Role hierarchy utilities."""

    @staticmethod
    def get_level(role_name: str) -> int:
        return ROLE_HIERARCHY.get(role_name, 0)

    @staticmethod
    def get_highest_role(roles: list[str]) -> str | None:
        if not roles:
            return None
        return max(roles, key=lambda r: ROLE_HIERARCHY.get(r, 0))

    @staticmethod
    def is_at_least(role_name: str, min_level: RoleLevel) -> bool:
        return ROLE_HIERARCHY.get(role_name, 0) >= min_level

    @staticmethod
    def can_manage(manager_role: str, target_role: str) -> bool:
        manager_level = ROLE_HIERARCHY.get(manager_role, 0)
        target_level = ROLE_HIERARCHY.get(target_role, 0)
        return manager_level > target_level

    @staticmethod
    def get_display_name(role_name: str) -> str:
        display_names = {
            "super_admin": "Super Administrator",
            "platform_owner": "Platform Owner",
            "platform_admin": "Platform Administrator",
            "org_admin": "Organization Administrator",
            "dept_manager": "Department Manager",
            "analyst": "Analyst",
            "researcher": "Researcher",
            "data_entry_officer": "Data Entry Officer",
            "viewer": "Viewer",
            "personal_user": "Personal Workspace User",
        }
        return display_names.get(role_name, role_name.replace("_", " ").title())

    @staticmethod
    def all_roles() -> list[dict]:
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
        return PERMISSION_MATRIX.get(role_name, set())

    @staticmethod
    def has_permission(role_name: str, permission: str) -> bool:
        perms = PermissionMatrix.get_permissions(role_name)
        return "*" in perms or permission in perms

    @staticmethod
    def user_has_permission(roles: list[str], permission: str) -> bool:
        for role in roles:
            if PermissionMatrix.has_permission(role, permission):
                return True
        return False

    @staticmethod
    def get_role_permissions_summary() -> dict[str, list[str]]:
        return {
            role: sorted(perms) if perms != {"*"} else ["* (all permissions)"]
            for role, perms in PERMISSION_MATRIX.items()
        }


def get_role_level(role_name: str) -> int:
    return RoleHierarchy.get_level(role_name)


def has_role_or_higher(roles: list[str], min_role: str) -> bool:
    min_level = ROLE_HIERARCHY.get(min_role, 0)
    for role in roles:
        if ROLE_HIERARCHY.get(role, 0) >= min_level:
            return True
    return False
