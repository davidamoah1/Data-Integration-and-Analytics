"""Generate synthetic DIRTY CSV datasets for each industry sector.

Creates realistic datasets with real-world data quality issues:
- Duplicate rows (~5%)
- Empty rows (~2%)
- Missing/null values in key columns
- Inconsistent date formats (7 different formats + invalid dates)
- String values in numeric columns ("N/A", "$1,200", "TBD")
- Negative values where they shouldn't be
- Inconsistent casing, extra whitespace in text fields
- Mixed column name casing (Title Case headers)

The ETL transform step and dashboard clean_df will clean these on upload.
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

MESSY_DATES = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m/%d/%y",
    "%B %d, %Y",
    "%d %b %Y",
    "%Y/%m/%d",
]
MESSY_NUMBERS = ["N/A", "TBD", "", "unknown", "null", "-", "N/A"]
MESSY_TEXT = ["", "  ", "N/A", "Unknown", "TBD", "null", "None", "  -  "]


def messy_date(start: datetime, end: datetime) -> str:
    if random.random() < 0.05:
        return random.choice(["", "N/A", "TBD", "0000-00-00", "2024-13-45", "invalid"])
    delta = end - start
    random_days = random.randint(0, delta.days)
    d = start + timedelta(days=random_days)
    fmt = random.choice(MESSY_DATES)
    try:
        return d.strftime(fmt)
    except Exception:
        return d.strftime("%Y-%m-%d")


def messy_number(value: float) -> str:
    r = random.random()
    if r < 0.03:
        return ""
    elif r < 0.05:
        return random.choice(MESSY_NUMBERS)
    elif r < 0.08:
        return f"${value:,.2f}"
    elif r < 0.10:
        return f"{value:.0f}"
    elif r < 0.12:
        return f" {value} "
    elif r < 0.14:
        return str(-abs(value))
    else:
        return str(round(value, 2))


def messy_text(value: str) -> str:
    r = random.random()
    if r < 0.03:
        return ""
    elif r < 0.05:
        return random.choice(MESSY_TEXT)
    elif r < 0.08:
        return f"  {value}  "
    elif r < 0.10:
        return value.upper()
    elif r < 0.12:
        return value.lower()
    elif r < 0.14:
        return f" {value}"
    else:
        return value


def messy_int(value: int) -> str:
    r = random.random()
    if r < 0.03:
        return ""
    elif r < 0.05:
        return random.choice(MESSY_NUMBERS)
    elif r < 0.07:
        return str(-abs(value))
    elif r < 0.09:
        return f"{value}.0"
    else:
        return str(value)


def inject_duplicates(rows: list, rate: float = 0.05) -> list:
    n_dupes = int(len(rows) * rate)
    for _ in range(n_dupes):
        rows.append(dict(random.choice(rows)))
    random.shuffle(rows)
    return rows


def inject_empty_rows(rows: list, rate: float = 0.02) -> list:
    n_empty = int(len(rows) * rate)
    if rows:
        keys = list(rows[0].keys())
        for _ in range(n_empty):
            rows.append({k: "" for k in keys})
    return rows


# ──────────────────────────────────────────────
# Education Dataset — Tuition & Enrollment
# ──────────────────────────────────────────────
def generate_education():
    regions = ["North", "South", "East", "West", "Central"]
    categories = ["Undergraduate", "Graduate", "PhD", "Certificate", "Diploma"]
    departments = ["Engineering", "Business", "Arts", "Sciences", "Medicine", "Law", "Education"]
    student_names = [f"Student_{i:04d}" for i in range(1, 801)]
    payment_methods = ["Cash", "Bank Transfer", "Credit Card", "Scholarship", "Loan"]

    rows = []
    for i in range(1, 801):
        category = random.choice(categories)
        dept = random.choice(departments)

        if category == "Undergraduate":
            tuition = random.uniform(3000, 12000)
        elif category == "Graduate":
            tuition = random.uniform(8000, 20000)
        elif category == "PhD":
            tuition = random.uniform(15000, 35000)
        elif category == "Certificate":
            tuition = random.uniform(500, 3000)
        else:
            tuition = random.uniform(1500, 6000)

        discount = random.choice([0, 0, 0, random.uniform(200, 2000)])
        net_tuition = tuition - discount
        quantity = random.randint(1, 6)
        payment = net_tuition * quantity

        rows.append(
            {
                "Transaction ID": f"TXN{10000 + i}",
                "Date": messy_date(datetime(2022, 1, 1), datetime(2024, 12, 31)),
                "Student Name": messy_text(random.choice(student_names)),
                "Department": messy_text(dept),
                "Program Type": messy_text(category),
                "Region": messy_text(random.choice(regions)),
                "Tuition": messy_number(tuition),
                "Discount": messy_number(discount),
                "Quantity": messy_int(quantity),
                "Payment": messy_number(payment),
                "Payment Method": messy_text(random.choice(payment_methods)),
            }
        )

    rows = inject_duplicates(rows, 0.05)
    rows = inject_empty_rows(rows, 0.02)

    path = os.path.join(OUTPUT_DIR, "Education_Enrollment_Data.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Education (dirty): {len(rows)} rows -> {path}")
    return path


# ──────────────────────────────────────────────
# Healthcare Dataset — Patient Billing
# ──────────────────────────────────────────────
def generate_healthcare():
    regions = ["North", "South", "East", "West", "Central"]
    departments = [
        "Cardiology",
        "Orthopedics",
        "Pediatrics",
        "Oncology",
        "Emergency",
        "Radiology",
        "General",
    ]
    patient_names = [f"Patient_{i:04d}" for i in range(1, 901)]
    service_types = [
        "Consultation",
        "Surgery",
        "Lab Test",
        "Imaging",
        "Therapy",
        "Vaccination",
        "Emergency Care",
    ]
    insurance = ["NHIS", "Private", "Self-Pay", "Corporate"]

    rows = []
    for i in range(1, 901):
        service = random.choice(service_types)

        if service == "Surgery":
            amount = random.uniform(2000, 25000)
        elif service == "Consultation":
            amount = random.uniform(50, 300)
        elif service == "Lab Test":
            amount = random.uniform(20, 500)
        elif service == "Imaging":
            amount = random.uniform(100, 1500)
        elif service == "Therapy":
            amount = random.uniform(80, 600)
        elif service == "Emergency Care":
            amount = random.uniform(200, 5000)
        else:
            amount = random.uniform(10, 100)

        discount = random.choice([0, 0, 0, random.uniform(10, amount * 0.3)])
        net_amount = amount - discount
        quantity = random.randint(1, 4)
        total = net_amount * quantity

        rows.append(
            {
                "Transaction ID": f"HCR{20000 + i}",
                "Date": messy_date(datetime(2022, 1, 1), datetime(2024, 12, 31)),
                "Patient Name": messy_text(random.choice(patient_names)),
                "Department": messy_text(random.choice(departments)),
                "Service Type": messy_text(service),
                "Region": messy_text(random.choice(regions)),
                "Amount": messy_number(amount),
                "Discount": messy_number(discount),
                "Quantity": messy_int(quantity),
                "Total": messy_number(total),
                "Insurance Type": messy_text(random.choice(insurance)),
            }
        )

    rows = inject_duplicates(rows, 0.05)
    rows = inject_empty_rows(rows, 0.02)

    path = os.path.join(OUTPUT_DIR, "Healthcare_Billing_Data.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Healthcare (dirty): {len(rows)} rows -> {path}")
    return path


# ──────────────────────────────────────────────
# Government Dataset — Public Spending
# ──────────────────────────────────────────────
def generate_government():
    regions = ["North", "South", "East", "West", "Central"]
    departments = [
        "Infrastructure",
        "Education",
        "Health",
        "Defense",
        "Agriculture",
        "Energy",
        "Transport",
    ]
    project_types = [
        "Road Construction",
        "School Building",
        "Hospital Project",
        "Water Supply",
        "Rural Electrification",
        "Public Transport",
    ]
    contractors = [f"Contractor_{i:03d}" for i in range(1, 101)]

    rows = []
    for i in range(1, 701):
        project = random.choice(project_types)

        if project == "Road Construction":
            amount = random.uniform(50000, 5000000)
        elif project == "School Building":
            amount = random.uniform(100000, 2000000)
        elif project == "Hospital Project":
            amount = random.uniform(500000, 10000000)
        elif project == "Water Supply":
            amount = random.uniform(20000, 800000)
        elif project == "Rural Electrification":
            amount = random.uniform(100000, 3000000)
        else:
            amount = random.uniform(80000, 1500000)

        discount = random.choice([0, 0, random.uniform(1000, amount * 0.1)])
        net_amount = amount - discount
        quantity = random.randint(1, 12)
        total = net_amount * quantity

        rows.append(
            {
                "Transaction ID": f"GOV{30000 + i}",
                "Date": messy_date(datetime(2022, 1, 1), datetime(2024, 12, 31)),
                "Contractor Name": messy_text(random.choice(contractors)),
                "Department": messy_text(random.choice(departments)),
                "Project Type": messy_text(project),
                "Region": messy_text(random.choice(regions)),
                "Amount": messy_number(amount),
                "Discount": messy_number(discount),
                "Quantity": messy_int(quantity),
                "Total": messy_number(total),
            }
        )

    rows = inject_duplicates(rows, 0.05)
    rows = inject_empty_rows(rows, 0.02)

    path = os.path.join(OUTPUT_DIR, "Government_Spending_Data.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Government (dirty): {len(rows)} rows -> {path}")
    return path


# ──────────────────────────────────────────────
# Church Dataset — Tithes & Offerings
# ──────────────────────────────────────────────
def generate_church():
    regions = ["North", "South", "East", "West", "Central"]
    event_types = [
        "Sunday Service",
        "Midweek Service",
        "Special Program",
        "Conference",
        "Outreach",
        "Building Fund",
    ]
    departments = [
        "Main Sanctuary",
        "Youth Ministry",
        "Children's Church",
        "Music Ministry",
        "Outreach",
        "Administration",
    ]
    member_names = [f"Member_{i:04d}" for i in range(1, 601)]
    payment_methods = ["Cash", "Bank Transfer", "Mobile Money", "Cheque"]

    rows = []
    for i in range(1, 601):
        event = random.choice(event_types)

        if event == "Special Program":
            amount = random.uniform(50, 5000)
        elif event == "Conference":
            amount = random.uniform(100, 3000)
        elif event == "Building Fund":
            amount = random.uniform(200, 10000)
        elif event == "Outreach":
            amount = random.uniform(20, 1000)
        else:
            amount = random.uniform(10, 500)

        quantity = random.randint(1, 4)
        total = amount * quantity

        rows.append(
            {
                "Transaction ID": f"CHC{40000 + i}",
                "Date": messy_date(datetime(2022, 1, 1), datetime(2024, 12, 31)),
                "Member Name": messy_text(random.choice(member_names)),
                "Department": messy_text(random.choice(departments)),
                "Event Type": messy_text(event),
                "Region": messy_text(random.choice(regions)),
                "Amount": messy_number(amount),
                "Discount": messy_number(0),
                "Quantity": messy_int(quantity),
                "Total": messy_number(total),
                "Payment Method": messy_text(random.choice(payment_methods)),
            }
        )

    rows = inject_duplicates(rows, 0.05)
    rows = inject_empty_rows(rows, 0.02)

    path = os.path.join(OUTPUT_DIR, "Church_Tithes_Data.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Church (dirty): {len(rows)} rows -> {path}")
    return path


# ──────────────────────────────────────────────
# NGO Dataset — Donations & Programs
# ──────────────────────────────────────────────
def generate_ngo():
    regions = ["North", "South", "East", "West", "Central", "International"]
    program_types = [
        "Education Support",
        "Health Outreach",
        "Water Project",
        "Food Aid",
        "Shelter",
        "Skills Training",
        "Emergency Relief",
    ]
    donors = [f"Donor_{i:03d}" for i in range(1, 201)]
    funding_sources = ["Individual", "Corporate", "Grant", "Government", "International Aid"]

    rows = []
    for i in range(1, 651):
        program = random.choice(program_types)

        if program == "Water Project":
            amount = random.uniform(5000, 200000)
        elif program == "Shelter":
            amount = random.uniform(10000, 500000)
        elif program == "Emergency Relief":
            amount = random.uniform(20000, 1000000)
        elif program == "Food Aid":
            amount = random.uniform(2000, 100000)
        elif program == "Skills Training":
            amount = random.uniform(1000, 50000)
        elif program == "Health Outreach":
            amount = random.uniform(3000, 150000)
        else:
            amount = random.uniform(1000, 80000)

        discount = random.choice([0, 0, random.uniform(100, amount * 0.05)])
        net_amount = amount - discount
        quantity = random.randint(1, 10)
        total = net_amount * quantity

        rows.append(
            {
                "Transaction ID": f"NGO{50000 + i}",
                "Date": messy_date(datetime(2022, 1, 1), datetime(2024, 12, 31)),
                "Donor Name": messy_text(random.choice(donors)),
                "Program Type": messy_text(program),
                "Region": messy_text(random.choice(regions)),
                "Amount": messy_number(amount),
                "Discount": messy_number(discount),
                "Quantity": messy_int(quantity),
                "Total": messy_number(total),
                "Funding Source": messy_text(random.choice(funding_sources)),
            }
        )

    rows = inject_duplicates(rows, 0.05)
    rows = inject_empty_rows(rows, 0.02)

    path = os.path.join(OUTPUT_DIR, "NGO_Donations_Data.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  NGO (dirty): {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    print("Generating DIRTY sector datasets...")
    print()
    print("Data quality issues injected:")
    print("  - Duplicate rows (~5%)")
    print("  - Empty rows (~2%)")
    print("  - Missing/null values in numeric fields (~3%)")
    print("  - Non-numeric strings in numeric fields (~2%)")
    print("  - Currency-formatted values ($1,200.00) (~2%)")
    print("  - Negative values where invalid (~2%)")
    print("  - Inconsistent date formats (7 different formats)")
    print("  - Invalid dates (~5%)")
    print("  - Extra whitespace in text fields (~5%)")
    print("  - Inconsistent casing in text fields (~4%)")
    print("  - Mixed column name casing (Title Case headers)")
    print()
    generate_education()
    generate_healthcare()
    generate_government()
    generate_church()
    generate_ngo()
    print()
    print("All dirty datasets generated in dataset/ folder.")
    print()
    print("Usage:")
    print("  1. Open the dashboard (http://localhost:8501)")
    print("  2. Switch to 'Upload File' mode in the sidebar")
    print("  3. Upload any of the generated CSV files")
    print("  4. The system will clean the data and show cleaned row count")
    print("  5. Compare original vs cleaned data in the dashboard")
