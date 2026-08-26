"""Tests for the Industry Intelligence Platform.

Verifies that each sector analytics module produces correct insights,
breakdowns, trends, and alerts for domain-specific data.
"""

from __future__ import annotations

import pandas as pd
import pytest

from industry_intelligence.agriculture import AgricultureAnalytics
from industry_intelligence.banking import BankingAnalytics
from industry_intelligence.base import (
    AnalyticsResult,
    IndustryAnalyticsRegistry,
)
from industry_intelligence.education import EducationAnalytics
from industry_intelligence.government import GovernmentAnalytics
from industry_intelligence.healthcare import HealthcareAnalytics
from industry_intelligence.manufacturing import ManufacturingAnalytics
from industry_intelligence.ngo import NGOAnalytics
from industry_intelligence.retail import RetailAnalytics


@pytest.fixture
def healthcare_df():
    return pd.DataFrame(
        {
            "patient_id": range(1, 21),
            "doctor_name": [f"Dr. {i % 5}" for i in range(20)],
            "department": ["Cardiology"] * 10 + ["Neurology"] * 10,
            "diagnosis_code": ["A00.1", "B01.0", "C50.2", "D45.0", "E11.9"] * 4,
            "billing_amount": [1000 + i * 50 for i in range(20)],
            "visit_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
            "gender": ["M", "F"] * 10,
        }
    )


@pytest.fixture
def healthcare_col_mapping():
    return {
        "patient_id": "patient",
        "doctor_name": "doctor",
        "department": "ward",
        "diagnosis_code": "diagnosis",
        "billing_amount": "billing",
        "visit_date": "date",
        "gender": "gender",
    }


@pytest.fixture
def education_df():
    return pd.DataFrame(
        {
            "student_id": range(1, 21),
            "teacher_name": [f"Teacher_{i % 4}" for i in range(20)],
            "course_name": [f"Course_{chr(65 + i % 3)}" for i in range(20)],
            "department": ["Science"] * 10 + ["Arts"] * 10,
            "grade": ["A", "B", "C", "D", "F"] * 4,
            "attendance_rate": [80 + i for i in range(20)],
            "fee_amount": [500 + i * 10 for i in range(20)],
            "enrollment_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
        }
    )


@pytest.fixture
def education_col_mapping():
    return {
        "student_id": "student",
        "teacher_name": "teacher",
        "course_name": "course",
        "department": "department_edu",
        "grade": "grade",
        "attendance_rate": "attendance",
        "fee_amount": "revenue",
        "enrollment_date": "date",
    }


@pytest.fixture
def banking_df():
    return pd.DataFrame(
        {
            "account_number": [f"ACC{i:04d}" for i in range(20)],
            "transaction_id": range(1, 21),
            "loan_id": [f"LN{i:04d}" for i in range(20)],
            "amount": [5000 + i * 100 for i in range(20)],
            "transaction_date": pd.date_range("2024-01-01", periods=20, freq="D"),
            "customer_id": [i % 10 + 1 for i in range(20)],
        }
    )


@pytest.fixture
def banking_col_mapping():
    return {
        "account_number": "account",
        "transaction_id": "transaction",
        "loan_id": "loan",
        "amount": "amount",
        "transaction_date": "date",
        "customer_id": "customer",
    }


@pytest.fixture
def agriculture_df():
    return pd.DataFrame(
        {
            "farm_id": [f"Farm_{i % 5}" for i in range(20)],
            "crop_name": ["Maize", "Rice", "Wheat", "Cassava"] * 5,
            "harvest_kg": [1000 + i * 50 for i in range(20)],
            "livestock_type": ["Cattle", "Goat", "Sheep"] * 6 + ["Cattle", "Goat"],
            "rainfall_mm": [800 + i * 5 for i in range(20)],
            "hectares": [10 + i for i in range(20)],
            "region": ["North", "South", "East", "West"] * 5,
            "record_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
        }
    )


@pytest.fixture
def agriculture_col_mapping():
    return {
        "farm_id": "farm",
        "crop_name": "crop",
        "harvest_kg": "crop",
        "livestock_type": "livestock",
        "rainfall_mm": "weather",
        "hectares": "area",
        "region": "region",
        "record_date": "date",
    }


