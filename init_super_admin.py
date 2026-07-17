#!/usr/bin/env python3
"""Initialize database with super admin user."""

import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


# Import all models to ensure they're registered
from authentication.models import Permission, Role, User
from authentication.repositories import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from shared.database import Base as SharedBase
from shared.database import Session as DbSession
from shared.database import get_engine
from shared.security import hash_password


def init_database():
    """Initialize database tables and seed super admin."""
    print("Initializing database...")

    # Create shared database engine
    engine = get_engine()

    # Create all tables
    SharedBase.metadata.create_all(engine)
    print("Database tables created successfully.")

    # Seed default data
    db = DbSession(engine)
    try:
        seed_default_data(db)
        print("Super admin user created successfully!")
        print("\nLogin credentials:")
        print("Email: admin@dataflow.io")
        print("Password: Admin@12345")
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_default_data(db: DbSession):
    """Seed default roles, permissions, and super admin user."""

    perm_repo = PermissionRepository(db)
    role_repo = RoleRepository(db)
    role_perm_repo = RolePermissionRepository(db)
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)

    # Define all permissions
    permissions_def = [
        # User management
        ("users.create", "Create Users", "users", "Create new user accounts"),
        ("users.read", "View Users", "users", "View user profiles"),
        ("users.edit", "Edit Users", "users", "Edit user information"),
        ("users.delete", "Delete Users", "users", "Delete user accounts"),
        ("users.manage", "Manage Users", "users", "Full user management"),
        # Role management
        ("roles.create", "Create Roles", "roles", "Create new roles"),
        ("roles.read", "View Roles", "roles", "View roles and permissions"),
        ("roles.manage", "Manage Roles", "roles", "Full role management"),
        # Pipeline
        ("pipelines.create", "Create Pipelines", "pipelines", "Create ETL pipelines"),
        ("pipelines.execute", "Execute Pipelines", "pipelines", "Run ETL pipelines"),
        ("pipelines.view", "View Pipelines", "pipelines", "View pipeline status"),
        # ETL
        ("etl.import", "Import Data", "etl", "Import data via ETL"),
        ("etl.export", "Export Data", "etl", "Export data from ETL"),
        # Dashboard
        ("dashboard.view", "View Dashboard", "dashboard", "View dashboards"),
        ("dashboard.manage", "Manage Dashboard", "dashboard", "Create and edit dashboards"),
        # Reports
        ("reports.generate", "Generate Reports", "reports", "Generate reports"),
        ("reports.export", "Export Reports", "reports", "Export report files"),
        ("reports.view", "View Reports", "reports", "View reports"),
        # Datasets
        ("datasets.upload", "Upload Datasets", "datasets", "Upload new datasets"),
        ("datasets.delete", "Delete Datasets", "datasets", "Delete datasets"),
        ("datasets.view", "View Datasets", "datasets", "View datasets"),
        # Analytics
        ("analytics.view", "View Analytics", "analytics", "View analytics"),
        # AI
        ("ai.use", "Use AI Features", "ai", "Access AI predictions and insights"),
        # Settings
        ("settings.manage", "Manage Settings", "settings", "Manage system settings"),
        # Audit
        ("audit.view", "View Audit Logs", "audit", "View audit logs"),
        # Notifications
        (
            "notifications.manage",
            "Manage Notifications",
            "notifications",
            "Manage notification settings",
        ),
        # Organization
        ("organizations.manage", "Manage Organizations", "organizations", "Manage organizations"),
        ("departments.manage", "Manage Departments", "departments", "Manage departments"),
        # Sessions
        ("sessions.manage", "Manage Sessions", "sessions", "Revoke user sessions"),
        # Profile
        ("profile.update", "Update Profile", "profile", "Update own profile"),
    ]

    print("Creating permissions...")
    for name, display, module, desc in permissions_def:
        if not perm_repo.get_by_name(name):
            perm_repo.create(
                Permission(
                    name=name,
                    display_name=display,
                    module=module,
                    description=desc,
                )
            )

    # Define roles and their permissions
    roles_def = [
        (
            "super_admin",
            "Super Administrator",
            "Full system access with all permissions",
            True,
            [p[0] for p in permissions_def],
        ),
        (
            "org_owner",
            "Organization Owner",
            "Owner of an organization with full org access",
            True,
            [p[0] for p in permissions_def if not p[0].startswith("settings.manage")],
        ),
        (
            "org_admin",
            "Organization Administrator",
            "Manage users and data within organization",
            True,
            [
                "users.create",
                "users.read",
                "users.edit",
                "users.delete",
                "users.manage",
                "roles.read",
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "dashboard.view",
                "dashboard.manage",
                "reports.generate",
                "reports.export",
                "reports.view",
                "datasets.upload",
                "datasets.view",
                "analytics.view",
                "notifications.manage",
                "departments.manage",
                "sessions.manage",
                "profile.update",
                "audit.view",
            ],
        ),
        (
            "dept_manager",
            "Department Manager",
            "Manage department operations",
            True,
            [
                "users.read",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "dashboard.view",
                "reports.view",
                "reports.generate",
                "reports.export",
                "datasets.view",
                "analytics.view",
                "profile.update",
            ],
        ),
        (
            "data_engineer",
            "Data Engineer",
            "Build and run ETL pipelines",
            True,
            [
                "pipelines.create",
                "pipelines.execute",
                "pipelines.view",
                "etl.import",
                "etl.export",
                "datasets.upload",
                "datasets.view",
                "dashboard.view",
                "profile.update",
            ],
        ),
        (
            "data_analyst",
            "Data Analyst",
            "Analyze data and create reports",
            True,
            [
                "dashboard.view",
                "reports.generate",
                "reports.view",
                "datasets.view",
                "analytics.view",
                "etl.export",
                "profile.update",
            ],
        ),
        (
            "business_analyst",
            "Business Analyst",
            "View dashboards and reports",
            True,
            ["dashboard.view", "reports.view", "datasets.view", "analytics.view", "profile.update"],
        ),
        (
            "executive",
            "Executive",
            "View high-level analytics and reports",
            True,
            ["dashboard.view", "reports.view", "analytics.view", "profile.update"],
        ),
        (
            "dept_officer",
            "Department Officer",
            "Department-level operations",
            True,
            ["dashboard.view", "reports.view", "datasets.view", "profile.update"],
        ),
        (
            "auditor",
            "Auditor",
            "View audit logs and security events",
            True,
            ["audit.view", "users.read", "profile.update"],
        ),
        (
            "viewer",
            "Viewer",
            "Read-only access to dashboards",
            True,
            ["dashboard.view", "profile.update"],
        ),
    ]

    print("Creating roles...")
    for name, display, desc, is_system, perm_names in roles_def:
        role = role_repo.get_by_name(name)
        if not role:
            role = Role(name=name, display_name=display, description=desc, is_system=is_system)
            role_repo.create(role)
        perm_ids = role_perm_repo.get_permission_ids_by_names(perm_names)
        role_perm_repo.set_role_permissions(role.id, perm_ids)

    # Create default super admin user
    admin_email = "admin@dataflow.io"
    print(f"Creating super admin user: {admin_email}")

    if not user_repo.get_by_email(admin_email):
        admin = User(
            email=admin_email,
            password_hash=hash_password("Admin@12345"),
            full_name="System Administrator",
            is_active=1,
            email_verified_at=datetime.now(timezone.utc),
        )
        user_repo.create(admin)

        super_admin_role = role_repo.get_by_name("super_admin")
        if super_admin_role:
            user_role_repo.assign_role(admin.id, super_admin_role.id)
            print("Super admin role assigned successfully!")
        else:
            print("Warning: Super admin role not found!")
    else:
        print("Super admin user already exists!")

    db.commit()
    print("Database initialization completed successfully!")


if __name__ == "__main__":
    init_database()
