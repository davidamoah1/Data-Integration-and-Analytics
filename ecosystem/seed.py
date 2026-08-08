"""Seed industry solution packages into the marketplace.

Creates pre-built packages for:
  - Healthcare
  - Education
  - Banking
  - Agriculture
  - Retail
  - Government
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session as DbSession

from ecosystem.plugin_models import IndustryPackage, Plugin

logger = logging.getLogger("etl_project.ecosystem")


INDUSTRY_PACKAGES = [
    {
        "package_id": "healthcare-analytics",
        "industry": "healthcare",
        "name": "Healthcare Analytics Package",
        "description": "Complete analytics for hospitals and clinics: patient flow, billing, admissions, insurance, and outcomes.",
        "version": "1.0.0",
        "is_africa_optimized": True,
        "dataset_templates": [
            {
                "name": "Patient Records",
                "columns": [
                    "patient_id",
                    "name",
                    "age",
                    "gender",
                    "diagnosis",
                    "admission_date",
                    "discharge_date",
                ],
            },
            {
                "name": "Billing Records",
                "columns": [
                    "bill_id",
                    "patient_id",
                    "amount",
                    "insurance_provider",
                    "status",
                    "date",
                ],
            },
            {
                "name": "Staff Records",
                "columns": ["staff_id", "name", "role", "department", "shift"],
            },
        ],
        "dashboard_templates": [
            {
                "name": "Hospital Executive Dashboard",
                "description": "Overview of hospital KPIs",
                "layout": {"grid": "2x3"},
            },
            {
                "name": "Patient Flow Dashboard",
                "description": "Admissions, discharges, and ward occupancy",
                "layout": {"grid": "2x2"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Admissions",
                "category": "operational",
                "formula": "count(admission_date)",
                "unit": "patients",
            },
            {
                "name": "Avg Billing per Patient",
                "category": "financial",
                "formula": "avg(billing_amount)",
                "unit": "USD",
            },
            {
                "name": "Bed Occupancy Rate",
                "category": "operational",
                "formula": "occupied_beds / total_beds * 100",
                "unit": "%",
            },
            {
                "name": "Patient Satisfaction",
                "category": "quality",
                "formula": "avg(satisfaction_score)",
                "unit": "/5",
            },
            {
                "name": "Insurance Claim Rate",
                "category": "financial",
                "formula": "approved_claims / total_claims * 100",
                "unit": "%",
            },
        ],
        "ai_insight_templates": [
            {
                "type": "patient_flow_analysis",
                "prompt": "Analyze patient admission patterns and predict peak periods",
            },
            {
                "type": "billing_anomaly",
                "prompt": "Detect unusual billing patterns and potential fraud",
            },
        ],
        "ml_model_templates": [
            {
                "type": "patient_readmission",
                "algorithm": "random_forest",
                "target": "readmission_30d",
            },
            {"type": "length_of_stay", "algorithm": "linear_regression", "target": "los_days"},
        ],
    },
    {
        "package_id": "education-intelligence",
        "industry": "education",
        "name": "Education Intelligence Package",
        "description": "Analytics for schools and universities: enrollment, performance, attendance, and fees.",
        "version": "1.0.0",
        "is_africa_optimized": True,
        "dataset_templates": [
            {
                "name": "Student Records",
                "columns": ["student_id", "name", "grade", "class", "enrollment_date", "gpa"],
            },
            {"name": "Attendance Records", "columns": ["student_id", "date", "status", "class_id"]},
            {
                "name": "Fees Records",
                "columns": ["student_id", "amount_due", "amount_paid", "status", "due_date"],
            },
        ],
        "dashboard_templates": [
            {
                "name": "School Executive Dashboard",
                "description": "Enrollment, performance, and financial overview",
                "layout": {"grid": "2x3"},
            },
            {
                "name": "Student Performance Dashboard",
                "description": "Grades, attendance, and at-risk students",
                "layout": {"grid": "2x2"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Enrollment",
                "category": "operational",
                "formula": "count(student_id)",
                "unit": "students",
            },
            {"name": "Avg GPA", "category": "academic", "formula": "avg(gpa)", "unit": "/4.0"},
            {
                "name": "Attendance Rate",
                "category": "operational",
                "formula": "present_days / total_days * 100",
                "unit": "%",
            },
            {
                "name": "Fee Collection Rate",
                "category": "financial",
                "formula": "amount_paid / amount_due * 100",
                "unit": "%",
            },
            {
                "name": "Dropout Rate",
                "category": "academic",
                "formula": "dropouts / total_students * 100",
                "unit": "%",
            },
        ],
        "ai_insight_templates": [
            {
                "type": "at_risk_students",
                "prompt": "Identify students at risk of dropping out based on attendance and grades",
            },
            {
                "type": "performance_trends",
                "prompt": "Analyze grade trends across classes and subjects",
            },
        ],
        "ml_model_templates": [
            {
                "type": "student_performance",
                "algorithm": "gradient_boosting",
                "target": "final_grade",
            },
            {"type": "dropout_prediction", "algorithm": "logistic_regression", "target": "dropout"},
        ],
    },
    {
        "package_id": "banking-analytics",
        "industry": "banking",
        "name": "Banking Analytics Package",
        "description": "Transaction analytics, risk analysis, and fraud detection for banks and financial institutions.",
        "version": "1.0.0",
        "is_africa_optimized": True,
        "dataset_templates": [
            {
                "name": "Transaction Records",
                "columns": [
                    "transaction_id",
                    "account_id",
                    "amount",
                    "type",
                    "timestamp",
                    "channel",
                ],
            },
            {
                "name": "Account Records",
                "columns": ["account_id", "customer_id", "type", "balance", "opened_date"],
            },
            {
                "name": "Loan Records",
                "columns": [
                    "loan_id",
                    "customer_id",
                    "amount",
                    "interest_rate",
                    "status",
                    "term_months",
                ],
            },
        ],
        "dashboard_templates": [
            {
                "name": "Bank Executive Dashboard",
                "description": "Total deposits, loans, and transaction volume",
                "layout": {"grid": "2x3"},
            },
            {
                "name": "Risk & Fraud Dashboard",
                "description": "Fraud alerts, risk scores, and suspicious transactions",
                "layout": {"grid": "2x2"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Transaction Volume",
                "category": "operational",
                "formula": "sum(amount)",
                "unit": "USD",
            },
            {
                "name": "Avg Transaction Value",
                "category": "financial",
                "formula": "avg(amount)",
                "unit": "USD",
            },
            {
                "name": "Loan Default Rate",
                "category": "risk",
                "formula": "defaults / total_loans * 100",
                "unit": "%",
            },
            {
                "name": "Fraud Detection Rate",
                "category": "risk",
                "formula": "fraud_detected / total_transactions * 100",
                "unit": "%",
            },
            {
                "name": "Customer Acquisition",
                "category": "growth",
                "formula": "count(new_customers)",
                "unit": "customers",
            },
        ],
        "ai_insight_templates": [
            {
                "type": "fraud_detection",
                "prompt": "Detect anomalous transaction patterns indicating potential fraud",
            },
            {
                "type": "credit_scoring",
                "prompt": "Assess credit risk for loan applicants based on transaction history",
            },
        ],
        "ml_model_templates": [
            {"type": "fraud_detection", "algorithm": "isolation_forest", "target": "is_fraud"},
            {"type": "credit_default", "algorithm": "xgboost", "target": "default_probability"},
        ],
    },
    {
        "package_id": "agriculture-analytics",
        "industry": "agriculture",
        "name": "Agriculture Analytics Package",
        "description": "Production analytics, yield forecasting, and market analysis for agricultural operations.",
        "version": "1.0.0",
        "is_africa_optimized": True,
        "dataset_templates": [
            {
                "name": "Crop Production",
                "columns": [
                    "farm_id",
                    "crop_type",
                    "planted_area",
                    "harvest_amount",
                    "season",
                    "year",
                ],
            },
            {
                "name": "Market Prices",
                "columns": ["crop_type", "market", "price", "date", "region"],
            },
            {
                "name": "Weather Records",
                "columns": ["station_id", "date", "rainfall_mm", "temperature_c", "humidity"],
            },
        ],
        "dashboard_templates": [
            {
                "name": "Farm Executive Dashboard",
                "description": "Yield, revenue, and weather overview",
                "layout": {"grid": "2x3"},
            },
            {
                "name": "Market Analysis Dashboard",
                "description": "Crop prices and market trends",
                "layout": {"grid": "2x2"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Yield",
                "category": "production",
                "formula": "sum(harvest_amount)",
                "unit": "tons",
            },
            {
                "name": "Yield per Hectare",
                "category": "production",
                "formula": "harvest_amount / planted_area",
                "unit": "tons/ha",
            },
            {
                "name": "Avg Market Price",
                "category": "market",
                "formula": "avg(price)",
                "unit": "USD/ton",
            },
            {
                "name": "Revenue",
                "category": "financial",
                "formula": "harvest_amount * price",
                "unit": "USD",
            },
        ],
        "ai_insight_templates": [
            {
                "type": "yield_forecast",
                "prompt": "Forecast crop yields based on weather and historical data",
            },
            {"type": "price_prediction", "prompt": "Predict market prices for key crops"},
        ],
        "ml_model_templates": [
            {"type": "yield_prediction", "algorithm": "random_forest", "target": "yield_tons"},
            {"type": "price_forecast", "algorithm": "arima", "target": "price"},
        ],
    },
    {
        "package_id": "retail-intelligence",
        "industry": "retail",
        "name": "Retail Intelligence Package",
        "description": "Sales analytics, inventory management, and customer insights for retail businesses.",
        "version": "1.0.0",
        "is_africa_optimized": False,
        "dataset_templates": [
            {
                "name": "Sales Records",
                "columns": [
                    "transaction_id",
                    "product_id",
                    "quantity",
                    "amount",
                    "date",
                    "store_id",
                ],
            },
            {
                "name": "Product Catalog",
                "columns": ["product_id", "name", "category", "cost", "price"],
            },
            {
                "name": "Inventory",
                "columns": ["product_id", "store_id", "stock_level", "reorder_point"],
            },
        ],
        "dashboard_templates": [
            {
                "name": "Retail Executive Dashboard",
                "description": "Sales, inventory, and customer overview",
                "layout": {"grid": "2x3"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Revenue",
                "category": "financial",
                "formula": "sum(amount)",
                "unit": "USD",
            },
            {
                "name": "Avg Order Value",
                "category": "financial",
                "formula": "avg(amount)",
                "unit": "USD",
            },
            {
                "name": "Inventory Turnover",
                "category": "operational",
                "formula": "cogs / avg_inventory",
                "unit": "ratio",
            },
        ],
        "ai_insight_templates": [],
        "ml_model_templates": [],
    },
    {
        "package_id": "government-analytics",
        "industry": "government",
        "name": "Government Analytics Package",
        "description": "Public sector analytics: projects, budgets, procurement, and citizen services.",
        "version": "1.0.0",
        "is_africa_optimized": True,
        "dataset_templates": [
            {
                "name": "Project Records",
                "columns": [
                    "project_id",
                    "name",
                    "department",
                    "budget",
                    "spent",
                    "status",
                    "start_date",
                ],
            },
            {
                "name": "Budget Records",
                "columns": ["department", "category", "allocated", "spent", "fiscal_year"],
            },
        ],
        "dashboard_templates": [
            {
                "name": "Government Executive Dashboard",
                "description": "Budget, projects, and procurement overview",
                "layout": {"grid": "2x3"},
            },
        ],
        "kpi_templates": [
            {
                "name": "Total Budget",
                "category": "financial",
                "formula": "sum(allocated)",
                "unit": "USD",
            },
            {
                "name": "Budget Utilization",
                "category": "financial",
                "formula": "spent / allocated * 100",
                "unit": "%",
            },
            {
                "name": "Project Completion Rate",
                "category": "operational",
                "formula": "completed / total * 100",
                "unit": "%",
            },
        ],
        "ai_insight_templates": [],
        "ml_model_templates": [],
    },
]


MARKETPLACE_PLUGINS = [
    {
        "plugin_id": "hospital-connector",
        "name": "Hospital Information System Connector",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Connect to hospital information systems for patient and billing data extraction.",
        "category": "connector",
        "icon": "healthcare",
        "tags": ["healthcare", "africa", "connector"],
        "is_featured": True,
    },
    {
        "plugin_id": "school-connector",
        "name": "Student Information System Connector",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Connect to student information systems for enrollment and performance data.",
        "category": "connector",
        "icon": "education",
        "tags": ["education", "africa", "connector"],
    },
    {
        "plugin_id": "bank-connector",
        "name": "Banking API Connector",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Connect to African banking APIs for transaction and account data.",
        "category": "connector",
        "icon": "bank",
        "tags": ["banking", "africa", "connector"],
    },
    {
        "plugin_id": "mobile-money-connector",
        "name": "Mobile Money Connector",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Connect to mobile money platforms (MTN MoMo, Airtel Money, M-Pesa, Orange Money).",
        "category": "connector",
        "icon": "wallet",
        "tags": ["africa", "fintech", "mobile_money", "connector"],
        "is_featured": True,
    },
    {
        "plugin_id": "healthcare-dashboard-template",
        "name": "Healthcare Dashboard Template",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Pre-built dashboard templates for healthcare analytics.",
        "category": "dashboard_template",
        "icon": "layout",
        "tags": ["healthcare", "dashboard"],
    },
    {
        "plugin_id": "executive-dashboard-template",
        "name": "Executive Dashboard Template",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Executive-level dashboard template with KPIs, trends, and alerts.",
        "category": "dashboard_template",
        "icon": "layout",
        "tags": ["executive", "dashboard"],
        "is_featured": True,
    },
    {
        "plugin_id": "sales-dashboard-template",
        "name": "Sales Dashboard Template",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Sales performance dashboard with revenue, conversion, and pipeline widgets.",
        "category": "dashboard_template",
        "icon": "layout",
        "tags": ["sales", "dashboard"],
    },
    {
        "plugin_id": "finance-dashboard-template",
        "name": "Finance Dashboard Template",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Financial dashboard with budget, spending, and forecast widgets.",
        "category": "dashboard_template",
        "icon": "layout",
        "tags": ["finance", "dashboard"],
    },
    {
        "plugin_id": "healthcare-analytics-package",
        "name": "Healthcare Analytics Package",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Complete healthcare analytics: dashboards, KPIs, AI insights, and ML models.",
        "category": "industry_solution",
        "icon": "package",
        "tags": ["healthcare", "industry", "africa"],
        "is_featured": True,
    },
    {
        "plugin_id": "education-intelligence-package",
        "name": "Education Intelligence Package",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Complete education analytics: enrollment, performance, attendance, fees.",
        "category": "industry_solution",
        "icon": "package",
        "tags": ["education", "industry", "africa"],
    },
    {
        "plugin_id": "banking-analytics-package",
        "name": "Banking Analytics Package",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Banking analytics: transactions, risk, fraud detection.",
        "category": "industry_solution",
        "icon": "package",
        "tags": ["banking", "industry", "africa"],
    },
    {
        "plugin_id": "agriculture-analytics-package",
        "name": "Agriculture Analytics Package",
        "version": "1.0.0",
        "author": "DataFlow Team",
        "description": "Agriculture analytics: production, forecasting, market analysis.",
        "category": "industry_solution",
        "icon": "package",
        "tags": ["agriculture", "industry", "africa"],
    },
]


def seed_ecosystem_data(db: DbSession) -> None:
    """Seed marketplace plugins and industry packages."""
    from sqlalchemy import select

    # Seed plugins
    for plugin_data in MARKETPLACE_PLUGINS:
        existing = db.execute(
            select(Plugin).where(Plugin.plugin_id == plugin_data["plugin_id"])
        ).scalar_one_or_none()
        if not existing:
            plugin = Plugin(
                plugin_id=plugin_data["plugin_id"],
                name=plugin_data["name"],
                version=plugin_data["version"],
                author=plugin_data["author"],
                description=plugin_data["description"],
                category=plugin_data["category"],
                icon=plugin_data.get("icon"),
                tags=plugin_data.get("tags"),
                is_verified=True,
                is_featured=plugin_data.get("is_featured", False),
            )
            db.add(plugin)
            db.flush()

    # Seed industry packages
    for pkg_data in INDUSTRY_PACKAGES:
        existing = db.execute(
            select(IndustryPackage).where(IndustryPackage.package_id == pkg_data["package_id"])
        ).scalar_one_or_none()
        if not existing:
            pkg = IndustryPackage(
                package_id=pkg_data["package_id"],
                industry=pkg_data["industry"],
                name=pkg_data["name"],
                description=pkg_data["description"],
                version=pkg_data["version"],
                dataset_templates=pkg_data.get("dataset_templates"),
                dashboard_templates=pkg_data.get("dashboard_templates"),
                kpi_templates=pkg_data.get("kpi_templates"),
                ai_insight_templates=pkg_data.get("ai_insight_templates"),
                ml_model_templates=pkg_data.get("ml_model_templates"),
                is_africa_optimized=pkg_data.get("is_africa_optimized", False),
            )
            db.add(pkg)
            db.flush()

    db.commit()
    logger.info("Ecosystem marketplace data seeded.")
