from __future__ import annotations


class ReportRegistry:
    _reports: dict[str, tuple[str, ...]] = {
        "healthcare": (
            "executive",
            "admissions",
            "clinical_quality",
            "revenue_cycle",
            "medicine_inventory",
        ),
        "education": (
            "executive",
            "enrollment",
            "academic_performance",
            "attendance",
            "fees",
            "student_risk",
        ),
        "church": ("executive", "membership", "giving", "attendance", "branch_growth", "ministry"),
        "government": (
            "executive",
            "budget",
            "projects",
            "procurement",
            "citizen_services",
            "assets",
        ),
        "ngo": (
            "executive",
            "programs",
            "beneficiaries",
            "donors",
            "funding",
            "impact",
            "monitoring_evaluation",
        ),
        "retail": (
            "executive",
            "sales",
            "orders",
            "customers",
            "inventory",
            "cash_flow",
            "profitability",
        ),
        "banking": (
            "executive",
            "accounts",
            "transactions",
            "loans",
            "cards",
            "risk_assessment",
        ),
        "manufacturing": (
            "executive",
            "production",
            "machine_utilization",
            "downtime_analysis",
            "quality_yield",
        ),
        "agriculture": (
            "executive",
            "harvest",
            "livestock",
            "farm_performance",
            "weather_impact",
        ),
        "insurance": (
            "executive",
            "policies",
            "claims",
            "premiums",
            "agent_performance",
        ),
        "hospitality": (
            "executive",
            "reservations",
            "guests",
            "rooms",
            "revenue",
            "services",
        ),
        "telecommunications": (
            "executive",
            "subscribers",
            "calls",
            "data_usage",
            "plans",
            "revenue",
        ),
    }

    @classmethod
    def get(cls, industry: str) -> list[str]:
        return list(cls._reports.get(industry, ()))

    @classmethod
    def register(cls, industry: str, reports: tuple[str, ...], replace: bool = False) -> None:
        if industry in cls._reports and not replace:
            raise ValueError(f"Report definitions already registered for {industry}")
        cls._reports[industry] = reports
