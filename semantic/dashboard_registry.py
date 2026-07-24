from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SALES_INDUSTRIES = frozenset({"retail", "sme", "wholesale", "distribution"})


@dataclass(frozen=True)
class WidgetDefinition:
    key: str
    widget_type: str
    title: str
    entity: str | None = None
    metric: str = "count"
    group_by: str | None = None
    time_entity: str | None = "date"
    required_entities: tuple[str, ...] = ()
    category: str = "operational"
    threshold: dict[str, Any] | None = None

    def to_dict(self, available: bool = True) -> dict:
        return {
            "key": self.key,
            "type": self.widget_type,
            "title": self.title,
            "entity": self.entity,
            "metric": self.metric,
            "group_by": self.group_by,
            "time_entity": self.time_entity,
            "required_entities": list(self.required_entities),
            "category": self.category,
            "threshold": self.threshold,
            "available": available,
        }


@dataclass(frozen=True)
class DashboardTemplate:
    key: str
    title: str
    report_types: tuple[str, ...]
    ai_insights: tuple[str, ...]
    widgets: tuple[WidgetDefinition, ...]


class WidgetRegistry:
    _supported_types = frozenset(
        {
            "kpi_card",
            "trend_card",
            "line_chart",
            "bar_chart",
            "pie_chart",
            "map",
            "heat_map",
            "timeline",
            "gauge",
            "leaderboard",
            "table",
            "tree",
            "forecast",
        }
    )

    @classmethod
    def validate(cls, widget: WidgetDefinition) -> None:
        if widget.widget_type not in cls._supported_types:
            raise ValueError(f"Unsupported widget type: {widget.widget_type}")

    @classmethod
    def supported_types(cls) -> list[str]:
        return sorted(cls._supported_types)


class DashboardRegistry:
    _templates: dict[str, DashboardTemplate] = {}
    _aliases = {
        "sme": "retail",
        "retail": "retail",
        "wholesale": "retail",
        "distribution": "retail",
        "healthcare": "healthcare",
        "education": "education",
        "church": "church",
        "government": "government",
        "ngo": "ngo",
        "manufacturing": "manufacturing",
        "agriculture": "agriculture",
        "banking": "banking",
        "insurance": "insurance",
        "hospitality": "hospitality",
        "telecommunications": "telecommunications",
    }

    @classmethod
    def register(cls, industry: str, template: DashboardTemplate, replace: bool = False) -> None:
        if industry in cls._templates and not replace:
            raise ValueError(f"Dashboard template already registered for {industry}")
        for widget in template.widgets:
            WidgetRegistry.validate(widget)
        cls._templates[industry] = template

    @classmethod
    def get(cls, industry: str) -> DashboardTemplate | None:
        resolved_industry = cls._aliases.get(industry, industry)
        return cls._templates.get(resolved_industry)

    @classmethod
    def industries(cls) -> list[str]:
        return sorted(cls._templates)

    @classmethod
    def to_dict(cls, industry: str) -> dict:
        template = cls.get(industry)
        if template is None:
            return {
                "industry": industry,
                "template": None,
                "title": None,
                "reports": [],
                "ai_insights": [],
                "widgets": [],
            }
        return {
            "industry": industry,
            "template": template.key,
            "title": template.title,
            "reports": list(template.report_types),
            "ai_insights": list(template.ai_insights),
            "widgets": [widget.to_dict() for widget in template.widgets],
        }


def _widgets(*definitions: WidgetDefinition) -> tuple[WidgetDefinition, ...]:
    return definitions


def _card(
    key: str, title: str, entity: str | None, metric: str = "count", category: str = "operational"
) -> WidgetDefinition:
    required = (entity,) if entity else ()
    return WidgetDefinition(
        key, "kpi_card", title, entity, metric, required_entities=required, category=category
    )


def _chart(
    key: str, widget_type: str, title: str, entity: str, group_by: str | None = None
) -> WidgetDefinition:
    required = tuple(item for item in (entity, group_by) if item)
    return WidgetDefinition(
        key, widget_type, title, entity, "sum", group_by, required_entities=required
    )


