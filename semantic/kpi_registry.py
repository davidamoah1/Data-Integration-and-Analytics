from __future__ import annotations

from dataclasses import dataclass

from semantic.dashboard_registry import SALES_INDUSTRIES


@dataclass(frozen=True)
class KPIDefinition:
    key: str
    label: str
    entity: str
    metric: str
    category: str
    threshold: dict | None = None


class KPIRegistry:
    _definitions: dict[str, tuple[KPIDefinition, ...]] = {
        "healthcare": (
            KPIDefinition("admissions", "Admissions", "admission", "count", "operational"),
            KPIDefinition("patients", "Patients", "patient", "count", "operational"),
            KPIDefinition(
                "bed_occupancy",
                "Bed Occupancy",
                "ward",
                "count",
                "operational",
                {"warning": 85, "critical": 95},
            ),
            KPIDefinition(
                "readmissions",
                "Readmissions",
                "admission",
                "count",
                "clinical",
                {"warning": 10, "critical": 15},
            ),
            KPIDefinition("billing", "Patient Billing", "billing", "sum", "financial"),
        ),
        "education": (
            KPIDefinition("enrollment", "Enrollment", "student", "count", "operational"),
            KPIDefinition(
                "attendance", "Attendance", "attendance", "count", "academic", {"warning": 75}
            ),
            KPIDefinition("courses", "Courses", "course", "count", "academic"),
            KPIDefinition("graduation_rate", "Graduation Rate", "graduation", "sum", "academic"),
            KPIDefinition("fees", "Fees", "revenue", "sum", "financial"),
        ),
        "church": (
            KPIDefinition("members", "Members", "member", "count", "operational"),
            KPIDefinition("visitors", "Visitors", "visitor", "count", "operational"),
            KPIDefinition("tithe", "Tithe", "tithe", "sum", "financial"),
            KPIDefinition("offering", "Offering", "offering", "sum", "financial"),
        ),
        "government": (
            KPIDefinition("revenue", "Revenue", "revenue_gov", "sum", "financial"),
            KPIDefinition("budget", "Budget", "budget_gov", "sum", "financial"),
            KPIDefinition("projects", "Projects", "project_gov", "count", "operational"),
            KPIDefinition("procurement", "Procurement", "procurement", "count", "operational"),
            KPIDefinition("assets", "Asset Value", "asset_gov", "sum", "operational"),
        ),
        "ngo": (
            KPIDefinition("beneficiaries", "Beneficiaries", "beneficiary", "count", "impact"),
            KPIDefinition("donors", "Donors", "donor", "count", "financial"),
            KPIDefinition("funding", "Funding", "donation", "sum", "financial"),
            KPIDefinition("programs", "Programs", "program", "count", "operational"),
        ),
        "retail": (
            KPIDefinition("sales", "Sales", "revenue", "sum", "financial"),
            KPIDefinition("orders", "Orders", "order", "count", "operational"),
            KPIDefinition("customers", "Customers", "customer", "count", "operational"),
            KPIDefinition("inventory", "Inventory", "inventory", "count", "operational"),
            KPIDefinition("profit", "Profit", "revenue", "sum", "financial"),
        ),
        "manufacturing": (
            KPIDefinition("production", "Total Production", "production", "sum", "operational"),
            KPIDefinition("machines", "Active Machines", "machine", "count", "operational"),
            KPIDefinition("downtime", "Downtime Hours", "downtime", "sum", "operational"),
            KPIDefinition("yield_rate", "Yield Rate", "production", "sum", "quality"),
        ),
        "agriculture": (
            KPIDefinition("harvest", "Total Harvest", "crop", "sum", "operational"),
            KPIDefinition("farms", "Farms", "farm", "count", "operational"),
            KPIDefinition("yield_per_hectare", "Yield per Hectare", "crop", "sum", "operational"),
            KPIDefinition("livestock", "Livestock Count", "livestock", "sum", "operational"),
            KPIDefinition("rainfall", "Average Rainfall", "weather", "sum", "operational"),
        ),
        "banking": (
            KPIDefinition("accounts", "Accounts", "account", "count", "operational"),
            KPIDefinition("transactions", "Transactions", "transaction", "count", "operational"),
            KPIDefinition("balance", "Total Balance", "account", "sum", "financial"),
            KPIDefinition("loans", "Loans", "loan", "count", "financial"),
            KPIDefinition("cards", "Cards", "card", "count", "operational"),
        ),
        "insurance": (
            KPIDefinition("policies", "Policies", "policy", "count", "operational"),
            KPIDefinition("claims", "Claims", "claim", "count", "operational"),
            KPIDefinition("premium", "Total Premium", "policy", "sum", "financial"),
            KPIDefinition("claim_amount", "Claim Amount", "claim", "sum", "financial"),
            KPIDefinition("agents", "Agents", "agent", "count", "operational"),
        ),
        "hospitality": (
            KPIDefinition("reservations", "Reservations", "reservation", "count", "operational"),
            KPIDefinition("guests", "Guests", "guest", "count", "operational"),
            KPIDefinition("rooms", "Rooms", "room", "count", "operational"),
            KPIDefinition("revenue", "Revenue", "reservation", "sum", "financial"),
            KPIDefinition("services", "Service Revenue", "service", "sum", "financial"),
        ),
        "telecommunications": (
            KPIDefinition("subscribers", "Subscribers", "subscriber", "count", "operational"),
            KPIDefinition("calls", "Calls", "call", "count", "operational"),
            KPIDefinition("data_usage", "Data Usage", "data_usage", "sum", "operational"),
            KPIDefinition("plans", "Plans", "plan", "count", "operational"),
        ),
    }

    @classmethod
    def definitions(cls, industry: str) -> list[KPIDefinition]:
        resolved = "retail" if industry in SALES_INDUSTRIES else industry
        return list(cls._definitions.get(resolved, ()))

    @classmethod
    def to_dict(cls, industry: str) -> list[dict]:
        return [
            {
                "key": definition.key,
                "label": definition.label,
                "entity": definition.entity,
                "metric": definition.metric,
                "category": definition.category,
                "threshold": definition.threshold,
            }
            for definition in cls.definitions(industry)
        ]

    @classmethod
    def register(
        cls, industry: str, definitions: tuple[KPIDefinition, ...], replace: bool = False
    ) -> None:
        if industry in cls._definitions and not replace:
            raise ValueError(f"KPI definitions already registered for {industry}")
        cls._definitions[industry] = definitions
