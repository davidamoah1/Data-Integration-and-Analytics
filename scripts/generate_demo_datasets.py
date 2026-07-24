"""Generate realistic demo datasets for all 12 supported industries.

Each dataset contains 200 rows with industry-specific columns that will
trigger correct semantic entity mapping and industry detection.

Usage:
    python scripts/generate_demo_datasets.py
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "demo_datasets")


def _dates(n: int = 200, start: str = "2024-01-01") -> list[str]:
    base = datetime.strptime(start, "%Y-%m-%d")
    return [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]


def generate_healthcare() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": range(1, 201),
            "patient_name": [f"Patient {i:03d}" for i in range(1, 201)],
            "doctor": [random.choice(["Dr. Smith", "Dr. Jones", "Dr. Lee", "Dr. Patel"]) for _ in range(200)],
            "admission_date": _dates(),
            "ward": [random.choice(["ICU", "General", "Pediatric", "Emergency", "Maternity"]) for _ in range(200)],
            "diagnosis": [random.choice(["Flu", "Diabetes", "Hypertension", "Fracture", "Asthma"]) for _ in range(200)],
            "medicine": [f"Med-{i:03d}" for i in range(1, 201)],
            "lab_test": [random.choice(["Blood Test", "X-Ray", "MRI", "Urine Test", "ECG"]) for _ in range(200)],
            "billing": [random.randint(500, 15000) for _ in range(200)],
            "insurance": [random.choice(["Aetna", "Cigna", "Blue Cross", "United", "None"]) for _ in range(200)],
        }
    )


def generate_education() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": range(1, 201),
            "student_name": [f"Student {i:03d}" for i in range(1, 201)],
            "teacher": [f"Teacher {i % 20 + 1:02d}" for i in range(200)],
            "course": [random.choice(["Math", "Science", "English", "History", "Art"]) for _ in range(200)],
            "department": [random.choice(["Engineering", "Arts", "Science", "Business"]) for _ in range(200)],
            "attendance": [random.randint(60, 100) for _ in range(200)],
            "exam": [f"Exam-{i:03d}" for i in range(1, 201)],
            "grade": [random.choice(["A", "B", "C", "D", "F"]) for _ in range(200)],
            "fee": [random.randint(100, 5000) for _ in range(200)],
            "enrollment_date": _dates(),
        }
    )


def generate_church() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "member_id": range(1, 201),
            "member_name": [f"Member {i:03d}" for i in range(1, 201)],
            "visitor": [f"Visitor {i:03d}" for i in range(1, 201)],
            "branch": [random.choice(["Branch A", "Branch B", "Branch C", "Branch D"]) for _ in range(200)],
            "ministry": [random.choice(["Youth", "Music", "Outreach", "Ushering", "Prayer"]) for _ in range(200)],
            "tithe": [random.randint(10, 1000) for _ in range(200)],
            "offering": [random.randint(5, 500) for _ in range(200)],
            "event": [random.choice(["Service", "Bible Study", "Concert", "Charity Drive"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_retail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": range(1, 201),
            "customer": [f"Customer {i:03d}" for i in range(1, 201)],
            "product": [random.choice(["Laptop", "Phone", "Tablet", "Monitor", "Keyboard"]) for _ in range(200)],
            "supplier": [f"Supplier {i % 10 + 1:02d}" for i in range(200)],
            "inventory": [random.randint(0, 500) for _ in range(200)],
            "sales": [random.randint(100, 10000) for _ in range(200)],
            "region": [random.choice(["North", "South", "East", "West", "Central"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_government() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "project_id": range(1, 201),
            "project_name": [f"Gov Project {i:03d}" for i in range(1, 201)],
            "department": [random.choice(["Works", "Health", "Education", "Defense", "Agriculture"]) for _ in range(200)],
            "budget": [random.randint(10000, 5000000) for _ in range(200)],
            "procurement": [f"Tender-{i:04d}" for i in range(1, 201)],
            "citizen": [f"Citizen {i:05d}" for i in range(1, 201)],
            "revenue": [random.randint(5000, 2000000) for _ in range(200)],
            "asset": [f"Asset-{i:04d}" for i in range(1, 201)],
            "date": _dates(),
        }
    )


def generate_ngo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "beneficiary_id": range(1, 201),
            "beneficiary_name": [f"Beneficiary {i:03d}" for i in range(1, 201)],
            "donor": [random.choice(["USAID", "UNICEF", "Red Cross", "Gates Foundation", "WHO"]) for _ in range(200)],
            "program": [random.choice(["Health", "Education", "Water", "Food Security", "Shelter"]) for _ in range(200)],
            "project": [f"Project-{i:04d}" for i in range(1, 201)],
            "donation": [random.randint(100, 50000) for _ in range(200)],
            "grant": [f"Grant-{i:04d}" for i in range(1, 201)],
            "region": [random.choice(["Africa", "Asia", "Latin America", "Middle East"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_banking() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "account_id": range(1, 201),
            "account_number": [f"ACC{i:06d}" for i in range(1, 201)],
            "transaction_id": range(1001, 1201),
            "loan_id": [f"LN{i:05d}" for i in range(1, 201)],
            "card": [random.choice(["Visa", "Mastercard", "Amex", "Discover"]) for _ in range(200)],
            "balance": [random.randint(100, 1000000) for _ in range(200)],
            "amount": [random.randint(10, 50000) for _ in range(200)],
            "branch": [random.choice(["Downtown", "Uptown", "Midtown", "Suburb"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_manufacturing() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "machine_id": range(1, 201),
            "machine_name": [f"Machine-{i:03d}" for i in range(1, 201)],
            "production_id": range(1001, 1201),
            "output": [random.randint(100, 5000) for _ in range(200)],
            "downtime": [random.randint(0, 120) for _ in range(200)],
            "product": [random.choice(["Widget A", "Widget B", "Component X", "Part Y"]) for _ in range(200)],
            "operator": [f"Operator {i % 15 + 1:02d}" for i in range(200)],
            "date": _dates(),
        }
    )


def generate_agriculture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "farm_id": range(1, 201),
            "farm_name": [f"Farm-{i:03d}" for i in range(1, 201)],
            "crop": [random.choice(["Maize", "Rice", "Wheat", "Soybean", "Cotton"]) for _ in range(200)],
            "harvest": [random.randint(500, 50000) for _ in range(200)],
            "livestock": [random.randint(10, 500) for _ in range(200)],
            "rainfall": [random.randint(200, 2000) for _ in range(200)],
            "temperature": [round(random.uniform(15, 40), 1) for _ in range(200)],
            "fertilizer": [random.choice(["NPK", "Urea", "Compost", "DAP"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_insurance() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "policy_id": range(1, 201),
            "policy_number": [f"POL{i:06d}" for i in range(1, 201)],
            "claim_id": range(1001, 1201),
            "agent": [f"Agent {i % 10 + 1:02d}" for i in range(200)],
            "premium": [random.randint(100, 10000) for _ in range(200)],
            "claim_amount": [random.randint(0, 50000) for _ in range(200)],
            "coverage": [random.choice(["Auto", "Home", "Life", "Health", "Travel"]) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_hospitality() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reservation_id": range(1, 201),
            "guest": [f"Guest {i:03d}" for i in range(1, 201)],
            "room": [random.choice(["Single", "Double", "Suite", "Deluxe", "Presidential"]) for _ in range(200)],
            "booking": [f"Booking-{i:04d}" for i in range(1, 201)],
            "service": [random.choice(["Spa", "Restaurant", "Minibar", "Laundry", "Room Service"]) for _ in range(200)],
            "amount": [random.randint(100, 5000) for _ in range(200)],
            "nights": [random.randint(1, 14) for _ in range(200)],
            "date": _dates(),
        }
    )


def generate_telecom() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subscriber_id": range(1, 201),
            "phone_number": [f"+1234567{i:04d}" for i in range(1, 201)],
            "call_id": range(1001, 1201),
            "plan": [random.choice(["Basic", "Premium", "Unlimited", "Family", "Business"]) for _ in range(200)],
            "data_usage": [random.randint(100, 50000) for _ in range(200)],
            "minutes": [random.randint(10, 2000) for _ in range(200)],
            "sms": [random.randint(0, 500) for _ in range(200)],
            "date": _dates(),
        }
    )


GENERATORS = {
    "healthcare": generate_healthcare,
    "education": generate_education,
    "church": generate_church,
    "retail": generate_retail,
    "government": generate_government,
    "ngo": generate_ngo,
    "banking": generate_banking,
    "manufacturing": generate_manufacturing,
    "agriculture": generate_agriculture,
    "insurance": generate_insurance,
    "hospitality": generate_hospitality,
    "telecommunications": generate_telecom,
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for industry, gen in GENERATORS.items():
        df = gen()
        path = os.path.join(OUT_DIR, f"{industry}_demo.csv")
        df.to_csv(path, index=False)
        print(f"  {industry:20s} -> {path}  ({len(df)} rows, {len(df.columns)} cols)")


if __name__ == "__main__":
    main()
