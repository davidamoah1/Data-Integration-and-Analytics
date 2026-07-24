"""Generate realistic synthetic datasets for RC3 industry validation."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def _date_range(n: int, start: datetime = datetime(2024, 1, 1)) -> list[datetime]:
    return [start + timedelta(days=i) for i in range(n)]


def generate_healthcare(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    diagnoses = ["Hypertension", "Diabetes", "Malaria", "Asthma", "COVID-19", "Fracture", "Pneumonia"]
    wards = ["A", "B", "C", "ICU", "ER"]
    doctors = ["Dr. Smith", "Dr. Doe", "Dr. Lee", "Dr. Brown", "Dr. Patel"]
    insurance = ["Private", "Public", "None"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "patient_id": [f"P{1000 + i}" for i in range(n)],
            "patient_name": [f"Patient_{i}" for i in range(n)],
            "age": rng.integers(1, 90, n),
            "gender": rng.choice(["M", "F"], n),
            "diagnosis": rng.choice(diagnoses, n),
            "admission_date": [d.strftime("%Y-%m-%d") for d in dates],
            "discharge_date": [(d + timedelta(days=int(rng.integers(1, 10)))).strftime("%Y-%m-%d") for d in dates],
            "ward": rng.choice(wards, n),
            "doctor": rng.choice(doctors, n),
            "amount": rng.uniform(50, 5000, n).round(2),
            "insurance_type": rng.choice(insurance, n),
        }
    )


def generate_education(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(43)
    departments = ["Science", "Arts", "Engineering", "Business", "Medicine"]
    courses = ["Math", "Physics", "History", "Economics", "Biology", "CS"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "student_id": [f"S{1000 + i}" for i in range(n)],
            "student_name": [f"Student_{i}" for i in range(n)],
            "grade": rng.choice(["A", "B", "C", "D", "F"], n),
            "department": rng.choice(departments, n),
            "enrollment_date": [d.strftime("%Y-%m-%d") for d in dates],
            "course": rng.choice(courses, n),
            "score": rng.uniform(40, 100, n).round(1),
            "attendance_rate": rng.uniform(0.5, 1.0, n).round(2),
            "graduation_rate": rng.uniform(0.6, 1.0, n).round(2),
        }
    )


def generate_church(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(44)
    branches = ["Main", "North", "South", "East"]
    ministries = ["Youth", "Women", "Men", "Worship", "Outreach"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "member_id": [f"M{1000 + i}" for i in range(n)],
            "member_name": [f"Member_{i}" for i in range(n)],
            "join_date": [d.strftime("%Y-%m-%d") for d in dates],
            "branch": rng.choice(branches, n),
            "ministry": rng.choice(ministries, n),
            "offering_amount": rng.uniform(5, 500, n).round(2),
            "tithe_amount": rng.uniform(10, 1000, n).round(2),
            "visitor_name": rng.choice(["Guest", "Newcomer", "Friend", ""], n),
            "visit_date": [d.strftime("%Y-%m-%d") for d in dates],
        }
    )


def generate_government(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(45)
    departments = ["Health", "Education", "Transport", "Finance", "Agriculture"]
    statuses = ["active", "completed", "delayed"]
    contractors = ["BuildCo", "TechSol", "Infra Ltd", "ConsultPro", "GreenWorks"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "project_id": [f"PRJ{1000 + i}" for i in range(n)],
            "project_name": [f"Project_{i}" for i in range(n)],
            "department": rng.choice(departments, n),
            "budget": rng.uniform(10000, 1000000, n).round(2),
            "spent": rng.uniform(5000, 900000, n).round(2),
            "status": rng.choice(statuses, n),
            "start_date": [d.strftime("%Y-%m-%d") for d in dates],
            "end_date": [(d + timedelta(days=int(rng.integers(30, 365)))).strftime("%Y-%m-%d") for d in dates],
            "contractor": rng.choice(contractors, n),
            "revenue_amount": rng.uniform(1000, 50000, n).round(2),
            "asset_value": rng.uniform(5000, 500000, n).round(2),
        }
    )


def generate_retail(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(46)
    segments = ["Consumer", "Corporate", "Home Office"]
    regions = ["North", "South", "East", "West", "Central"]
    categories = ["Electronics", "Furniture", "Office Supplies", "Clothing", "Food"]
    dates = _date_range(n)
    qty = rng.integers(1, 10, n)
    sales = rng.uniform(10, 1000, n).round(2)
    profit = (sales * rng.uniform(0.05, 0.30, n)).round(2)
    return pd.DataFrame(
        {
            "order_id": [f"ORD{1000 + i}" for i in range(n)],
            "order_date": [d.strftime("%Y-%m-%d") for d in dates],
            "customer_name": [f"Customer_{i}" for i in range(n)],
            "segment": rng.choice(segments, n),
            "region": rng.choice(regions, n),
            "category": rng.choice(categories, n),
            "product_name": [f"Product_{i}" for i in range(n)],
            "sales": sales,
            "quantity": qty,
            "discount": rng.uniform(0, 0.3, n).round(2),
            "profit": profit,
        }
    )


def generate_ngo(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(47)
    locations = ["Urban", "Rural", "Coastal", "Highland"]
    programs = ["Education", "Health", "WASH", "Livelihood", "Protection"]
    statuses = ["active", "graduated", "dropped"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "beneficiary_id": [f"BEN{1000 + i}" for i in range(n)],
            "name": [f"Beneficiary_{i}" for i in range(n)],
            "location": rng.choice(locations, n),
            "program_id": [f"PGM{i % 5}" for i in range(n)],
            "program_name": rng.choice(programs, n),
            "donation_amount": rng.uniform(10, 5000, n).round(2),
            "donor_id": [f"DON{100 + i % 50}" for i in range(n)],
            "donor_name": [f"Donor_{i % 50}" for i in range(n)],
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "status": rng.choice(statuses, n),
        }
    )


def generate_manufacturing(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(48)
    machines = [f"MCH_{i % 10}" for i in range(n)]
    products = ["Widget", "Gadget", "Tool", "Component", "Assembly"]
    statuses = ["running", "running", "running", "running", "down", "maintenance"]
    dates = _date_range(n)
    units = rng.integers(50, 500, n)
    good = (units * rng.uniform(0.85, 0.99, n)).astype(int)
    return pd.DataFrame(
        {
            "machine_id": machines,
            "machine_name": machines,
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "production_volume": units,
            "units_produced": units,
            "downtime_hours": rng.uniform(0, 4, n).round(2),
            "status": rng.choice(statuses, n),
            "good_units": good,
            "total_units": units,
            "product_name": rng.choice(products, n),
        }
    )


def generate_banking(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(49)
    types = ["debit", "credit", "transfer", "withdrawal", "deposit"]
    account_types = ["savings", "checking", "business"]
    branches = ["B001", "B002", "B003", "B004"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "account_id": [f"ACC{1000 + i}" for i in range(n)],
            "customer_id": [f"CUST{1000 + i}" for i in range(n)],
            "account_type": rng.choice(account_types, n),
            "balance": rng.uniform(100, 100000, n).round(2),
            "transaction_id": [f"TXN{10000 + i}" for i in range(n)],
            "amount": rng.uniform(10, 5000, n).round(2),
            "transaction_type": rng.choice(types, n),
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "branch_id": rng.choice(branches, n),
        }
    )


def generate_insurance(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(50)
    statuses = ["approved", "pending", "rejected"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "policy_id": [f"POL{1000 + i}" for i in range(n)],
            "customer_id": [f"CUST{1000 + i}" for i in range(n)],
            "premium": rng.uniform(100, 2000, n).round(2),
            "coverage_amount": rng.uniform(10000, 500000, n).round(2),
            "claim_id": [f"CLM{10000 + i}" for i in range(n)],
            "claim_amount": rng.uniform(100, 50000, n).round(2),
            "status": rng.choice(statuses, n),
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "agent_id": [f"AGT{100 + i % 20}" for i in range(n)],
        }
    )


def generate_agriculture(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(51)
    crops = ["Maize", "Rice", "Wheat", "Beans", "Cassava"]
    livestock_types = ["Cattle", "Goat", "Sheep", "Poultry"]
    farms = [f"Farm_{i % 20}" for i in range(n)]
    dates = _date_range(n)
    hectares = rng.uniform(1, 50, n).round(2)
    harvest = hectares * rng.uniform(500, 3000, n)
    return pd.DataFrame(
        {
            "farm_id": farms,
            "farm_name": farms,
            "crop": rng.choice(crops, n),
            "harvest_kg": harvest.round(2),
            "hectares": hectares,
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "rainfall_mm": rng.uniform(0, 50, n).round(2),
            "temperature_c": rng.uniform(20, 35, n).round(1),
            "livestock_type": rng.choice(livestock_types, n),
            "livestock_count": rng.integers(0, 200, n),
        }
    )


def generate_hospitality(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(52)
    room_types = ["Standard", "Deluxe", "Suite", "Family"]
    services = ["Spa", "Restaurant", "Minibar", "Laundry"]
    dates = _date_range(n)
    check_in = [d + timedelta(days=int(rng.integers(0, 30))) for d in dates]
    nights = rng.integers(1, 7, n)
    return pd.DataFrame(
        {
            "reservation_id": [f"RES{1000 + i}" for i in range(n)],
            "guest_id": [f"GST{1000 + i}" for i in range(n)],
            "guest_name": [f"Guest_{i}" for i in range(n)],
            "room_id": [f"RM{100 + i % 50}" for i in range(n)],
            "room_type": rng.choice(room_types, n),
            "check_in": [d.strftime("%Y-%m-%d") for d in check_in],
            "check_out": [(d + timedelta(days=int(n))).strftime("%Y-%m-%d") for d, n in zip(check_in, nights, strict=False)],
            "nights": nights,
            "amount": rng.uniform(50, 1000, n).round(2),
            "service_type": rng.choice(services, n),
            "date": [d.strftime("%Y-%m-%d") for d in dates],
        }
    )


def generate_telecommunications(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(53)
    plans = ["Basic", "Standard", "Premium", "Unlimited"]
    dates = _date_range(n)
    return pd.DataFrame(
        {
            "subscriber_id": [f"SUB{1000 + i}" for i in range(n)],
            "plan_id": [f"PLN{i % 4}" for i in range(n)],
            "plan_name": rng.choice(plans, n),
            "call_id": [f"CALL{10000 + i}" for i in range(n)],
            "duration_minutes": rng.uniform(0.5, 60, n).round(2),
            "data_mb": rng.uniform(0, 2000, n).round(2),
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "tower_id": [f"TWR{100 + i % 30}" for i in range(n)],
            "cost": rng.uniform(0.1, 10, n).round(2),
        }
    )


GENERATORS = {
    "healthcare": generate_healthcare,
    "education": generate_education,
    "church": generate_church,
    "government": generate_government,
    "retail": generate_retail,
    "ngo": generate_ngo,
    "manufacturing": generate_manufacturing,
    "banking": generate_banking,
    "insurance": generate_insurance,
    "agriculture": generate_agriculture,
    "hospitality": generate_hospitality,
    "telecommunications": generate_telecommunications,
}


def generate_all(output_dir: str | None = None) -> dict[str, str]:
    """Generate all RC3 datasets and return a manifest of paths."""
    base = Path(__file__).resolve().parent.parent / "dataset" / "industries"
    if output_dir:
        base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    manifest = {}
    for name, generator in GENERATORS.items():
        df = generator()
        path = base / f"{name}.csv"
        df.to_csv(path, index=False)
        manifest[name] = str(path)
        print(f"Generated {name}: {len(df)} rows -> {path}")
    return manifest


if __name__ == "__main__":
    generate_all()