@pytest.fixture
def government_df():
    return pd.DataFrame(
        {
            "project_id": [f"PRJ{i:03d}" for i in range(20)],
            "department": ["Health", "Education", "Infrastructure"] * 6 + ["Health", "Education"],
            "budget_amount": [100000 + i * 5000 for i in range(20)],
            "revenue_amount": [120000 + i * 4000 for i in range(20)],
            "contractor": [f"Contractor_{i % 4}" for i in range(20)],
            "region": ["North", "South", "East", "West"] * 5,
            "project_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
        }
    )


@pytest.fixture
def government_col_mapping():
    return {
        "project_id": "project_gov",
        "department": "department_gov",
        "budget_amount": "budget_gov",
        "revenue_amount": "revenue_gov",
        "contractor": "contractor",
        "region": "region",
        "project_date": "date",
    }


@pytest.fixture
def retail_df():
    return pd.DataFrame(
        {
            "order_id": range(1, 31),
            "customer_id": [i % 10 + 1 for i in range(30)],
            "product_name": [f"Product_{chr(65 + i % 5)}" for i in range(30)],
            "category": ["Electronics", "Clothing", "Food"] * 10,
            "sales_amount": [100.0 + i * 10 for i in range(30)],
            "profit": [20.0 + i * 2 for i in range(30)],
            "order_date": pd.date_range("2024-01-01", periods=30, freq="D"),
            "region": ["North", "South", "East", "West"] * 7 + ["North", "South"],
        }
    )


@pytest.fixture
def retail_col_mapping():
    return {
        "order_id": "order",
        "customer_id": "customer",
        "product_name": "product",
        "category": "category",
        "sales_amount": "revenue",
        "profit": "profit",
        "order_date": "date",
        "region": "region",
    }


@pytest.fixture
def manufacturing_df():
    return pd.DataFrame(
        {
            "machine_id": [f"M{i % 5}" for i in range(20)],
            "production_volume": [500 + i * 10 for i in range(20)],
            "downtime_hours": [2 + i * 0.5 for i in range(20)],
            "product_line": ["WidgetA", "WidgetB", "WidgetC"] * 6 + ["WidgetA", "WidgetB"],
            "yield_rate": [95 + i * 0.2 for i in range(20)],
            "production_date": pd.date_range("2024-01-01", periods=20, freq="D"),
        }
    )


@pytest.fixture
def manufacturing_col_mapping():
    return {
        "machine_id": "machine",
        "production_volume": "production",
        "downtime_hours": "downtime",
        "product_line": "product",
        "yield_rate": "yield",
        "production_date": "date",
    }


@pytest.fixture
def ngo_df():
    return pd.DataFrame(
        {
            "donor_id": [f"Donor_{i % 8}" for i in range(20)],
            "beneficiary_id": range(1, 21),
            "program_name": ["Education", "Health", "Agriculture"] * 6 + ["Education", "Health"],
            "donation_amount": [500 + i * 20 for i in range(20)],
            "region": ["North", "South", "East", "West"] * 5,
            "donation_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
        }
    )


@pytest.fixture
def ngo_col_mapping():
    return {
        "donor_id": "donor",
        "beneficiary_id": "beneficiary",
        "program_name": "program",
        "donation_amount": "donation",
        "region": "region",
        "donation_date": "date",
    }


class TestRegistry:
    def test_all_industries_registered(self):
        industries = IndustryAnalyticsRegistry.industries()
        for expected in (
            "healthcare",
            "education",
            "banking",
            "agriculture",
            "government",
            "retail",
            "manufacturing",
            "ngo",
        ):
            assert expected in industries, f"{expected} not registered"

    def test_get_engine(self):
        engine = IndustryAnalyticsRegistry.get("healthcare")
        assert engine is HealthcareAnalytics

    def test_get_unknown_returns_none(self):
        assert IndustryAnalyticsRegistry.get("nonexistent") is None

    def test_analyze_dispatches_correctly(self, healthcare_df, healthcare_col_mapping):
        result = IndustryAnalyticsRegistry.analyze(
            "healthcare", healthcare_df, healthcare_col_mapping
        )
        assert result is not None
        assert result.industry == "healthcare"


