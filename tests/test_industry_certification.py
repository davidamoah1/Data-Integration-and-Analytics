"""Industry Certification Tests.

Verifies that every supported industry:
1. Is correctly detected from a representative dataset
2. Produces a dashboard with the correct template (no cross-industry contamination)
3. Has KPIs, reports, and knowledge base entries
4. Does NOT default to retail or banking as a fallback
5. Respects the confidence gate (admin_confirmed required for <90%)
"""

from __future__ import annotations

import pandas as pd
import pytest

from semantic.dashboard_generator import DashboardGenerator
from semantic.dashboard_registry import DashboardRegistry
from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE, get_industry_knowledge
from semantic.kpi_registry import KPIRegistry
from semantic.mapping_engine import SemanticMappingEngine
from semantic.report_registry import ReportRegistry


# ── Industry-specific test datasets ──


def _healthcare_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": range(1, 21),
            "patient_name": [f"Patient {i}" for i in range(1, 21)],
            "doctor": [f"Dr. {i}" for i in range(1, 21)],
            "admission_date": pd.date_range("2024-01-01", periods=20),
            "ward": ["ICU", "General", "Pediatric"] * 6 + ["ICU", "General"],
            "diagnosis": ["Flu", "Diabetes", "Hypertension"] * 6 + ["Flu", "Diabetes"],
            "medicine": [f"Med {i}" for i in range(1, 21)],
            "lab_test": [f"Test {i}" for i in range(1, 21)],
            "billing": [1000 * i for i in range(1, 21)],
            "insurance": ["Aetna", "Cigna"] * 10,
        }
    )


def _education_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": range(1, 21),
            "student_name": [f"Student {i}" for i in range(1, 21)],
            "teacher": [f"Teacher {i}" for i in range(1, 21)],
            "course": ["Math", "Science", "English"] * 6 + ["Math", "Science"],
            "department": ["Engineering", "Arts", "Science"] * 6 + ["Engineering", "Arts"],
            "attendance": [80 + i for i in range(20)],
            "exam": [f"Exam {i}" for i in range(1, 21)],
            "grade": ["A", "B", "C"] * 6 + ["A", "B"],
            "fee": [500 * i for i in range(1, 21)],
        }
    )


def _church_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "member_id": range(1, 21),
            "member_name": [f"Member {i}" for i in range(1, 21)],
            "visitor": [f"Visitor {i}" for i in range(1, 21)],
            "branch": ["Branch A", "Branch B"] * 10,
            "ministry": ["Youth", "Music", "Outreach"] * 6 + ["Youth", "Music"],
            "tithe": [100 * i for i in range(1, 21)],
            "offering": [50 * i for i in range(1, 21)],
            "event": [f"Event {i}" for i in range(1, 21)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _retail_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": range(1, 21),
            "customer": [f"Customer {i}" for i in range(1, 21)],
            "product": [f"Product {i}" for i in range(1, 21)],
            "supplier": [f"Supplier {i}" for i in range(1, 21)],
            "inventory": [100 - i for i in range(20)],
            "sales": [1000 * i for i in range(1, 21)],
            "region": ["North", "South", "East"] * 6 + ["North", "South"],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _government_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "project_id": range(1, 21),
            "project_name": [f"Project {i}" for i in range(1, 21)],
            "department": ["Works", "Health", "Education"] * 6 + ["Works", "Health"],
            "budget": [10000 * i for i in range(1, 21)],
            "procurement": [f"Tender {i}" for i in range(1, 21)],
            "citizen": [f"Citizen {i}" for i in range(1, 21)],
            "revenue": [5000 * i for i in range(1, 21)],
            "asset": [f"Asset {i}" for i in range(1, 21)],
        }
    )