DashboardRegistry.register(
    "healthcare",
    DashboardTemplate(
        "healthcare_executive",
        "Healthcare Executive Dashboard",
        ("executive", "admissions", "clinical_quality", "revenue_cycle", "medicine_inventory"),
        (
            "Analyze admission volume and readmission patterns.",
            "Identify departments with capacity or care-quality risks.",
        ),
        _widgets(
            _card("admissions", "Admissions", "admission"),
            _card("discharges", "Discharges", "admission"),
            _card("patients", "Patients", "patient"),
            _card("emergency", "Emergency Visits", "appointment"),
            _card("inpatient", "Inpatients", "admission"),
            _card("icu", "ICU Activity", "ward"),
            _card("bed_occupancy", "Bed Occupancy", "ward"),
            _card("readmissions", "Readmissions", "admission"),
            _card("laboratory", "Laboratory Tests", "lab_test"),
            _card("radiology", "Radiology", "lab_test"),
            _card("pharmacy", "Pharmacy", "medicine"),
            _card("insurance", "Insurance Claims", "insurance", category="financial"),
            _card("billing", "Patient Billing", "billing", "sum", "financial"),
            _chart("disease_trends", "line_chart", "Disease Trends", "patient", "diagnosis"),
            _chart("doctor_performance", "leaderboard", "Doctor Performance", "doctor", "patient"),
            _chart("ward_occupancy", "bar_chart", "Ward Utilization", "admission", "ward"),
        ),
    ),
)
DashboardRegistry.register(
    "education",
    DashboardTemplate(
        "education_executive",
        "Education Executive Dashboard",
        ("executive", "enrollment", "academic_performance", "attendance", "fees", "student_risk"),
        (
            "Identify students with low attendance or performance.",
            "Compare enrollment and fee collection across departments.",
        ),
        _widgets(
            _card("enrollment", "Enrollment", "student"),
            _card("attendance", "Attendance", "attendance"),
            _card("students", "Students", "student"),
            _card("teachers", "Teachers", "teacher"),
            _card("courses", "Courses", "course"),
            _card("departments", "Departments", "department_edu"),
            _card("exam_results", "Exam Results", "exam"),
            _card("graduation", "Graduation Rate", "graduation", "sum", "academic"),
            _card("fees", "Fees", "revenue", "sum", "financial"),
            _chart(
                "enrollment_by_department",
                "bar_chart",
                "Enrollment by Department",
                "student",
                "department_edu",
            ),
            _chart("course_performance", "leaderboard", "Course Performance", "grade", "course"),
            _chart("attendance_trend", "line_chart", "Attendance Trend", "attendance", "date"),
        ),
    ),
)
DashboardRegistry.register(
    "church",
    DashboardTemplate(
        "church_executive",
        "Church Executive Dashboard",
        ("executive", "membership", "giving", "attendance", "branch_growth", "ministry"),
        (
            "Identify branches with declining attendance.",
            "Analyze member retention and giving patterns.",
        ),
        _widgets(
            _card("members", "Members", "member"),
            _card("visitors", "Visitors", "visitor"),
            _card("attendance", "Attendance", "attendance_church"),
            _card("baptism", "Baptisms", "member"),
            _card("tithe", "Tithe", "tithe", "sum", "financial"),
            _card("offering", "Offering", "offering", "sum", "financial"),
            _card("branches", "Branches", "branch_church"),
            _card("ministries", "Ministries", "ministry"),
            _card("events", "Events", "event"),
            _chart("giving_trend", "line_chart", "Giving Trend", "offering", "date"),
            _chart("branch_growth", "bar_chart", "Growth by Branch", "member", "branch_church"),
            _chart("ministry_engagement", "pie_chart", "Ministry Engagement", "member", "ministry"),
        ),
    ),
)
DashboardRegistry.register(
    "government",
    DashboardTemplate(
        "government_executive",
        "Government Executive Dashboard",
        ("executive", "budget", "projects", "procurement", "citizen_services", "assets"),
        (
            "Identify projects at risk of delay or budget overrun.",
            "Review procurement concentration and budget utilization.",
        ),
        _widgets(
            _card("revenue", "Revenue", "revenue_gov", "sum", "financial"),
            _card("budget", "Budget", "budget_gov", "sum", "financial"),
            _card("projects", "Projects", "project_gov"),
            _card("departments", "Departments", "department_gov"),
            _card("procurement", "Procurement", "procurement"),
            _card("citizen_services", "Citizen Services", "citizen"),
            _card("assets", "Asset Value", "asset_gov", "sum", "operational"),
            _chart(
                "project_status",
                "bar_chart",
                "Projects by Department",
                "project_gov",
                "department_gov",
            ),
            _chart(
                "budget_utilization", "gauge", "Budget Utilization", "budget_gov", "department_gov"
            ),
        ),
    ),
)
DashboardRegistry.register(
    "ngo",
    DashboardTemplate(
        "ngo_executive",
        "NGO Executive Dashboard",
        (
            "executive",
            "programs",
            "beneficiaries",
            "donors",
            "funding",
            "impact",
            "monitoring_evaluation",
        ),
        (
            "Compare beneficiary reach and impact by program.",
            "Identify donor retention and funding concentration risks.",
        ),
        _widgets(
            _card("projects", "Projects", "project_ngo"),
            _card("beneficiaries", "Beneficiaries", "beneficiary"),
            _card("donors", "Donors", "donor"),
            _card("funding", "Funding", "donation", "sum", "financial"),
            _card("programs", "Programs", "program"),
            _chart("program_impact", "bar_chart", "Impact by Program", "beneficiary", "program"),
            _chart("funding_trend", "line_chart", "Funding Trend", "donation", "date"),
            _chart(
                "beneficiary_coverage", "heat_map", "Beneficiary Coverage", "beneficiary", "region"
            ),
        ),
    ),
)
DashboardRegistry.register(
    "retail",
    DashboardTemplate(
        "retail_executive",
        "Retail Executive Dashboard",
        ("executive", "sales", "orders", "customers", "inventory", "cash_flow", "profitability"),
        (
            "Identify profitable products and regions.",
            "Detect inventory risks and customer trends.",
        ),
        _widgets(
            _card("sales", "Sales", "revenue", "sum", "financial"),
            _card("orders", "Orders", "order"),
            _card("customers", "Customers", "customer"),
            _card("inventory", "Inventory", "inventory"),
            _card("suppliers", "Suppliers", "supplier"),
            _card("profit", "Profit", "revenue", "sum", "financial"),
            _chart("sales_trend", "line_chart", "Sales Trend", "revenue", "date"),
            _chart("product_performance", "bar_chart", "Product Performance", "revenue", "product"),
            _chart(
                "customer_distribution", "pie_chart", "Customer Distribution", "customer", "region"
            ),
        ),
    ),
)
DashboardRegistry.register(
    "manufacturing",
    DashboardTemplate(
        "manufacturing_executive",
        "Manufacturing Executive Dashboard",
        ("executive", "production", "machine_utilization", "downtime", "yield", "quality"),
        (
            "Identify production bottlenecks and under-utilized machines.",
            "Track downtime reasons and yield rates by product line.",
        ),
        _widgets(
            _card("production", "Total Production", "production", "sum", "operational"),
            _card("machines", "Active Machines", "machine", "count", "operational"),
            _card("utilization", "Utilization Rate", "machine", "count", "operational"),
            _card("downtime", "Downtime Hours", "downtime", "sum", "operational"),
            _card("yield", "Yield Rate", "production", "sum", "quality"),
            _chart("production_trend", "line_chart", "Production Trend", "production", "date"),
            _chart("production_by_machine", "bar_chart", "Production by Machine", "production", "machine"),
            _chart("downtime_reasons", "bar_chart", "Downtime Reasons", "downtime", "machine"),
        ),
    ),
)
DashboardRegistry.register(
    "agriculture",
    DashboardTemplate(
        "agriculture_executive",
        "Agriculture Executive Dashboard",
        ("executive", "farm_yield", "harvest", "livestock", "weather", "crop"),
        (
            "Compare farm yields and harvest volumes across crops.",
            "Correlate weather patterns with yield outcomes.",
        ),
        _widgets(
            _card("harvest", "Total Harvest", "crop", "sum", "operational"),
            _card("farms", "Farms", "farm", "count", "operational"),
            _card("yield_per_hectare", "Yield per Hectare", "crop", "sum", "operational"),
            _card("livestock", "Livestock Count", "livestock", "sum", "operational"),
            _card("rainfall", "Average Rainfall", "weather", "sum", "operational"),
            _chart("yield_by_farm", "bar_chart", "Yield by Farm", "crop", "farm"),
            _chart("harvest_by_crop", "pie_chart", "Harvest by Crop", "crop", "crop"),
            _chart("weather_trend", "line_chart", "Weather Trend", "weather", "date"),
        ),
    ),
)
DashboardRegistry.register(
    "banking",
    DashboardTemplate(
        "banking_executive",
        "Banking Executive Dashboard",
        ("executive", "accounts", "transactions", "loans", "cards", "deposits"),
        (
            "Monitor account balances and transaction volumes across branches.",
            "Track loan portfolio health and card activity.",
        ),
        _widgets(
            _card("accounts", "Accounts", "account", "count", "operational"),
            _card("transactions", "Transactions", "transaction", "count", "operational"),
            _card("balance", "Total Balance", "account", "sum", "financial"),
            _card("loans", "Loans", "loan", "count", "financial"),
            _card("cards", "Cards", "card", "count", "operational"),
            _chart("transaction_trend", "line_chart", "Transaction Trend", "transaction", "date"),
            _chart("balance_by_branch", "bar_chart", "Balance by Branch", "account", "account"),
            _chart("transaction_types", "pie_chart", "Transaction Types", "transaction", "transaction"),
        ),
    ),
)
DashboardRegistry.register(
    "insurance",
    DashboardTemplate(
        "insurance_executive",
        "Insurance Executive Dashboard",
        ("executive", "policies", "claims", "premiums", "agents", "coverage"),
        (
            "Monitor policy volume and premium income.",
            "Track claim approval rates and agent performance.",
        ),
        _widgets(
            _card("policies", "Policies", "policy", "count", "operational"),
            _card("claims", "Claims", "claim", "count", "operational"),
            _card("premium", "Total Premium", "policy", "sum", "financial"),
            _card("claim_amount", "Claim Amount", "claim", "sum", "financial"),
            _card("agents", "Agents", "agent", "count", "operational"),
            _chart("claim_trend", "line_chart", "Claim Trend", "claim", "date"),
            _chart("policies_by_agent", "bar_chart", "Policies by Agent", "policy", "agent"),
            _chart("claim_status", "pie_chart", "Claim Status", "claim", "claim"),
        ),
    ),
)
DashboardRegistry.register(
    "hospitality",
    DashboardTemplate(
        "hospitality_executive",
        "Hospitality Executive Dashboard",
        ("executive", "reservations", "guests", "rooms", "revenue", "services"),
        (
            "Monitor occupancy rates and revenue per available room.",
            "Track guest satisfaction and service revenue.",
        ),
        _widgets(
            _card("reservations", "Reservations", "reservation", "count", "operational"),
            _card("guests", "Guests", "guest", "count", "operational"),
            _card("rooms", "Rooms", "room", "count", "operational"),
            _card("revenue", "Revenue", "reservation", "sum", "financial"),
            _card("services", "Service Revenue", "service", "sum", "financial"),
            _chart("reservation_trend", "line_chart", "Reservation Trend", "reservation", "date"),
            _chart("revenue_by_room_type", "bar_chart", "Revenue by Room Type", "room", "room"),
            _chart("service_distribution", "pie_chart", "Service Distribution", "service", "service"),
        ),
    ),
)
DashboardRegistry.register(
    "telecommunications",
    DashboardTemplate(
        "telecommunications_executive",
        "Telecommunications Executive Dashboard",
        ("executive", "subscribers", "calls", "data_usage", "plans", "revenue"),
        (
            "Monitor subscriber growth and churn rates.",
            "Track call volume, data usage, and plan revenue.",
        ),
        _widgets(
            _card("subscribers", "Subscribers", "subscriber", "count", "operational"),
            _card("calls", "Calls", "call", "count", "operational"),
            _card("data_usage", "Data Usage", "data_usage", "sum", "operational"),
            _card("plans", "Plans", "plan", "count", "operational"),
            _card("revenue", "Revenue", "call", "sum", "financial"),
            _chart("call_trend", "line_chart", "Call Trend", "call", "date"),
            _chart("subscribers_by_plan", "bar_chart", "Subscribers by Plan", "subscriber", "plan"),
            _chart("data_usage_trend", "line_chart", "Data Usage Trend", "data_usage", "date"),
        ),
    ),
)
