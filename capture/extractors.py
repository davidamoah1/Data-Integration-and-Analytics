"""Field and table extraction for the Smart Data Capture platform.

Two complementary strategies:
  1. Label-anchored extraction â€” search OCR text for a field's known label
     keywords (e.g. "Patient Name", "DOB") and capture the value that follows
     on the same line. This is the primary strategy for forms/cards.
  2. Pattern-based extraction â€” regex scans for universally-shaped values
     (phone, email, currency, date, ID numbers) anywhere in the text, used
     both as a fallback and to sanity-check/label-anchored matches.

Table detection groups OCR words into rows/columns using coordinate
clustering â€” effective for register-style tabular documents (the dominant
paper format in the target industries) without requiring a deep-learning
table-structure model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from capture.document_types import GENERIC_FIELDS, DocumentTypeSpec, FieldSpec
from capture.ocr_engine import OcrResult, OcrWord

DATE_PATTERNS = [
    r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})\b",
    r"\b(\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})\b",
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
]
PHONE_PATTERN = r"\b(\+?\d[\d\s\-]{7,14}\d)\b"
EMAIL_PATTERN = r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
CURRENCY_PATTERN = r"(?:GHS|USD|\$|â‚¦|GHâ‚µ|Â£|â‚¬)\s?([\d,]+\.?\d{0,2})"
NUMBER_PATTERN = r"\b(\d{1,4})\b"


@dataclass
class ExtractedField:
    field_name: str
    field_label: str
    data_type: str
    value: str | None
    confidence: float  # 0..1
    page: int = 1
    bounding_box: dict | None = None


def _find_word_confidence(value: str, words: list[OcrWord]) -> float:
    """Approximate confidence of an extracted value by matching it against
    OCR words that make it up, averaging their per-word confidences."""
    if not value or not words:
        return 0.6  # neutral default when we can't cross-reference

    tokens = [t.lower() for t in re.findall(r"\w+", value)]
    if not tokens:
        return 0.6

    matched_confidences = []
    for word in words:
        w = word.text.lower().strip(".,;:")
        if w in tokens:
            matched_confidences.append(word.confidence)

    if not matched_confidences:
        return 0.55
    return sum(matched_confidences) / len(matched_confidences)


_LABEL_INDICATORS = {
    "name",
    "date",
    "number",
    "id",
    "institution",
    "university",
    "college",
    "degree",
    "diploma",
    "certificate",
    "grade",
    "gpa",
    "department",
    "faculty",
    "school",
    "programme",
    "program",
    "course",
    "signature",
    "signed",
    "seal",
    "issued",
    "awarded",
    "conferred",
    "address",
    "phone",
    "email",
    "location",
    "country",
    "expiry",
    "valid",
    "license",
    "licence",
    "registration",
}

_LABEL_FIELD_NAMES = {
    "full_name",
    "student_name",
    "applicant_name",
    "mother_name",
    "patient_name",
    "taxpayer_name",
    "household_head",
    "vendor_name",
    "customer_name",
    "recipient_name",
    "respondent_name",
    "member_name",
}


def _looks_like_label(value: str, spec: FieldSpec) -> bool:
    """Check if an extracted value looks like another field label rather than
    an actual value.

    For name fields, a value like "Institution Name" or "Date of Birth" is
    clearly another label, not a person's name. For non-name fields, this
    check is skipped.
    """
    if spec.name not in _LABEL_FIELD_NAMES:
        return False
    v = value.lower().strip()
    if not v:
        return False
    # If the value is short (<= 3 words) and contains multiple label indicator
    # words, it's likely another field label, not a value.
    words_in_value = v.split()
    if len(words_in_value) <= 5:
        label_word_count = sum(1 for w in words_in_value if w in _LABEL_INDICATORS)
        if label_word_count >= 2:
            return True
    return False


def _extract_label_anchored(text: str, spec: FieldSpec, words: list[OcrWord]) -> ExtractedField:
    best_value = None
    # Sort keywords by length (longest first) so more specific labels like
    # "Student Name" are tried before generic ones like "Name". This prevents
    # "Institution Name: ..." from matching when "Student Name: ..." is present.
    sorted_keywords = sorted(spec.keywords, key=len, reverse=True)
    for kw in sorted_keywords:
        # Match "<label> : value" or "<label> - value" or "<label> value" up to line end.
        pattern = re.compile(rf"{re.escape(kw)}\s*[:\-]?\s*([^\n]{{1,80}})", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            candidate = m.group(1).strip()
            # Trim trailing text that looks like the start of the next field label.
            candidate = re.split(r"\s{2,}|\t", candidate)[0].strip(" .:-\t")
            # Skip values that look like they belong to another field label
            # (e.g. "Name: Institution Name" would capture "Institution Name"
            # which is clearly not a person's name).
            if candidate and not _looks_like_label(candidate, spec):
                best_value = candidate
                break

    if best_value is None:
        return ExtractedField(spec.name, spec.label, spec.data_type, None, 0.0)

    confidence = _find_word_confidence(best_value, words)
    return ExtractedField(spec.name, spec.label, spec.data_type, best_value, round(confidence, 3))


def _extract_pattern(text: str, spec: FieldSpec, words: list[OcrWord]) -> ExtractedField | None:
    patterns_by_type = {
        "date": DATE_PATTERNS,
        "phone": [PHONE_PATTERN],
        "email": [EMAIL_PATTERN],
        "currency": [CURRENCY_PATTERN],
    }
    patterns = patterns_by_type.get(spec.data_type)
    if not patterns:
        return None

    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            value = m.group(1)
            confidence = _find_word_confidence(value, words)
            return ExtractedField(
                spec.name, spec.label, spec.data_type, value, round(confidence, 3)
            )
    return None


def extract_fields(
    ocr_result: OcrResult,
    doc_type: DocumentTypeSpec | None,
    template_boost: dict | None = None,
) -> list[ExtractedField]:
    """Extract all expected fields for the given document type (or generic
    fields if the document type is unknown)."""
    text = ocr_result.full_text or ""
    words = ocr_result.words or []
    specs = doc_type.fields if doc_type else GENERIC_FIELDS

    results: list[ExtractedField] = []
    for spec in specs:
        field_result = _extract_label_anchored(text, spec, words)

        if field_result.value is None:
            pattern_result = _extract_pattern(text, spec, words)
            if pattern_result:
                field_result = pattern_result

        # Apply learned template boost: if this org has previously corrected
        # this field on this document type multiple times, nudge confidence
        # up slightly when a value was found (reflects real-world accuracy
        # improvement from a known layout) â€” never fabricate a missing value.
        if field_result.value is not None and template_boost:
            boost = template_boost.get(spec.name, {}).get("correction_count", 0)
            if boost:
                field_result.confidence = min(1.0, field_result.confidence + min(boost, 5) * 0.02)

        results.append(field_result)

    return results


def detect_tables(ocr_result: OcrResult, row_tolerance: float = 0.015) -> list[dict]:
    """Heuristically detect a table per page by clustering words into rows
    (by normalized top coordinate) and columns (by normalized left
    coordinate). Works well for register-style documents with visible rows.
    """
    tables: list[dict] = []
    words_by_page: dict[int, list[OcrWord]] = {}
    for w in ocr_result.words:
        words_by_page.setdefault(w.page, []).append(w)

    for page, words in words_by_page.items():
        if len(words) < 6:
            continue

        sorted_words = sorted(words, key=lambda w: w.top)
        rows: list[list[OcrWord]] = []
        current_row: list[OcrWord] = []
        current_top = None

        for w in sorted_words:
            if current_top is None or abs(w.top - current_top) <= row_tolerance:
                current_row.append(w)
                current_top = w.top if current_top is None else current_top
            else:
                rows.append(current_row)
                current_row = [w]
                current_top = w.top
        if current_row:
            rows.append(current_row)

        # Need at least a few multi-word rows to call this a table.
        multi_word_rows = [r for r in rows if len(r) >= 2]
        if len(multi_word_rows) < 3:
            continue

        # Determine column count from the row with the most cells (likely header).
        header_row = max(multi_word_rows, key=len)
        col_count = len(header_row)

        table_rows = []
        for row in multi_word_rows:
            sorted_cells = sorted(row, key=lambda w: w.left)
            cells = [c.text for c in sorted_cells]
            table_rows.append(cells)

        headers = table_rows[0] if table_rows else []
        data_rows = table_rows[1:] if len(table_rows) > 1 else []

        tables.append(
            {
                "page": page,
                "headers": headers,
                "rows": data_rows,
                "estimated_columns": col_count,
                "row_count": len(data_rows),
            }
        )

    return tables