def _ngo_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "beneficiary_id": range(1, 21),
            "beneficiary_name": [f"Beneficiary {i}" for i in range(1, 21)],
            "donor": [f"Donor {i}" for i in range(1, 21)],
            "program": ["Health", "Education", "Water"] * 6 + ["Health", "Education"],
            "project": [f"Project {i}" for i in range(1, 21)],
            "donation": [500 * i for i in range(1, 21)],
            "grant": [f"Grant {i}" for i in range(1, 21)],
            "region": ["Africa", "Asia"] * 10,
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _banking_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "account_id": range(1, 21),
            "account_number": [f"ACC{i:05d}" for i in range(1, 21)],
            "transaction_id": range(101, 121),
            "loan_id": [f"LN{i:04d}" for i in range(1, 21)],
            "card": [f"Card {i}" for i in range(1, 21)],
            "balance": [10000 * i for i in range(1, 21)],
            "amount": [100 * i for i in range(1, 21)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _manufacturing_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "machine_id": range(1, 21),
            "machine_name": [f"Machine {i}" for i in range(1, 21)],
            "production_id": range(101, 121),
            "output": [500 + i * 10 for i in range(20)],
            "downtime": [i * 2 for i in range(20)],
            "product": [f"Product {i}" for i in range(1, 21)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _agriculture_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "farm_id": range(1, 21),
            "farm_name": [f"Farm {i}" for i in range(1, 21)],
            "crop": ["Maize", "Rice", "Wheat"] * 6 + ["Maize", "Rice"],
            "harvest": [1000 * i for i in range(1, 21)],
            "livestock": [50 + i for i in range(20)],
            "rainfall": [800 + i * 5 for i in range(20)],
            "temperature": [25 + i * 0.5 for i in range(20)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _insurance_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "policy_id": range(1, 21),
            "policy_number": [f"POL{i:05d}" for i in range(1, 21)],
            "claim_id": range(101, 121),
            "agent": [f"Agent {i}" for i in range(1, 21)],
            "premium": [500 * i for i in range(1, 21)],
            "claim_amount": [200 * i for i in range(1, 21)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _hospitality_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reservation_id": range(1, 21),
            "guest": [f"Guest {i}" for i in range(1, 21)],
            "room": [f"Room {i}" for i in range(1, 21)],
            "booking": [f"Booking {i}" for i in range(1, 21)],
            "service": ["Spa", "Restaurant", "Minibar"] * 6 + ["Spa", "Restaurant"],
            "amount": [200 * i for i in range(1, 21)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


def _telecom_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subscriber_id": range(1, 21),
            "phone_number": [f"+1234567{i:03d}" for i in range(1, 21)],
            "call_id": range(101, 121),
            "plan": ["Basic", "Premium", "Unlimited"] * 6 + ["Basic", "Premium"],
            "data_usage": [1024 * i for i in range(1, 21)],
            "minutes": [60 + i * 5 for i in range(20)],
            "date": pd.date_range("2024-01-01", periods=20),
        }
    )


# ── Test data registry ──

INDUSTRY_DATASETS = {
    "healthcare": _healthcare_df,
    "education": _education_df,
    "church": _church_df,
    "retail": _retail_df,
    "government": _government_df,
    "ngo": _ngo_df,
    "banking": _banking_df,
    "manufacturing": _manufacturing_df,
    "agriculture": _agriculture_df,
    "insurance": _insurance_df,
    "hospitality": _hospitality_df,
    "telecommunications": _telecom_df,
}


# ── Certification Tests ──


@pytest.fixture(params=sorted(INDUSTRY_DATASETS.keys()))
def industry_data(request):
    industry = request.param
    df = INDUSTRY_DATASETS[industry]()
    return industry, df


class TestIndustryCertification:
    """Certify that every industry produces correct, non-contaminated results."""

    def test_industry_detected_correctly(self, industry_data):
        industry, df = industry_data
        mapping = SemanticMappingEngine.analyze(df)
        assert mapping.industry == industry, (
            f"Expected industry '{industry}', got '{mapping.industry}' "
            f"(confidence: {mapping.industry_confidence}%)"
        )

    def test_no_default_to_retail(self, industry_data):
        industry, df = industry_data
        if industry == "retail":
            pytest.skip("Retail is expected to detect as retail")
        mapping = SemanticMappingEngine.analyze(df)
        assert mapping.industry != "retail", (
            f"Industry '{industry}' was incorrectly detected as 'retail'"
        )

    def test_dashboard_template_matches_industry(self, industry_data):
        industry, df = industry_data
        mapping = SemanticMappingEngine.analyze(df)
        config = DashboardGenerator.generate(df, mapping, admin_confirmed=True)
        assert config.industry == industry
        assert config.template == f"{industry}_executive", (
            f"Expected template '{industry}_executive', got '{config.template}'"
        )

    def test_dashboard_has_kpi_cards(self, industry_data):
        industry, df = industry_data
        mapping = SemanticMappingEngine.analyze(df)
        config = DashboardGenerator.generate(df, mapping, admin_confirmed=True)
        assert len(config.kpi_cards) > 0, f"Industry '{industry}' produced no KPI cards"

    def test_dashboard_has_widgets(self, industry_data):
        industry, df = industry_data
        mapping = SemanticMappingEngine.analyze(df)
        config = DashboardGenerator.generate(df, mapping, admin_confirmed=True)
        assert len(config.widgets) > 0, f"Industry '{industry}' produced no widgets"

    def test_dashboard_has_reports(self, industry_data):
        industry, df = industry_data
        reports = ReportRegistry.get(industry)
        assert len(reports) > 0, f"Industry '{industry}' has no report types"

    def test_kpi_registry_has_definitions(self, industry_data):
        industry, df = industry_data
        kpis = KPIRegistry.definitions(industry)
        assert len(kpis) > 0, f"Industry '{industry}' has no KPI definitions"

    def test_industry_knowledge_exists(self, industry_data):
        industry, _ = industry_data
        knowledge = get_industry_knowledge(industry)
        assert knowledge is not None, f"Industry '{industry}' has no knowledge base"
        assert "display_name" in knowledge
        assert "kpis" in knowledge
        assert "business_rules" in knowledge
        assert "alerts" in knowledge

    def test_no_cross_industry_widget_contamination(self, industry_data):
        industry, df = industry_data
        mapping = SemanticMappingEngine.analyze(df)
        config = DashboardGenerator.generate(df, mapping, admin_confirmed=True)
        widget_keys = {w["key"] for w in config.widgets}

        # Define forbidden widgets per industry (widgets from OTHER industries)
        forbidden = {
            "healthcare": {"sales", "orders", "customers", "members", "enrollment"},
            "education": {"sales", "orders", "patients", "members", "accounts"},
            "church": {"sales", "orders", "patients", "students", "accounts"},
            "retail": {"patients", "students", "members", "admissions"},
            "government": {"sales", "orders", "patients", "students", "members"},
            "ngo": {"sales", "orders", "patients", "students", "members"},
            "banking": {"sales", "orders", "patients", "students", "members"},
            "manufacturing": {"sales", "orders", "patients", "students", "members"},
            "agriculture": {"sales", "orders", "patients", "students", "members"},
            "insurance": {"sales", "orders", "patients", "students", "members"},
            "hospitality": {"sales", "orders", "patients", "students", "members"},
            "telecommunications": {"sales", "orders", "patients", "students", "members"},
        }
        forbidden_set = forbidden.get(industry, set())
        contamination = widget_keys & forbidden_set
        assert not contamination, (
            f"Industry '{industry}' dashboard contains cross-industry widgets: {contamination}"
        )

    def test_dashboard_registry_template_exists(self, industry_data):
        industry, _ = industry_data
        template = DashboardRegistry.get(industry)
        assert template is not None, f"Industry '{industry}' has no dashboard template"

    def test_dashboard_registry_to_dict_valid(self, industry_data):
        industry, _ = industry_data
        d = DashboardRegistry.to_dict(industry)
        assert d["template"] is not None
        assert d["title"] is not None
        assert len(d["widgets"]) > 0


class TestConfidenceGate:
    """Verify the confidence gate blocks low-confidence dashboard generation."""

    def test_low_confidence_blocks_dashboard(self):
        df = pd.DataFrame(
            {
                "col_a": range(10),
                "col_b": range(10),
                "col_c": range(10),
            }
        )
        mapping = SemanticMappingEngine.analyze(df)
        assert mapping.industry == "unknown"
        assert mapping.industry_confidence == 0.0

        with pytest.raises(ValueError, match="confidence"):
            DashboardGenerator.generate(df, mapping, admin_confirmed=False)

    def test_admin_confirmed_bypasses_gate(self):
        df = pd.DataFrame(
            {
                "col_a": range(10),
                "col_b": range(10),
                "col_c": range(10),
            }
        )
        mapping = SemanticMappingEngine.analyze(df)
        with pytest.raises(ValueError, match="No dashboard template"):
            DashboardGenerator.generate(df, mapping, admin_confirmed=True)

    def test_high_confidence_allows_dashboard(self):
        df = _healthcare_df()
        mapping = SemanticMappingEngine.analyze(df)
        if mapping.industry_confidence >= 90.0:
            config = DashboardGenerator.generate(df, mapping, admin_confirmed=False)
            assert config.industry == "healthcare"


class TestNoFallbackDefaults:
    """Verify no hidden fallbacks to retail or banking."""

    def test_unknown_industry_returns_none_template(self):
        template = DashboardRegistry.get("nonexistent_industry")
        assert template is None

    def test_unknown_industry_returns_empty_reports(self):
        reports = ReportRegistry.get("nonexistent_industry")
        assert reports == []

    def test_unknown_industry_returns_empty_kpis(self):
        kpis = KPIRegistry.definitions("nonexistent_industry")
        assert kpis == []

    def test_all_12_industries_have_knowledge(self):
        assert len(INDUSTRY_KNOWLEDGE) == 12
        expected = {
            "healthcare",
            "education",
            "church",
            "retail",
            "government",
            "ngo",
            "banking",
            "manufacturing",
            "agriculture",
            "insurance",
            "hospitality",
            "telecommunications",
        }
        assert set(INDUSTRY_KNOWLEDGE.keys()) == expected

    def test_all_12_industries_have_dashboard_templates(self):
        for industry in INDUSTRY_KNOWLEDGE:
            template = DashboardRegistry.get(industry)
            assert template is not None, f"Missing dashboard template for {industry}"

    def test_all_12_industries_have_reports(self):
        for industry in INDUSTRY_KNOWLEDGE:
            reports = ReportRegistry.get(industry)
            assert len(reports) > 0, f"Missing reports for {industry}"

    def test_all_12_industries_have_kpis(self):
        for industry in INDUSTRY_KNOWLEDGE:
            kpis = KPIRegistry.definitions(industry)
            assert len(kpis) > 0, f"Missing KPI definitions for {industry}"
