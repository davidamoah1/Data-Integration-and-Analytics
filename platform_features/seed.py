"""Enterprise Seed Data.

Seeds:
  - Organizations: Hospital A, School B, Company C
  - Enterprise roles: analyst, manager (mapped to existing roles)
  - Demo users for each organization with appropriate roles

Called during database initialization or via the /platform/seed endpoint.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession


def seed_enterprise_data(db: DbSession) -> dict:
    """Seed enterprise organizations, roles, and demo users.

    Returns:
        Summary of what was created.
    """
    from authentication.models import Permission, Role, User
    from authentication.repositories import (
        PermissionRepository,
        RolePermissionRepository,
        RoleRepository,
        UserRepository,
        UserRoleRepository,
    )
    from organizations.models import Organization
    from shared.security import hash_password

    created = {"organizations": [], "roles": [], "users": []}

    # 1. Seed organizations
    orgs_def = [
        ("Hospital A", "hospital-a", "healthcare", "A regional hospital system"),
        ("School B", "school-b", "education", "An educational institution"),
        ("Company C", "company-c", "retail", "A retail business company"),
    ]

    for name, slug, industry, description in orgs_def:
        existing = db.execute(
            select(Organization).where(Organization.slug == slug)
        ).scalar_one_or_none()
        if not existing:
            org = Organization(
                name=name,
                slug=slug,
                description=description,
                is_active=1,
            )
            # Store industry in branding JSON
            org.branding = {"industry": industry}
            db.add(org)
            db.flush()
            created["organizations"].append({"id": org.id, "name": name, "slug": slug})

    # 2. Add "analyst" and "manager" roles if they don't exist
    role_repo = RoleRepository(db)
    role_perm_repo = RolePermissionRepository(db)
    perm_repo = PermissionRepository(db)

    # Ensure permissions exist
    new_perms = [
        ("ai.use", "Use AI Features", "ai", "Access AI predictions and insights"),
        ("predictive.view", "View Predictions", "predictive", "View predictive analytics"),
        ("quality.view", "View Quality", "quality", "View data quality intelligence"),
    ]
    for name, display, module, desc in new_perms:
        if not perm_repo.get_by_name(name):
            perm_repo.create(
                Permission(name=name, display_name=display, module=module, description=desc)
            )

    roles_def = [
        (
            "analyst",
            "Analyst",
            "Analyze data, create reports, and use AI features",
            False,
            [
                "dashboard.view",
                "reports.generate",
                "reports.export",
                "reports.view",
                "datasets.view",
                "analytics.view",
                "analytics.export",
                "ai.use",
                "predictive.view",
                "quality.view",
                "etl.export",
                "profile.update",
            ],
        ),
        (
            "manager",
            "Manager",
            "Manage department operations and view analytics",
            False,
            [
                "users.read",
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
                "analytics.export",
                "ai.use",
                "predictive.view",
                "quality.view",
                "departments.manage",
                "profile.update",
            ],
        ),
    ]

    for name, display, desc, is_system, perm_names in roles_def:
        role = role_repo.get_by_name(name)
        if not role:
            role = Role(name=name, display_name=display, description=desc, is_system=is_system)
            role_repo.create(role)
            created["roles"].append({"name": name, "display_name": display})
        perm_ids = role_perm_repo.get_permission_ids_by_names(perm_names)
        role_perm_repo.set_role_permissions(role.id, perm_ids)

    # 3. Create demo users for each organization
    user_repo = UserRepository(db)
    user_role_repo = UserRoleRepository(db)

    import os as _os

    demo_password = _os.getenv("DEMO_USER_PASSWORD", "")
    if demo_password:
        demo_password_hash = hash_password(demo_password)

        demo_users = [
            # Hospital A users
            ("admin@hospitala.io", "Hospital A Admin", "hospital-a", "org_admin"),
            ("analyst@hospitala.io", "Hospital A Analyst", "hospital-a", "analyst"),
            ("manager@hospitala.io", "Hospital A Manager", "hospital-a", "manager"),
            ("viewer@hospitala.io", "Hospital A Viewer", "hospital-a", "viewer"),
            # School B users
            ("admin@schoolb.io", "School B Admin", "school-b", "org_admin"),
            ("analyst@schoolb.io", "School B Analyst", "school-b", "analyst"),
            ("manager@schoolb.io", "School B Manager", "school-b", "manager"),
            ("viewer@schoolb.io", "School B Viewer", "school-b", "viewer"),
            # Company C users
            ("admin@companyc.io", "Company C Admin", "company-c", "org_admin"),
            ("analyst@companyc.io", "Company C Analyst", "company-c", "analyst"),
            ("manager@companyc.io", "Company C Manager", "company-c", "manager"),
            ("viewer@companyc.io", "Company C Viewer", "company-c", "viewer"),
        ]

        for email, full_name, org_slug, role_name in demo_users:
            if user_repo.get_by_email(email):
                continue

            org = db.execute(
                select(Organization).where(Organization.slug == org_slug)
            ).scalar_one_or_none()
            org_id = org.id if org else None

            user = User(
                email=email,
                password_hash=demo_password_hash,
                full_name=full_name,
                organization_id=org_id,
                is_active=1,
                email_verified_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
            )
            user_repo.create(user)

            role = role_repo.get_by_name(role_name)
            if role:
                user_role_repo.assign_role(user.id, role.id)

            created["users"].append(
                {"email": email, "name": full_name, "role": role_name, "org": org_slug}
            )

    db.commit()

    return {
        "organizations_created": created["organizations"],
        "roles_created": created["roles"],
        "users_created": created["users"],
        "summary": (
            f"Seeded {len(created['organizations'])} organizations, "
            f"{len(created['roles'])} roles, "
            f"{len(created['users'])} demo users."
        ),
    }
