"""Data privacy detection for tabular datasets.

Provides regex and heuristic-based detection of common personally identifiable
information (PII) and sensitive data categories. The results are used to assign
classification levels and warn users before publishing dashboards or reports.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class SensitivityCategory(str, Enum):
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    GOVERNMENT_ID = "government_id"
    FINANCIAL = "financial"
    HEALTH = "health"
    LOCATION = "location"


# Regex patterns for common sensitive values. These are intentionally conservative
# (focused on reducing false negatives) and should be combined with column-name
# heuristics for higher confidence.
_PATTERNS = {
    SensitivityCategory.EMAIL: re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE
    ),
    SensitivityCategory.PHONE: re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
        re.IGNORECASE,
    ),
    # Very loose numeric ID pattern â€” catches passport, national ID, SSN-like values
    SensitivityCategory.GOVERNMENT_ID: re.compile(
        r"\b\d{6,}\b",
        re.IGNORECASE,
    ),
    # Credit/debit card-like numbers (16 digits with optional spaces/dashes)
    SensitivityCategory.FINANCIAL: re.compile(
        r"(?:\d{4}[-\s]?){3}\d{4}",
        re.IGNORECASE,
    ),
}

# Column-name heuristics. Keys are sensitivity categories; values are lists of
# substrings that strongly indicate the category when present in a column name.
_COLUMN_NAME_HINTS = {
    SensitivityCategory.NAME: [
        "name",
        "first_name",
        "last_name",
        "full_name",
        "surname",
        "given_name",
        "middle_name",
    ],
    SensitivityCategory.EMAIL: ["email", "e_mail", "mail"],
    SensitivityCategory.PHONE: [
        "phone",
        "mobile",
        "cell",
        "telephone",
        "contact",
        "fax",
    ],
    SensitivityCategory.ADDRESS: [
        "address",
        "street",
        "city",
        "zip",
        "postal",
        "state",
        "country",
        "residence",
    ],
    SensitivityCategory.GOVERNMENT_ID: [
        "ssn",
        "social",
        "passport",
        "national_id",
        "id_number",
        "license",
        "nin",
        "tax_id",
        "tin",
        " voter",
    ],
    SensitivityCategory.FINANCIAL: [
        "credit",
        "debit",
        "card",
        "account_number",
        "iban",
        "swift",
        "routing",
        "salary",
        "income",
        "balance",
    ],
    SensitivityCategory.HEALTH: [
        "diagnosis",
        "condition",
        "patient",
        "medical",
        "health",
        "treatment",
        "medication",
        "drug",
    ],
    SensitivityCategory.LOCATION: [
        "latitude",
        "longitude",
        "lat",
        "lng",
        "gps",
        "coordinates",
        "location",
    ],
}


def _column_name_hints(column: str) -> set[SensitivityCategory]:
    """Return sensitivity categories suggested by the column name."""
    lowered = column.lower().replace(" ", "_")
    matched: set[SensitivityCategory] = set()
    for category, hints in _COLUMN_NAME_HINTS.items():
        for hint in hints:
            if hint in lowered:
                matched.add(category)
                break
    return matched


def _sample_values(series: Any, max_rows: int = 1000) -> list[Any]:
    """Return a representative sample of non-null values from a pandas-like series."""
    values = series.dropna().astype(str).tolist()
    if len(values) > max_rows:
        # Take the first rows and a few from later in the dataset to catch
        # formatting variations.
        step = max(1, len(values) // max_rows)
        return values[::step][:max_rows]
    return values


def detect_sensitive_columns(df: Any) -> dict[str, list[SensitivityCategory]]:
    """Inspect a DataFrame and flag columns that likely contain sensitive data.

    Args:
        df: A pandas DataFrame.

    Returns:
        Mapping of column name -> list of detected sensitivity categories.
    """
    flagged: dict[str, list[SensitivityCategory]] = {}

    for column in df.columns:
        categories: set[SensitivityCategory] = _column_name_hints(column)

        values = _sample_values(df[column])
        if not values:
            continue

        # Check regex patterns against a concatenated sample of values.
        sample_text = "\n".join(str(v) for v in values[:200])

        if SensitivityCategory.EMAIL not in categories and _PATTERNS[
            SensitivityCategory.EMAIL
        ].search(sample_text):
            categories.add(SensitivityCategory.EMAIL)

        if SensitivityCategory.PHONE not in categories and _PATTERNS[
            SensitivityCategory.PHONE
        ].search(sample_text):
            categories.add(SensitivityCategory.PHONE)

        # Only flag numeric IDs / financial values if the column name also hints
        # at that category, to avoid false positives on ordinary numbers.
        name_hints = _column_name_hints(column)
        if SensitivityCategory.GOVERNMENT_ID in name_hints:
            categories.add(SensitivityCategory.GOVERNMENT_ID)
        if SensitivityCategory.FINANCIAL in name_hints:
            categories.add(SensitivityCategory.FINANCIAL)

        # Address and location are currently heuristic-only via column names.
        if SensitivityCategory.ADDRESS in name_hints:
            categories.add(SensitivityCategory.ADDRESS)
        if SensitivityCategory.LOCATION in name_hints:
            categories.add(SensitivityCategory.LOCATION)

        if categories:
            flagged[column] = sorted(categories, key=lambda c: c.value)

    return flagged


def has_sensitive_data(df: Any) -> bool:
    """Return True if any column is flagged as sensitive."""
    return bool(detect_sensitive_columns(df))
