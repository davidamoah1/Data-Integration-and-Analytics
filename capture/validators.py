"""Smart Validation Engine for the Smart Data Capture platform.

Validates extracted field values per data type, suggests standardized
spellings for known vocabularies (drug names, common diagnoses) via fuzzy
matching, and detects likely duplicate document submissions.
"""

from __future__ import annotations

import difflib
import re
from datetime import datetime

from sqlalchemy.orm import Session as DbSession

# Small illustrative master lists. In production these would be loaded from
# a maintained formulary / ICD-10 table; kept inline here so validation works
# out of the box without extra data files.
DRUG_MASTER_LIST = [
    "Paracetamol",
    "Amoxicillin",
    "Ibuprofen",
    "Artesunate",
    "Metformin",
    "Amlodipine",
    "Ciprofloxacin",
    "Diclofenac",
    "Omeprazole",
    "Cotrimoxazole",
    "Chloroquine",
    "Artemether",
    "Lumefantrine",
    "Furosemide",
    "Hydrochlorothiazide",
    "Insulin",
    "Aspirin",
    "Atorvastatin",
    "Losartan",
    "Metronidazole",
]

DIAGNOSIS_MASTER_LIST = [
    "Malaria",
    "Hypertension",
    "Diabetes Mellitus",
    "Pneumonia",
    "Typhoid Fever",
    "Urinary Tract Infection",
    "Anemia",
    "Asthma",
    "Gastroenteritis",
    "Tuberculosis",
    "Upper Respiratory Tract Infection",
    "Peptic Ulcer Disease",
    "Sickle Cell Disease",
]

GENDER_VALUES = {"m": "Male", "male": "Male", "f": "Female", "female": "Female"}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d %b %Y",
    "%d %B %Y",
]


def validate_age(value: str) -> tuple[bool, str | None]:
    cleaned = re.sub(r"[^\d]", "", value or "")
    if not cleaned:
        return False, "Age must be numeric."
    age = int(cleaned)
    if age < 0 or age > 130:
        return False, f"Age {age} is out of plausible range."
    return True, None


