"""Demo data seeding for pilot readiness.

Creates a demo organization, demo users, sample sales data,
sample ETL pipeline, sample dashboards, and sample KPIs.
"""

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from analytics.models import Dashboard, KPI
from etl.models import ETLPipeline


def seed_demo_data(db: DbSession) -> dict:
    """Seed demo organization, users, and sample data.

    Returns a summary of what was created.
    """
    created: dict[str, list] = {"organizations": [], "users": [], "dashboards": [], "kpis": [], "pipelines": []}

    # 1. Demo organization (skip if exists)
    from organizations.models import Organization

    existing_org = db.query(Organization).filter(Organization.name == "Demo Corporation").first()
    if not existing_org:
        org = Organization(
            name="Demo Corporation",
            slug="demo-corporation",
            description="Sample organization for pilot demonstration",
            is_active=1,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        created["organizations"].append(org.name)
        org_id = org.id
    else:
        org_id = existing_org.id

    # 1b. Demo users
    from authentication.models import User
    from authentication.repositories import RoleRepository, UserRoleRepository
    from shared.security import hash_password

    demo_users = [
        ("demo.admin@democorp.com", "DemoAdmin1!", "Demo Admin", "admin"),
        ("demo.analyst@democorp.com", "DemoAnalyst1!", "Demo Analyst", "analyst"),
        ("demo.viewer@democorp.com", "DemoViewer1!", "Demo Viewer", "viewer"),
    ]
    role_repo = RoleRepository(db)
    user_role_repo = UserRoleRepository(db)
    for email, password, full_name, role_name in demo_users:
        existing_user = db.query(User).filter(User.email == email).first()
        if not existing_user:
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                organization_id=org_id,
            )
            db.add(user)
            db.flush()
            role = role_repo.get_by_name(role_name)
            if role:
                user_role_repo.set_user_roles(user.id, [role.id])
            created["users"].append(email)
    db.commit()

    # 2. Demo dashboard
    existing_dash = db.query(Dashboard).filter(Dashboard.name == "Sales Performance Demo").first()
    if not existing_dash:
        dashboard = Dashboard(
            owner_id=1,
            organization_id=org_id,
            name="Sales Performance Demo",
            description="Sample dashboard showing sales KPIs and trends",
            theme="default",
            layout=[
                {"type": "kpi_card", "title": "Total Revenue", "position": {"col": 1, "row": 1}},
                {"type": "kpi_card", "title": "Total Profit", "position": {"col": 2, "row": 1}},
                {"type": "line_chart", "title": "Revenue Trend", "position": {"col": 1, "row": 2}},
                {"type": "bar_chart", "title": "Top Products", "position": {"col": 2, "row": 2}},
            ],
            is_public=True,
        )
        db.add(dashboard)
        db.commit()
        created["dashboards"].append(dashboard.name)

    # 3. Demo KPIs
    demo_kpis = [
        ("Monthly Revenue", "SUM(sales)", "Sales", 100000.0, "USD"),
        ("Profit Margin", "SUM(profit) / SUM(sales) * 100", "Profitability", 25.0, "%"),
        ("Order Count", "COUNT(DISTINCT order_id)", "Sales", 500.0, "orders"),
    ]
    for name, formula, category, target, unit in demo_kpis:
        existing = db.query(KPI).filter(KPI.name == name).first()
        if not existing:
            kpi = KPI(
                owner_id=1,
                organization_id=org_id,
                name=name,
                formula=formula,
                category=category,
                target_value=target,
                unit=unit,
            )
            db.add(kpi)
            created["kpis"].append(name)
    db.commit()

    # 4. Demo ETL pipeline
    existing_pipe = db.query(ETLPipeline).filter(ETLPipeline.name == "Demo Sales Import").first()
    if not existing_pipe:
        pipeline = ETLPipeline(
            name="Demo Sales Import",
            description="Sample ETL pipeline for importing sales data from CSV",
            status="active",
        )
        db.add(pipeline)
        db.commit()
        created["pipelines"].append(pipeline.name)

    return created


def is_demo_seeded(db: DbSession) -> bool:
    """Check if demo data has already been seeded."""
    from organizations.models import Organization

    return db.query(Organization).filter(Organization.name == "Demo Corporation").first() is not None
