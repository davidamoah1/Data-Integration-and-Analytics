"""Demo data seeding for pilot readiness.

Creates a demo organization, demo users (admin, analyst, manager, data engineer, viewer),
sample dashboards, KPIs, ETL pipelines, AI conversations, and AI reports.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session as DbSession

from analytics.models import KPI, Dashboard
from etl.models import ETLPipeline


def seed_demo_data(db: DbSession) -> dict:
    """Seed demo organization, users, and sample data.

    Returns a summary of what was created.
    """
    created: dict[str, list] = {
        "organizations": [],
        "users": [],
        "dashboards": [],
        "kpis": [],
        "pipelines": [],
        "ai_conversations": [],
        "ai_reports": [],
    }

    # 1. Demo organization
    from organizations.models import Organization

    existing_org = db.query(Organization).filter(Organization.name == "Demo Corporation").first()
    if not existing_org:
        org = Organization(
            name="Demo Corporation",
            slug="demo-corporation",
            description="Pilot demonstration organization — explore all platform features with sample data.",
            contact_email="info@democorp.com",
            timezone="UTC",
            is_active=1,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        created["organizations"].append(org.name)
        org_id = org.id
    else:
        org_id = existing_org.id

    # 2. Demo users — all pilot roles
    from authentication.models import User
    from authentication.repositories import RoleRepository, UserRoleRepository
    from shared.security import hash_password

    demo_users = [
        ("demo.admin@democorp.com", "DemoAdmin1!", "Demo Admin", "admin", "System Administrator"),
        ("demo.analyst@democorp.com", "DemoAnalyst1!", "Demo Analyst", "analyst", "Data Analyst"),
        (
            "demo.manager@democorp.com",
            "DemoManager1!",
            "Demo Manager",
            "viewer",
            "Operations Manager",
        ),
        (
            "demo.engineer@democorp.com",
            "DemoEngineer1!",
            "Demo Engineer",
            "analyst",
            "Data Engineer",
        ),
        ("demo.viewer@democorp.com", "DemoViewer1!", "Demo Viewer", "viewer", "Executive Viewer"),
    ]
    role_repo = RoleRepository(db)
    user_role_repo = UserRoleRepository(db)
    user_id_map = {}
    for email, password, full_name, role_name, position in demo_users:
        existing_user = db.query(User).filter(User.email == email).first()
        if not existing_user:
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                organization_id=org_id,
                position=position,
                email_verified_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(user)
            db.flush()
            role = role_repo.get_by_name(role_name)
            if role:
                user_role_repo.set_user_roles(user.id, [role.id])
            created["users"].append(email)
            user_id_map[email] = user.id
        else:
            user_id_map[email] = existing_user.id
    db.commit()

    admin_id = user_id_map.get("demo.admin@democorp.com", 1)

    # 3. Demo dashboards — one per sector
    demo_dashboards = [
        (
            "Sales Performance Demo",
            "KPIs and trends for sales, profit, and regional performance",
            "default",
        ),
        (
            "Healthcare Billing Demo",
            "Patient billing, insurance coverage, and department efficiency",
            "healthcare",
        ),
        (
            "Education Enrollment Demo",
            "Tuition collection, program enrollment, and department analytics",
            "education",
        ),
        (
            "Government Spending Demo",
            "Project spending, contractor performance, and budget allocation",
            "government",
        ),
        (
            "Church Offerings Demo",
            "Offering trends, member giving patterns, and ministry performance",
            "church",
        ),
        (
            "NGO Donations Demo",
            "Donation growth, program impact, and funding source diversity",
            "ngo",
        ),
    ]
    for name, desc, theme in demo_dashboards:
        existing_dash = db.query(Dashboard).filter(Dashboard.name == name).first()
        if not existing_dash:
            dashboard = Dashboard(
                owner_id=admin_id,
                organization_id=org_id,
                name=name,
                description=desc,
                theme=theme,
                layout=[
                    {
                        "type": "kpi_card",
                        "title": "Total Revenue",
                        "position": {"col": 1, "row": 1},
                    },
                    {"type": "kpi_card", "title": "Total Profit", "position": {"col": 2, "row": 1}},
                    {
                        "type": "line_chart",
                        "title": "Revenue Trend",
                        "position": {"col": 1, "row": 2},
                    },
                    {
                        "type": "bar_chart",
                        "title": "Top Products",
                        "position": {"col": 2, "row": 2},
                    },
                ],
                is_public=True,
            )
            db.add(dashboard)
            db.commit()
            created["dashboards"].append(dashboard.name)

    # 4. Demo KPIs — broader set
    demo_kpis = [
        ("Monthly Revenue", "SUM(sales)", "Sales", 100000.0, "USD"),
        ("Profit Margin", "SUM(profit) / SUM(sales) * 100", "Profitability", 25.0, "%"),
        ("Order Count", "COUNT(DISTINCT order_id)", "Sales", 500.0, "orders"),
        ("Avg Order Value", "AVG(sales)", "Sales", 250.0, "USD"),
        ("Customer Count", "COUNT(DISTINCT customer_name)", "Customers", 800.0, "customers"),
        ("Data Quality Score", "valid_records / total_records * 100", "Data Quality", 95.0, "%"),
    ]
    for name, formula, category, target, unit in demo_kpis:
        existing = db.query(KPI).filter(KPI.name == name).first()
        if not existing:
            kpi = KPI(
                owner_id=admin_id,
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

    # 5. Demo ETL pipelines — multiple
    demo_pipelines = [
        (
            "Demo Sales Import",
            "ETL pipeline for importing and cleaning sales data from CSV",
            "active",
        ),
        (
            "Demo Healthcare Billing",
            "ETL pipeline for healthcare billing data with insurance mapping",
            "active",
        ),
        (
            "Demo Education Enrollment",
            "ETL pipeline for student enrollment and tuition data",
            "active",
        ),
        (
            "Demo Data Quality Check",
            "Automated data quality validation and anomaly detection",
            "active",
        ),
    ]
    for name, desc, status in demo_pipelines:
        existing_pipe = db.query(ETLPipeline).filter(ETLPipeline.name == name).first()
        if not existing_pipe:
            pipeline = ETLPipeline(
                name=name,
                description=desc,
                status=status,
            )
            db.add(pipeline)
            db.commit()
            created["pipelines"].append(pipeline.name)

    # 6. Demo AI conversations
    from ai.models import AIConversation, AIMessage

    demo_conversations = [
        (
            "Sales Performance Analysis",
            "data_copilot",
            admin_id,
            [
                ("user", "What are the top selling product categories?"),
                (
                    "assistant",
                    "Based on the sales data, the top 3 product categories by revenue are:\n1. **Technology** — $827,955 (36.3% of total)\n2. **Furniture** — $742,312 (32.5%)\n3. **Office Supplies** — $718,617 (31.2%)\n\nTechnology leads primarily due to strong phone and copier sales in the Consumer segment.",
                ),
                ("user", "Which region has the highest profit margin?"),
                (
                    "assistant",
                    "The **West** region has the highest profit margin at 24.5%, followed by the East region at 22.1%. The Central region has the lowest margin at 18.3%, largely due to higher discount rates in that territory.",
                ),
            ],
        ),
        (
            "Data Quality Report",
            "etl_copilot",
            admin_id,
            [
                ("user", "Check the data quality of the latest upload"),
                (
                    "assistant",
                    "Data quality analysis complete:\n\n- **Total records**: 856\n- **Duplicates removed**: 55 (6.4%)\n- **Missing values filled**: 23 records\n- **Date format inconsistencies**: 127 records normalized\n- **Currency strings parsed**: 18 records (e.g., '$2,068.74' → 2068.74)\n- **Negative values corrected**: 8 records\n\n**Overall quality score**: 91.2%\n\nRecommendation: Enable automatic deduplication on import to prevent future duplicate entries.",
                ),
            ],
        ),
    ]
    for title, assistant_type, user_id, messages in demo_conversations:
        existing_conv = (
            db.query(AIConversation)
            .filter(AIConversation.title == title, AIConversation.user_id == user_id)
            .first()
        )
        if not existing_conv:
            conv = AIConversation(
                user_id=user_id,
                assistant_type=assistant_type,
                title=title,
                context={"organization_id": org_id},
                is_active=True,
            )
            db.add(conv)
            db.flush()
            for role, content in messages:
                msg = AIMessage(
                    conversation_id=conv.id,
                    role=role,
                    content=content,
                    tokens_used=len(content) // 4,
                    model_used="gpt-4o-mini",
                    provider="openai",
                )
                db.add(msg)
            created["ai_conversations"].append(title)
    db.commit()

    # 7. Demo AI reports
    from ai.models import AIReportGeneration

    demo_reports = [
        (
            "Executive Summary Report",
            "executive",
            "## Executive Summary\n\n**Q4 2024 Performance Overview**\n\nTotal revenue reached $2.3M, a 15.2% increase year-over-year. Profit margins improved to 22.8%, driven by operational efficiencies and reduced discount rates in the West region.\n\n### Key Highlights\n- Revenue: $2,297,200 (↑15.2% YoY)\n- Profit: $523,456 (↑18.7% YoY)\n- Orders: 5,004 (↑8.3% YoY)\n- Avg Order Value: $459 (↑6.4%)\n\n### Regional Performance\nThe West region continues to be the strongest performer, contributing 38% of total revenue with the highest profit margin at 24.5%.",
            "Monthly revenue, profit, and order trends for Q4 2024",
        ),
        (
            "Monthly Operations Report",
            "monthly",
            "## Monthly Operations Report — December 2024\n\n### Data Pipeline Status\n- All 4 ETL pipelines completed successfully\n- Data freshness: 2.1 hours (target: <24h)\n- Data quality score: 94.7%\n\n### User Activity\n- 142 active users\n- 1,847 dashboard views\n- 326 AI Copilot queries\n- 89 reports generated\n\n### System Health\n- API uptime: 99.97%\n- Avg response time: 142ms\n- No critical incidents",
            "Platform usage metrics and system health for December 2024",
        ),
    ]
    for title, report_type, content, summary in demo_reports:
        existing_report = (
            db.query(AIReportGeneration)
            .filter(AIReportGeneration.title == title, AIReportGeneration.user_id == admin_id)
            .first()
        )
        if not existing_report:
            report = AIReportGeneration(
                report_type=report_type,
                title=title,
                content=content,
                summary=summary,
                user_id=admin_id,
                sections=["Summary", "Key Metrics", "Regional Performance", "Recommendations"],
                format="markdown",
            )
            db.add(report)
            created["ai_reports"].append(title)
    db.commit()

    return created


def is_demo_seeded(db: DbSession) -> bool:
    """Check if demo data has already been seeded."""
    from organizations.models import Organization

    return (
        db.query(Organization).filter(Organization.name == "Demo Corporation").first() is not None
    )