def validate_date(value: str) -> tuple[bool, str | None]:
    value = (value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True, None
        except ValueError:
            continue
    return False, "Date could not be parsed. Expected a recognizable date format."


def validate_gender(value: str) -> tuple[bool, str | None]:
    normalized = (value or "").strip().lower()
    if normalized in GENDER_VALUES:
        return True, None
    return False, "Gender/Sex must be one of M, F, Male, Female."


def validate_phone(value: str) -> tuple[bool, str | None]:
    digits = re.sub(r"[^\d+]", "", value or "")
    if len(re.sub(r"\D", "", digits)) < 7:
        return False, "Phone number is too short to be valid."
    return True, None


def validate_email(value: str) -> tuple[bool, str | None]:
    if not EMAIL_RE.match((value or "").strip()):
        return False, "Email address syntax is invalid."
    return True, None


def validate_currency(value: str) -> tuple[bool, str | None]:
    cleaned = re.sub(r"[^\d.]", "", value or "")
    if not cleaned:
        return False, "Amount must contain a numeric value."
    try:
        float(cleaned)
    except ValueError:
        return False, "Amount could not be parsed as a number."
    return True, None


def suggest_standard_spelling(
    value: str, master_list: list[str], cutoff: float = 0.72
) -> str | None:
    """Return the closest master-list match if similarity is high enough,
    else None (never silently overwrite — this is a suggestion only)."""
    if not value:
        return None
    matches = difflib.get_close_matches(value.strip(), master_list, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def validate_gpa(value: str) -> tuple[bool, str | None]:
    """Validate GPA/CGPA is within a plausible range (0-10)."""
    cleaned = re.sub(r"[^\d.]", "", value or "")
    if not cleaned:
        return False, "GPA must be numeric."
    # Check for negative sign in original value
    if "-" in (value or ""):
        return False, "GPA cannot be negative."
    try:
        gpa = float(cleaned)
    except ValueError:
        return False, "GPA could not be parsed as a number."
    if gpa < 0 or gpa > 10:
        return False, f"GPA {gpa} is outside the valid range (0-10)."
    return True, None


def validate_certificate_dates(
    date_issued: str | None, expiry_date: str | None
) -> tuple[bool, str | None]:
    """Validate that expiry date is not before issue date."""
    if not date_issued or not expiry_date:
        return True, None
    issued_dt = None
    expiry_dt = None
    for fmt in DATE_FORMATS:
        try:
            issued_dt = datetime.strptime(date_issued.strip(), fmt)
            break
        except ValueError:
            continue
    for fmt in DATE_FORMATS:
        try:
            expiry_dt = datetime.strptime(expiry_date.strip(), fmt)
            break
        except ValueError:
            continue
    if issued_dt and expiry_dt and expiry_dt < issued_dt:
        return False, "Expiry date cannot be before the issue date."
    return True, None


VALIDATORS_BY_TYPE = {
    "number": None,  # handled specially per-field (age vs generic number)
    "date": validate_date,
    "phone": validate_phone,
    "email": validate_email,
    "currency": validate_currency,
}


def validate_field(
    field_name: str, value: str | None, data_type: str, enum_values: list[str] | None = None
) -> tuple[bool, str | None]:
    """Validate a single field value based on its declared data type.

    Returns (is_valid, message). A None/empty value is treated as valid here
    (required-ness is enforced separately) since blank fields should be
    flagged as low-confidence/missing rather than "invalid".
    """
    if value is None or str(value).strip() == "":
        return True, None

    if field_name in ("age",):
        return validate_age(value)

    if field_name in ("gpa", "cgpa"):
        return validate_gpa(value)

    if field_name in ("sex", "gender") or (
        enum_values and {"m", "f"} <= {v.lower() for v in enum_values}
    ):
        return validate_gender(value)

    validator = VALIDATORS_BY_TYPE.get(data_type)
    if validator:
        return validator(value)

    if enum_values:
        if value.strip().lower() not in {v.lower() for v in enum_values}:
            return False, f"Value must be one of: {', '.join(enum_values)}."
        return True, None

    return True, None


def find_duplicate_document(
    db: DbSession,
    organization_id: int,
    document_type: str | None,
    fields: dict[str, str],
) -> int | None:
    """Look for an existing approved/ready document of the same type in the
    same org whose key identifying fields match closely. Returns the
    matching document id, or None.

    Uses a lightweight heuristic: same document_type + same value for the
    first "name"-like field + same date-like field, if present.
    """
    from capture.models import CaptureDocument, CaptureField

    if not document_type:
        return None

    name_value = None
    date_value = None
    cert_number_value = None
    for key, value in fields.items():
        if not value:
            continue
        if "name" in key and name_value is None:
            name_value = value.strip().lower()
        if (
            key
            in (
                "date",
                "admission_date",
                "delivery_date",
                "service_date",
                "date_awarded",
                "date_issued",
                "graduation_date",
            )
            and date_value is None
        ):
            date_value = value.strip().lower()
        if (
            key
            in (
                "certificate_number",
                "license_number",
                "serial_number",
                "registration_number",
                "credential_id",
            )
            and cert_number_value is None
        ):
            cert_number_value = value.strip().lower()

    # For certificates, a matching certificate number is strong evidence of a duplicate
    if cert_number_value:
        cert_candidates = (
            db.query(CaptureDocument)
            .filter(
                CaptureDocument.organization_id == organization_id,
                CaptureDocument.status.in_(["ready_for_review", "approved"]),
            )
            .order_by(CaptureDocument.id.desc())
            .limit(200)
            .all()
        )
        for candidate in cert_candidates:
            cert_fields = (
                db.query(CaptureField)
                .filter(
                    CaptureField.document_id == candidate.id,
                    CaptureField.field_name.in_(
                        [
                            "certificate_number",
                            "license_number",
                            "serial_number",
                            "registration_number",
                            "credential_id",
                        ]
                    ),
                )
                .all()
            )
            for cf in cert_fields:
                if cf.value and cf.value.strip().lower() == cert_number_value:
                    return candidate.id

    if not name_value:
        return None

    candidates = (
        db.query(CaptureDocument)
        .filter(
            CaptureDocument.organization_id == organization_id,
            CaptureDocument.document_type == document_type,
            CaptureDocument.status.in_(["ready_for_review", "approved"]),
        )
        .order_by(CaptureDocument.id.desc())
        .limit(200)
        .all()
    )

    for candidate in candidates:
        candidate_fields = (
            db.query(CaptureField)
            .filter(
                CaptureField.document_id == candidate.id, CaptureField.field_name.like("%name%")
            )
            .all()
        )
        for cf in candidate_fields:
            if cf.value and cf.value.strip().lower() == name_value:
                if date_value:
                    date_field = (
                        db.query(CaptureField)
                        .filter(
                            CaptureField.document_id == candidate.id,
                            CaptureField.field_name.in_(
                                ["date", "admission_date", "delivery_date", "service_date"]
                            ),
                        )
                        .first()
                    )
                    if (
                        date_field
                        and date_field.value
                        and date_field.value.strip().lower() == date_value
                    ):
                        return candidate.id
                else:
                    return candidate.id

    return None