class TestHealthcareAnalytics:
    def test_returns_result(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        assert isinstance(result, AnalyticsResult)
        assert result.industry == "healthcare"

    def test_patient_insight(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        patient_insight = result.get_insight("Total Patients")
        assert patient_insight is not None
        assert patient_insight.value == 20

    def test_doctor_insight(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        doctor_insight = result.get_insight("Active Doctors")
        assert doctor_insight is not None
        assert doctor_insight.value == 5

    def test_billing_insight(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        billing = result.get_insight("Total Billing")
        assert billing is not None
        assert billing.value > 0

    def test_diagnosis_breakdown(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        diag_breakdowns = [b for b in result.breakdowns if b.dimension == "Diagnosis"]
        assert len(diag_breakdowns) > 0

    def test_billing_trend(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        billing_trends = [t for t in result.trends if t.metric == "billing"]
        assert len(billing_trends) > 0

    def test_has_recommendations(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        assert len(result.recommendations) > 0

    def test_to_dict(self, healthcare_df, healthcare_col_mapping):
        result = HealthcareAnalytics.analyze(healthcare_df, healthcare_col_mapping)
        d = result.to_dict()
        assert d["industry"] == "healthcare"
        assert isinstance(d["insights"], list)
        assert isinstance(d["breakdowns"], list)


class TestEducationAnalytics:
    def test_returns_result(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        assert result.industry == "education"

    def test_student_insight(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        assert result.get_insight("Total Students").value == 20

    def test_teacher_insight(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        assert result.get_insight("Active Teachers").value == 4

    def test_fee_insight(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        fees = result.get_insight("Total Fees")
        assert fees is not None
        assert fees.value > 0

    def test_grade_breakdown(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        grade_bd = [b for b in result.breakdowns if b.dimension == "Grade"]
        assert len(grade_bd) > 0

    def test_attendance_insight(self, education_df, education_col_mapping):
        result = EducationAnalytics.analyze(education_df, education_col_mapping)
        attendance = result.get_insight("Average Attendance")
        assert attendance is not None


class TestBankingAnalytics:
    def test_returns_result(self, banking_df, banking_col_mapping):
        result = BankingAnalytics.analyze(banking_df, banking_col_mapping)
        assert result.industry == "banking"

    def test_account_insight(self, banking_df, banking_col_mapping):
        result = BankingAnalytics.analyze(banking_df, banking_col_mapping)
        assert result.get_insight("Total Accounts").value == 20

    def test_transaction_insight(self, banking_df, banking_col_mapping):
        result = BankingAnalytics.analyze(banking_df, banking_col_mapping)
        assert result.get_insight("Total Transactions").value == 20

    def test_volume_insight(self, banking_df, banking_col_mapping):
        result = BankingAnalytics.analyze(banking_df, banking_col_mapping)
        vol = result.get_insight("Total Transaction Volume")
        assert vol is not None
        assert vol.value > 0

    def test_loan_insight(self, banking_df, banking_col_mapping):
        result = BankingAnalytics.analyze(banking_df, banking_col_mapping)
        assert result.get_insight("Total Loans").value == 20


class TestAgricultureAnalytics:
    def test_returns_result(self, agriculture_df, agriculture_col_mapping):
        result = AgricultureAnalytics.analyze(agriculture_df, agriculture_col_mapping)
        assert result.industry == "agriculture"

    def test_farm_insight(self, agriculture_df, agriculture_col_mapping):
        result = AgricultureAnalytics.analyze(agriculture_df, agriculture_col_mapping)
        assert result.get_insight("Total Farms").value == 5

    def test_production_insight(self, agriculture_df, agriculture_col_mapping):
        result = AgricultureAnalytics.analyze(agriculture_df, agriculture_col_mapping)
        prod = result.get_insight("Total Production")
        assert prod is not None
        assert prod.value > 0

    def test_crop_breakdown(self, agriculture_df, agriculture_col_mapping):
        result = AgricultureAnalytics.analyze(agriculture_df, agriculture_col_mapping)
        crop_bd = [b for b in result.breakdowns if b.dimension == "Crop"]
        assert len(crop_bd) > 0

    def test_yield_per_hectare(self, agriculture_df, agriculture_col_mapping):
        result = AgricultureAnalytics.analyze(agriculture_df, agriculture_col_mapping)
        yph = result.get_insight("Yield per Hectare")
        assert yph is not None
        assert yph.value > 0


class TestGovernmentAnalytics:
    def test_returns_result(self, government_df, government_col_mapping):
        result = GovernmentAnalytics.analyze(government_df, government_col_mapping)
        assert result.industry == "government"

    def test_project_insight(self, government_df, government_col_mapping):
        result = GovernmentAnalytics.analyze(government_df, government_col_mapping)
        assert result.get_insight("Total Projects").value == 20

    def test_budget_insight(self, government_df, government_col_mapping):
        result = GovernmentAnalytics.analyze(government_df, government_col_mapping)
        budget = result.get_insight("Total Budget")
        assert budget is not None
        assert budget.value > 0

    def test_contractor_insight(self, government_df, government_col_mapping):
        result = GovernmentAnalytics.analyze(government_df, government_col_mapping)
        assert result.get_insight("Active Contractors").value == 4


class TestRetailAnalytics:
    def test_returns_result(self, retail_df, retail_col_mapping):
        result = RetailAnalytics.analyze(retail_df, retail_col_mapping)
        assert result.industry == "retail"

    def test_sales_insight(self, retail_df, retail_col_mapping):
        result = RetailAnalytics.analyze(retail_df, retail_col_mapping)
        sales = result.get_insight("Total Sales")
        assert sales is not None
        assert sales.value > 0

    def test_customer_insight(self, retail_df, retail_col_mapping):
        result = RetailAnalytics.analyze(retail_df, retail_col_mapping)
        assert result.get_insight("Total Customers").value == 10

    def test_profit_margin(self, retail_df, retail_col_mapping):
        result = RetailAnalytics.analyze(retail_df, retail_col_mapping)
        margin = result.get_insight("Profit Margin")
        assert margin is not None
        assert margin.value > 0

    def test_product_breakdown(self, retail_df, retail_col_mapping):
        result = RetailAnalytics.analyze(retail_df, retail_col_mapping)
        prod_bd = [b for b in result.breakdowns if b.dimension == "Product"]
        assert len(prod_bd) > 0


class TestManufacturingAnalytics:
    def test_returns_result(self, manufacturing_df, manufacturing_col_mapping):
        result = ManufacturingAnalytics.analyze(manufacturing_df, manufacturing_col_mapping)
        assert result.industry == "manufacturing"

    def test_production_insight(self, manufacturing_df, manufacturing_col_mapping):
        result = ManufacturingAnalytics.analyze(manufacturing_df, manufacturing_col_mapping)
        prod = result.get_insight("Total Production")
        assert prod is not None
        assert prod.value > 0

    def test_machine_insight(self, manufacturing_df, manufacturing_col_mapping):
        result = ManufacturingAnalytics.analyze(manufacturing_df, manufacturing_col_mapping)
        assert result.get_insight("Active Machines").value == 5

    def test_downtime_insight(self, manufacturing_df, manufacturing_col_mapping):
        result = ManufacturingAnalytics.analyze(manufacturing_df, manufacturing_col_mapping)
        dt = result.get_insight("Total Downtime")
        assert dt is not None
        assert dt.value > 0

    def test_yield_insight(self, manufacturing_df, manufacturing_col_mapping):
        result = ManufacturingAnalytics.analyze(manufacturing_df, manufacturing_col_mapping)
        yld = result.get_insight("Average Yield Rate")
        assert yld is not None


class TestNGOAnalytics:
    def test_returns_result(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        assert result.industry == "ngo"

    def test_donor_insight(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        assert result.get_insight("Total Donors").value == 8

    def test_beneficiary_insight(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        assert result.get_insight("Beneficiaries Reached").value == 20

    def test_funding_insight(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        funding = result.get_insight("Total Funding")
        assert funding is not None
        assert funding.value > 0

    def test_cost_per_beneficiary(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        cpb = result.get_insight("Cost per Beneficiary")
        assert cpb is not None
        assert cpb.value > 0

    def test_program_breakdown(self, ngo_df, ngo_col_mapping):
        result = NGOAnalytics.analyze(ngo_df, ngo_col_mapping)
        prog_bd = [b for b in result.breakdowns if b.dimension == "Program"]
        assert len(prog_bd) > 0


class TestFullPipeline:
    def test_pipeline_includes_intelligence(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        assert result.industry_intelligence is not None
        assert result.industry_intelligence.industry == "healthcare"

    def test_pipeline_to_dict_includes_intelligence(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        d = result.to_dict()
        assert "industry_intelligence" in d
        assert d["industry_intelligence"] is not None
        assert d["industry_intelligence"]["industry"] == "healthcare"
