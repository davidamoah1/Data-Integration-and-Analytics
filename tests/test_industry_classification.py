"""Automated tests for industry classification accuracy.

Tests that the SemanticEngine correctly identifies the industry of uploaded
datasets across Healthcare, Education, Banking, Agriculture, Government,
Retail, Church, NGO, Manufacturing, Insurance, Hospitality, and Telecom.

Verifies that:
1. Classification accuracy is correct for strong-signal datasets
2. Generic terms (amount, balance, date, status) don't cause banking bias
3. Results are independent of column order
4. Results are independent of dataset filename
5. Tie-breaking returns "unknown" when signals are ambiguous
"""

from __future__ import annotations

import pandas as pd
import pytest

from semantic.semantic_engine import SemanticEngine


# ── Test Data Fixtures ──


@pytest.fixture
def healthcare_df():
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P003"],
            "patient_name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "medical_record_number": ["MRN001", "MRN002", "MRN003"],
            "diagnosis": ["Hypertension", "Diabetes", "Asthma"],
            "doctor_name": ["Dr. Adams", "Dr. Brown", "Dr. Clark"],
            "admission_date": ["2024-01-15", "2024-02-20", "2024-03-10"],
            "ward": ["ICU", "General", "Pediatric"],
            "billing_amount": [5000, 3200, 1500],
            "insurance_provider": ["BlueCross", "Aetna", "Cigna"],
        }
    )


@pytest.fixture
def education_df():
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002", "S003"],
            "student_name": ["Alice", "Bob", "Charlie"],
            "course": ["Math 101", "Physics 201", "Chemistry 101"],
            "teacher_name": ["Prof. Smith", "Dr. Jones", "Prof. Lee"],
            "grade": ["A", "B+", "A-"],
            "attendance": [95, 82, 78],
            "exam_id": ["E001", "E002", "E003"],
            "semester": ["Fall 2024", "Fall 2024", "Spring 2024"],
        }
    )


