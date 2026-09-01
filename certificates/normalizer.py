"""Field normalization for certificate intelligence.

Normalizes extracted field values (names, dates, GPAs, certificate numbers)
without fabricating data.  The original OCR value is always preserved in
``CaptureField.raw_value``; the normalized value is stored in
``CaptureField.value``.

All functions are pure: they take a raw string and return a normalized
string (or the original if normalization is not applicable).  They never
invent values that are not present in the input.
"""

from __future__ import annotations

import re
from datetime import datetime

# â”€â”€ Name normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def normalize_name(raw: str | None) -> str | None:
    """Normalize a person or institution name.

    - Trims surrounding whitespace.
    - Collapses internal multiple spaces.
    - Applies title-case for names that are all UPPER or all lower.
    - Preserves mixed-case names (e.g. "McDonald", "O'Brien") as-is.
    """
    if not raw:
        return raw
    value = re.sub(r"\s+", " ", raw).strip()
    if not value:
        return value
    # Only title-case when the entire string is uniform case.
    if value == value.upper() or value == value.lower():
        return value.title()
    return value


# â”€â”€ Date normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


_DATE_FORMATS = [
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
    "%B %d, %Y",  # January 15, 2024
    "%d %B %Y",  # 15 January 2024
    "%b %d, %Y",  # Jan 15, 2024
    "%d %b %Y",  # 15 Jan 2024
]


def normalize_date(raw: str | None) -> str | None:
    """Normalize a date string to ISO 8601 (YYYY-MM-DD).

    Returns the original string if parsing fails â€” never fabricates a date.
    """
    if not raw:
        return raw
    cleaned = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Try regex extraction for embedded dates.
    m = re.search(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", cleaned)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = "20" + y if int(y) <= 50 else "19" + y
        try:
            dt = datetime(int(y), int(mo), int(d))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return cleaned  # return original if we cannot parse


# â”€â”€ GPA / CGPA normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def normalize_gpa(raw: str | None) -> str | None:
    """Normalize a GPA/CGPA value to a float string with 2 decimals.

    Returns the original if parsing fails.
    """
    if not raw:
        return raw
    cleaned = raw.strip()
    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        try:
            val = float(m.group(1))
            if 0 <= val <= 10:
                return f"{val:.2f}"
        except ValueError:
            pass
    return cleaned


# â”€â”€ Certificate / license number normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def normalize_certificate_number(raw: str | None) -> str | None:
    """Normalize a certificate or license number.

    - Strips whitespace.
    - Converts to uppercase.
    - Removes common surrounding punctuation.
    """
    if not raw:
        return raw
    value = raw.strip().upper()
    value = value.strip(".,;:-")
    return value if value else raw


# â”€â”€ Grade / class normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


_GRADE_MAP = {
    "first class": "First Class",
    "first class honours": "First Class Honours",
    "second class upper": "Second Class Upper",
    "second class lower": "Second Class Lower",
    "third class": "Third Class",
    "pass": "Pass",
    "distinction": "Distinction",
    "merit": "Merit",
    "credit": "Credit",
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "e": "E",
    "f": "F",
}


def normalize_grade(raw: str | None) -> str | None:
    """Normalize a grade/class string to a canonical form.

    Returns the original if no mapping is found.
    """
    if not raw:
        return raw
    key = raw.strip().lower()
    return _GRADE_MAP.get(key, raw.strip())


# â”€â”€ Dispatch table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


_NORMALIZERS: dict[str, callable] = {
    "full_name": normalize_name,
    "student_name": normalize_name,
    "institution": normalize_name,
    "course": normalize_name,
    "programme": normalize_name,
    "program": normalize_name,
    "qualification": normalize_name,
    "date_awarded": normalize_date,
    "graduation_date": normalize_date,
    "date_issued": normalize_date,
    "expiry_date": normalize_date,
    "gpa": normalize_gpa,
    "certificate_number": normalize_certificate_number,
    "license_number": normalize_certificate_number,
    "member_id": normalize_certificate_number,
    "grade": normalize_grade,
}


def normalize_field(field_name: str, raw_value: str | None) -> str | None:
    """Dispatch to the appropriate normalizer based on field name.

    If no specific normalizer exists, the raw value is returned unchanged.
    """
    normalizer = _NORMALIZERS.get(field_name)
    if normalizer and raw_value:
        return normalizer(raw_value)
    return raw_value