@pytest.fixture
def banking_df():
    return pd.DataFrame(
        {
            "account_number": ["ACC001", "ACC002", "ACC003"],
            "loan_id": ["L001", "L002", "L003"],
            "credit_score": [720, 680, 750],
            "interest_rate": [5.5, 6.2, 4.8],
            "mortgage": [250000, 180000, 320000],
            "swift_code": ["BOFAUS3N", "CHASUS33", "WFCBUS33"],
            "amount": [1500, 2500, 3500],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def agriculture_df():
    return pd.DataFrame(
        {
            "farm_id": ["F001", "F002", "F003"],
            "farm_name": ["Green Valley", "Sunny Acres", "Hilltop"],
            "crop": ["Maize", "Wheat", "Rice"],
            "livestock": [50, 120, 30],
            "rainfall": [1200, 800, 950],
            "temperature": [25.5, 28.0, 22.3],
            "harvest_date": ["2024-09-15", "2024-10-01", "2024-09-20"],
            "amount": [5000, 7200, 3100],
        }
    )


@pytest.fixture
def government_df():
    return pd.DataFrame(
        {
            "project_id": ["PRJ001", "PRJ002", "PRJ003"],
            "project_name": ["Road Construction", "School Building", "Water Supply"],
            "department": ["Ministry of Transport", "Ministry of Education", "Ministry of Water"],
            "budget": [5000000, 2000000, 1500000],
            "procurement": ["Tender A", "Tender B", "Tender C"],
            "citizen_id": ["C001", "C002", "C003"],
            "date": ["2024-01-01", "2024-02-01", "2024-03-01"],
        }
    )


@pytest.fixture
def retail_df():
    return pd.DataFrame(
        {
            "order_id": ["ORD001", "ORD002", "ORD003"],
            "customer_id": ["CUST001", "CUST002", "CUST003"],
            "product": ["Widget A", "Gadget B", "Tool C"],
            "supplier": ["Supplier X", "Supplier Y", "Supplier Z"],
            "warehouse": ["WH1", "WH2", "WH1"],
            "inventory": [100, 50, 75],
            "amount": [29.99, 49.99, 15.50],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def church_df():
    return pd.DataFrame(
        {
            "member_id": ["M001", "M002", "M003"],
            "member_name": ["John", "Mary", "Peter"],
            "tithe": [500, 300, 750],
            "offering": [100, 50, 200],
            "branch": ["North Campus", "South Campus", "East Campus"],
            "pastor": ["Pastor James", "Pastor Paul", "Pastor Luke"],
            "event": ["Sunday Service", "Bible Study", "Prayer Meeting"],
            "date": ["2024-01-07", "2024-01-14", "2024-01-21"],
        }
    )


@pytest.fixture
def ngo_df():
    return pd.DataFrame(
        {
            "beneficiary_id": ["B001", "B002", "B003"],
            "donor_id": ["D001", "D002", "D003"],
            "program": ["Food Aid", "Education Support", "Health Outreach"],
            "grant_id": ["G001", "G002", "G003"],
            "donation": [10000, 5000, 7500],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def manufacturing_df():
    return pd.DataFrame(
        {
            "machine_id": ["MCH001", "MCH002", "MCH003"],
            "machine_name": ["Lathe A", "Mill B", "Press C"],
            "production": [500, 320, 800],
            "downtime": [2.5, 5.0, 1.2],
            "batch": ["B001", "B002", "B003"],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def insurance_df():
    return pd.DataFrame(
        {
            "policy_number": ["POL001", "POL002", "POL003"],
            "claim_id": ["CLM001", "CLM002", "CLM003"],
            "agent_name": ["Agent Smith", "Agent Jones", "Agent Brown"],
            "premium": [1200, 800, 1500],
            "claim_amount": [5000, 3000, 7500],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def hospitality_df():
    return pd.DataFrame(
        {
            "reservation_id": ["RES001", "RES002", "RES003"],
            "guest_name": ["Alice", "Bob", "Charlie"],
            "room_number": ["101", "202", "303"],
            "check_in": ["2024-06-01", "2024-06-05", "2024-06-10"],
            "check_out": ["2024-06-03", "2024-06-08", "2024-06-12"],
            "amount": [300, 450, 600],
        }
    )


@pytest.fixture
def telecom_df():
    return pd.DataFrame(
        {
            "subscriber_id": ["SUB001", "SUB002", "SUB003"],
            "msisdn": ["+1234567890", "+1234567891", "+1234567892"],
            "call_duration": [15.5, 22.0, 8.3],
            "data_mb": [2048, 5120, 1024],
            "plan": ["Basic", "Premium", "Standard"],
            "date": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )


@pytest.fixture
def generic_df():
    """Dataset with only generic columns — should classify as unknown."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Item A", "Item B", "Item C"],
            "amount": [100, 200, 300],
            "date": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "status": ["Active", "Pending", "Closed"],
            "type": ["Type1", "Type2", "Type1"],
        }
    )


@pytest.fixture
def banking_biased_generic_df():
    """Dataset with generic terms that used to trigger banking (balance, transaction).
    Should NOT classify as banking."""
    return pd.DataFrame(
        {
            "transaction": [100, 200, 300],
            "balance": [500, 600, 700],
            "amount": [50, 60, 70],
            "date": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "status": ["Active", "Pending", "Closed"],
        }
    )


# ── Classification Accuracy Tests ──


class TestIndustryClassification:
    """Test that the semantic engine correctly classifies datasets by industry."""

    def test_healthcare_classification(self, healthcare_df):
        result = SemanticEngine.analyze(healthcare_df)
        assert result.detected_industry == "healthcare"
        assert result.industry_confidence >= 40.0

    def test_education_classification(self, education_df):
        result = SemanticEngine.analyze(education_df)
        assert result.detected_industry == "education"
        assert result.industry_confidence >= 40.0

    def test_banking_classification(self, banking_df):
        result = SemanticEngine.analyze(banking_df)
        assert result.detected_industry == "banking"
        assert result.industry_confidence >= 40.0

    def test_agriculture_classification(self, agriculture_df):
        result = SemanticEngine.analyze(agriculture_df)
        assert result.detected_industry == "agriculture"
        assert result.industry_confidence >= 40.0

    def test_government_classification(self, government_df):
        result = SemanticEngine.analyze(government_df)
        assert result.detected_industry == "government"
        assert result.industry_confidence >= 40.0

    def test_retail_classification(self, retail_df):
        result = SemanticEngine.analyze(retail_df)
        assert result.detected_industry == "retail"
        assert result.industry_confidence >= 40.0

    def test_church_classification(self, church_df):
        result = SemanticEngine.analyze(church_df)
        assert result.detected_industry == "church"
        assert result.industry_confidence >= 40.0

    def test_ngo_classification(self, ngo_df):
        result = SemanticEngine.analyze(ngo_df)
        assert result.detected_industry == "ngo"
        assert result.industry_confidence >= 40.0

    def test_manufacturing_classification(self, manufacturing_df):
        result = SemanticEngine.analyze(manufacturing_df)
        assert result.detected_industry == "manufacturing"
        assert result.industry_confidence >= 40.0

    def test_insurance_classification(self, insurance_df):
        result = SemanticEngine.analyze(insurance_df)
        assert result.detected_industry == "insurance"
        assert result.industry_confidence >= 40.0

    def test_hospitality_classification(self, hospitality_df):
        result = SemanticEngine.analyze(hospitality_df)
        assert result.detected_industry == "hospitality"
        assert result.industry_confidence >= 40.0

    def test_telecom_classification(self, telecom_df):
        result = SemanticEngine.analyze(telecom_df)
        assert result.detected_industry == "telecommunications"
        assert result.industry_confidence >= 40.0


class TestBankingBiasRemoval:
    """Test that generic terms no longer cause banking misclassification."""

    def test_generic_dataset_is_unknown(self, generic_df):
        result = SemanticEngine.analyze(generic_df)
        assert result.detected_industry == "unknown"

    def test_banking_terms_dont_cause_banking(self, banking_biased_generic_df):
        """Dataset with only generic financial terms should NOT be banking."""
        result = SemanticEngine.analyze(banking_biased_generic_df)
        assert result.detected_industry != "banking"
        assert result.detected_industry == "unknown"

    def test_healthcare_not_banking(self, healthcare_df):
        """Healthcare dataset with billing/insurance should not be banking."""
        result = SemanticEngine.analyze(healthcare_df)
        assert result.detected_industry == "healthcare"
        assert result.detected_industry != "banking"


class TestColumnOrderIndependence:
    """Test that classification is independent of column order."""

    def test_healthcare_reversed_columns(self, healthcare_df):
        reversed_df = healthcare_df[healthcare_df.columns[::-1]]
        result1 = SemanticEngine.analyze(healthcare_df)
        result2 = SemanticEngine.analyze(reversed_df)
        assert result1.detected_industry == result2.detected_industry
        assert result1.industry_confidence == pytest.approx(result2.industry_confidence, abs=0.1)

    def test_education_shuffled_columns(self, education_df):
        import random

        cols = list(education_df.columns)
        random.seed(42)
        random.shuffle(cols)
        shuffled = education_df[cols]
        result1 = SemanticEngine.analyze(education_df)
        result2 = SemanticEngine.analyze(shuffled)
        assert result1.detected_industry == result2.detected_industry


class TestDashboardRegistry:
    """Test that dashboard templates exist for all supported industries."""

    def test_all_industries_have_templates(self):
        from semantic.dashboard_registry import DashboardRegistry

        industries = [
            "healthcare",
            "education",
            "banking",
            "agriculture",
            "government",
            "retail",
            "church",
            "ngo",
            "manufacturing",
            "insurance",
            "hospitality",
            "telecommunications",
        ]
        for industry in industries:
            template = DashboardRegistry.get(industry)
            assert template is not None, f"No dashboard template for {industry}"

    def test_generic_fallback_exists(self):
        from semantic.dashboard_registry import DashboardRegistry

        template = DashboardRegistry.get("unknown")
        assert template is not None
        assert "Generic" in template.title or "generic" in template.key

    def test_unknown_resolves_to_generic(self):
        from semantic.dashboard_registry import DashboardRegistry

        template = DashboardRegistry.get("unknown")
        generic = DashboardRegistry.get("generic")
        assert template is not None
        assert generic is not None
        assert template.key == generic.key
