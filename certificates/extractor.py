"""Certificate-specific field extraction engine.

Certificates have a narrative structure ("This is to certify that NAME
has completed COURSE") rather than the label:value structure of forms.
The generic label-anchored extractor in ``capture.extractors`` captures
text on the same line as a keyword, which fails for certificates where
the name and course typically appear on separate lines.

This module implements a layered extraction strategy:

LEVEL 1 — Semantic pattern matching
    Recognize certificate phrasing patterns and extract the name/course
    from the appropriate position (same line or next non-empty line).

LEVEL 2 — Label-anchored fallback
    Fall back to the existing label-anchored extraction for fields that
    the semantic patterns don't cover (institution, dates, etc.).

LEVEL 3 — Confidence scoring
    Score each extracted field based on pattern strength, name-like-ness,
    and OCR word confidence. Mark low-confidence fields for review.

LEVEL 4 — Disambiguation
    Distinguish student name from institution name, signatory names,
    and other person names on the certificate.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

from capture.extractors import ExtractedField, _find_word_confidence
from capture.ocr_engine import OcrResult

logger = logging.getLogger(__name__)


# ── Certificate phrasing patterns for student name ──────────────────

# Patterns where the name follows the phrase, possibly on the next line.
# Each pattern is (regex, capture_group_for_name).
# The regex matches the phrase and then captures everything up to the
# next certificate phrase (like "has successfully completed").
_NAME_PATTERNS: list[re.Pattern[str]] = [
    # "This is to certify that NAME" — name may be on same line or next lines
    re.compile(
        r"this\s+is\s+to\s+certify\s+that\s*[:\-]?\s*"
        r"(.*?)(?:\s+has\s+successfully\s+completed|\s+has\s+completed|"
        r"\s+for\s+successfully\s+completing|\s+for\s+successful\s+completion|"
        r"\s+has\s+successfully\s+completed\s+the|\s+is\s+awarded\b)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "This certificate is awarded to NAME"
    re.compile(
        r"this\s+certificate\s+is\s+awarded\s+to\s*[:\-]?\s*"
        r"(.*?)(?:\s+for\s+successfully|\s+for\s+successful|\s+has\s+completed|"
        r"\s+upon\s+successful|\s+in\s+recognition)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "This certificate is proudly presented to NAME"
    re.compile(
        r"this\s+certificate\s+is\s+proudly\s+presented\s+to\s*[:\-]?\s*"
        r"(.*?)(?:\s+for\s+successfully|\s+for\s+successful|\s+has\s+completed|"
        r"\s+in\s+recognition)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "This is proudly presented to NAME"
    re.compile(
        r"this\s+is\s+proudly\s+presented\s+to\s*[:\-]?\s*"
        r"(.*?)(?:\s+for\s+successfully|\s+for\s+successful|\s+has\s+completed|"
        r"\s+in\s+recognition)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Awarded to NAME" / "Awarded to: NAME" / "Awarded to:\nNAME"
    re.compile(
        r"awarded\s+to\s*[:\-]?\s*"
        r"(.*?)(?:\s+for\s+successfully|\s+for\s+successful|\s+has\s+completed|"
        r"\s+in\s+recognition|\s+upon\s+successful)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Presented to NAME" / "Presented to: NAME"
    re.compile(
        r"presented\s+to\s*[:\-]?\s*"
        r"(.*?)(?:\s+for\s+successfully|\s+for\s+successful|\s+has\s+completed|"
        r"\s+in\s+recognition|\s+upon\s+successful)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "certify that NAME" (shorter variant)
    re.compile(
        r"certify\s+that\s*[:\-]?\s*"
        r"(.*?)(?:\s+has\s+successfully\s+completed|\s+has\s+completed|"
        r"\s+for\s+successfully\s+completing|\s+for\s+successful\s+completion|"
        r"\s+is\s+awarded\b)",
        re.IGNORECASE | re.DOTALL,
    ),
]


# ── Certificate phrasing patterns for course/programme ──────────────

_COURSE_PATTERNS: list[re.Pattern[str]] = [
    # "has successfully completed the COURSE" / "has successfully completed\nCOURSE"
    re.compile(
        r"has\s+successfully\s+completed\s*(?:the\s+)?(?:course\s+)?"
        r"(.*?)(?:\s+awarded\s+by|\s+issued\s+by|\s+from\s+|\s+at\s+|"
        r"\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "has successfully completed COURSE"
    re.compile(
        r"has\s+successfully\s+completed\s+"
        r"(.*?)(?:\s+awarded\s+by|\s+issued\s+by|\s+from\s+|\s+at\s+|"
        r"\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "has completed the COURSE" / "has completed COURSE"
    re.compile(
        r"has\s+completed\s*(?:the\s+)?"
        r"(.*?)(?:\s+awarded\s+by|\s+issued\s+by|\s+from\s+|\s+at\s+|"
        r"\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "for successfully completing COURSE"
    re.compile(
        r"for\s+successfully\s+completing\s*"
        r"(.*?)(?:\s+awarded\s+by|\s+issued\s+by|\s+from\s+|\s+at\s+|"
        r"\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "for successful completion of COURSE"
    re.compile(
        r"for\s+successful\s+completion\s+of\s*"
        r"(.*?)(?:\s+awarded\s+by|\s+issued\s+by|\s+from\s+|\s+at\s+|"
        r"\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Programme: COURSE" / "Programme COURSE" / "Program:\nCOURSE"
    re.compile(
        r"programme\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|institution|awarded|issued)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"program\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|institution|awarded|issued)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Course: COURSE" / "Course:\nCOURSE"
    re.compile(
        r"course\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|institution|awarded|issued|programme|program)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Certificate in COURSE" / "Diploma in COURSE" / "Degree in COURSE"
    re.compile(
        r"(?:certificate\s+in|diploma\s+in|degree\s+in|advanced\s+diploma\s+in|"
        r"higher\s+diploma\s+in|postgraduate\s+diploma\s+in)\s+"
        r"(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|institution|awarded|issued|from|at|by)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Bachelor of COURSE" / "Master of COURSE" / "Doctor of COURSE"
    re.compile(
        r"(?:bachelor\s+of|master\s+of|doctor\s+of|b\.?\s*sc\.?|m\.?\s*sc\.?|b\.?\s*a\.?|m\.?\s*a\.?|ph\.?d\.?)\s+(?:in\s+)?"
        r"(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|institution|awarded|issued|from|at|by)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
]


# ── Institution patterns ───────────────────────────────────────────

_INSTITUTION_PATTERNS: list[re.Pattern[str]] = [
    # "awarded by / issued by / from / at INSTITUTION"
    re.compile(
        r"(?:awarded\s+by|issued\s+by|\bfrom\b|\bat\b)\s*[:\-]?\s*"
        r"(.*?)(?:\s+date\s+[:\-]|\s+certificate\s+number|\s+serial\s+number|"
        r"\s+registration\s+number|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Institution: NAME" / "Institution:\nNAME"
    re.compile(
        r"institution\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|awarded|issued|from|at|by|student|name|course|programme|program)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "University: NAME" / "College: NAME" / "School: NAME"
    re.compile(
        r"(?:university|college|school|institute|academy|polytechnic)\s*[:\-]\s*"
        r"(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|awarded|issued|from|at|by|student|name|course|programme|program)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "This certificate is awarded by INSTITUTION"
    re.compile(
        r"(?:this\s+certificate\s+is\s+)?(?:awarded|issued|granted|presented)\s+(?:by|from|at)\s+"
        r"(.*?)(?:\s+(?:to|on|date|certificate|serial|registration)|\n\s*\n|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # "Issuing Organization: NAME" / "Issuing Body: NAME"
    re.compile(
        r"issuing\s+(?:organization|organisation|body|authority|institution)\s*[:\-]\s*"
        r"(.*?)(?:\n\s*\n|\n\s*(?:date|certificate|serial|registration|awarded|issued|from|at|by|student|name|course|programme|program)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
]


# ── Date patterns ──────────────────────────────────────────────────

_DATE_PATTERNS: list[re.Pattern[str]] = [
    # "Date: 15th January 2024" / "Date: 2024-01-15" / "Date: 15/01/2024"
    re.compile(
        r"\bdate\s+(?:of\s+(?:award|issue|completion|graduation)\s*[:\-]?\s*)?[:\-]?\s*"
        r"(\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdate\s+(?:of\s+(?:award|issue|completion|graduation)\s*[:\-]?\s*)?[:\-]?\s*"
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdate\s+(?:of\s+(?:award|issue|completion|graduation)\s*[:\-]?\s*)?[:\-]?\s*"
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdate\s+(?:of\s+(?:award|issue|completion|graduation)\s*[:\-]?\s*)?[:\-]?\s*"
        r"(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
        re.IGNORECASE,
    ),
    # "Awarded on DATE" / "Issued on DATE" / "Completed on DATE"
    re.compile(
        r"(?:awarded|issued|completed|graduated)\s+on\s*[:\-]?\s*"
        r"(\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:awarded|issued|completed|graduated)\s+on\s*[:\-]?\s*"
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        re.IGNORECASE,
    ),
    # Bare date on a line labeled "Date"
    re.compile(
        r"^\s*date\s*[:\-]\s*(.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
]


# ── Certificate number patterns ────────────────────────────────────

_CERT_NUMBER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\bcertificate\s+(?:no\.?|number|id|code)\s*[:\-]?\s*" r"([A-Z0-9][A-Z0-9\-/\.]{2,50})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bserial\s+(?:no\.?|number)\s*[:\-]?\s*" r"([A-Z0-9][A-Z0-9\-/\.]{2,50})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bregistration\s+(?:no\.?|number)\s*[:\-]?\s*" r"([A-Z0-9][A-Z0-9\-/\.]{2,50})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bref(?:erence)?\s+(?:no\.?|number)\s*[:\-]?\s*" r"([A-Z0-9][A-Z0-9\-/\.]{2,50})",
        re.IGNORECASE,
    ),
]


# ── Signatory / non-student name indicators ─────────────────────────

_SIGNATORY_LABELS = {
    "registrar",
    "dean",
    "director",
    "principal",
    "lecturer",
    "trainer",
    "instructor",
    "professor",
    "prof",
    "dr",
    "mr",
    "mrs",
    "ms",
    "miss",
    "signed",
    "signature",
    "chairman",
    "chairperson",
    "vice",
    "chancellor",
    "rector",
    "head",
    "coordinator",
    "facilitator",
    "speaker",
    "president",
    "secretary",
    "clerk",
    "officer",
    "authority",
    "board",
    "committee",
}

# Words that indicate an institution name, not a person name
_INSTITUTION_INDICATORS = {
    "university",
    "college",
    "institute",
    "school",
    "academy",
    "polytechnic",
    "technical",
    "education",
    "training",
    "center",
    "centre",
    "organization",
    "organisation",
    "association",
    "society",
    "council",
    "board",
    "authority",
    "agency",
    "foundation",
    "trust",
    "limited",
    "ltd",
    "inc",
    "corp",
    "corporation",
    "company",
    "ghana",
    "nigeria",
    "kenya",
    "africa",
    "international",
    "global",
}


# ── Helpers ─────────────────────────────────────────────────────────


def _normalize_text(text: str) -> str:
    """Normalize OCR text: Unicode NFKC, collapse whitespace per line, strip."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines)


def _clean_extracted_value(raw: str) -> str:
    """Clean an extracted value: strip whitespace, remove trailing punctuation,
    remove OCR noise characters."""
    if not raw:
        return ""
    val = raw.strip()
    # Remove trailing/leading punctuation that is not part of a name
    val = re.sub(r"^[·•\-\:\;\,\.\|]+", "", val)
    val = re.sub(r"[·•\-\:\;\,\.\|]+$", "", val)
    # Collapse internal whitespace
    val = re.sub(r"\s+", " ", val).strip()
    return val


def _extract_name_from_block(block: str) -> str | None:
    """Extract a person's name from a block of text.

    The block is the text captured between a certificate phrase (e.g.
    "This is to certify that") and the next phrase (e.g. "has successfully
    completed"). The name may be on the same line or on the next line.

    Returns the cleaned name, or None if no valid name is found.
    """
    if not block:
        return None

    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        return None

    # Strategy: look at the first 1-3 non-empty lines after the phrase.
    # Skip lines that look like part of the phrase itself, institution names,
    # or signatory labels. The name is typically the first line that looks
    # like a person's name.
    for line in lines[:4]:
        cleaned = _clean_extracted_value(line)
        if not cleaned:
            continue

        # Skip lines that are clearly part of the certificate phrasing
        lower = cleaned.lower()
        if any(
            phrase in lower
            for phrase in [
                "has successfully completed",
                "has completed",
                "for successfully completing",
                "for successful completion",
                "is awarded",
                "in recognition",
                "upon successful",
            ]
        ):
            continue

        # Skip lines that look like signatory labels
        words = lower.split()
        if len(words) <= 3 and any(w in _SIGNATORY_LABELS for w in words):
            continue

        # Skip lines that look like institution names
        if any(ind in lower for ind in _INSTITUTION_INDICATORS):
            continue

        # Skip lines that are too long (likely a sentence, not a name)
        if len(cleaned) > 100:
            continue

        # Skip lines that look like dates, numbers, or certificate numbers
        if re.match(r"^[\d\s/\-\.]+$", cleaned):
            continue

        # A person's name is typically 1-5 words, mostly alphabetic
        # (allow hyphens, apostrophes, periods for initials)
        name_words = re.findall(r"[\w'\-\.]+", cleaned)
        if not name_words:
            continue

        # At least 1 word, at most 6 words
        if len(name_words) < 1 or len(name_words) > 6:
            continue

        # Check that most words look like name parts (alphabetic, possibly
        # with hyphens, apostrophes, or single periods for initials)
        name_like = 0
        for w in name_words:
            # Allow: "John", "O'Brien", "Kwame-Mensah", "J.", "K."
            if re.match(r"^[A-Za-z][A-Za-z'\-\.]*$", w):
                name_like += 1

        if name_like < len(name_words) * 0.6:
            continue

        return cleaned

    # If no line matched the heuristics, return the first non-empty line
    # as a low-confidence fallback (better than nothing)
    for line in lines[:2]:
        cleaned = _clean_extracted_value(line)
        if cleaned and not any(
            phrase in cleaned.lower()
            for phrase in [
                "has successfully completed",
                "has completed",
                "for successfully completing",
                "for successful completion",
            ]
        ):
            return cleaned

    return None


def _extract_course_from_block(block: str) -> str | None:
    """Extract a course/programme name from a block of text.

    The block is the text captured after a course phrase (e.g. "has
    successfully completed"). The course may be on the same line or
    on the next line.
    """
    if not block:
        return None

    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        return None

    # The course is typically the first 1-3 lines after the phrase
    course_parts: list[str] = []
    for line in lines[:4]:
        cleaned = _clean_extracted_value(line)
        if not cleaned:
            continue

        lower = cleaned.lower()

        # Stop at institution/date/certificate number phrases
        if any(
            phrase in lower
            for phrase in [
                "awarded by",
                "issued by",
                "date:",
                "date ",
                "certificate number",
                "serial number",
                "registration number",
                "signed",
                "signature",
                "registrar",
                "dean",
                "director",
                "principal",
            ]
        ):
            break

        # Skip lines that are just dates or numbers
        if re.match(r"^[\d\s/\-\.]+$", cleaned):
            continue

        course_parts.append(cleaned)

        # If this line looks like a complete course name (contains "in" or "of"
        # or is a known qualification prefix), stop after it
        if any(
            prefix in lower
            for prefix in [
                "certificate in",
                "diploma in",
                "degree in",
                "bachelor of",
                "master of",
                "doctor of",
                "in information",
                "in data",
                "in business",
                "in computer",
                "in management",
                "in engineering",
            ]
        ):
            break

    if course_parts:
        return " ".join(course_parts)

    return None


def _looks_like_institution(name: str) -> bool:
    """Check if a name looks like an institution rather than a person."""
    if not name:
        return False
    lower = name.lower()
    return any(ind in lower for ind in _INSTITUTION_INDICATORS)


def _looks_like_signatory(name: str) -> bool:
    """Check if a name looks like a signatory label rather than a student."""
    if not name:
        return False
    lower = name.lower()
    # Strip punctuation from words for matching
    words = [re.sub(r"[^a-z]", "", w) for w in lower.split()]
    words = [w for w in words if w]
    if len(words) <= 5:
        return any(w in _SIGNATORY_LABELS for w in words)
    return False


# ── Main extraction function ────────────────────────────────────────


@dataclass
class CertificateExtractionResult:
    """Result of certificate-specific field extraction."""

    student_name: ExtractedField | None = None
    course: ExtractedField | None = None
    institution: ExtractedField | None = None
    date_awarded: ExtractedField | None = None
    certificate_number: ExtractedField | None = None


def extract_certificate_fields(
    ocr_result: OcrResult,
    doc_type_key: str | None = None,
) -> CertificateExtractionResult:
    """Extract student name, course, and institution from certificate OCR text.

    Uses semantic pattern matching to handle the narrative structure of
    certificates. Falls back to None for fields that cannot be extracted.

    Args:
        ocr_result: OCR result with full text and word-level confidence.
        doc_type_key: Document type key (e.g. "academic_certificate") for
            field label mapping. If None, generic labels are used.

    Returns:
        CertificateExtractionResult with extracted fields.
    """
    raw_text = ocr_result.full_text or ""
    normalized = _normalize_text(raw_text)
    words = ocr_result.words or []

    result = CertificateExtractionResult()

    # ── Student name ──────────────────────────────────────────────
    best_name: str | None = None
    name_confidence = 0.0

    for pattern in _NAME_PATTERNS:
        m = pattern.search(normalized)
        if m:
            block = m.group(1).strip()
            name = _extract_name_from_block(block)
            if name and not _looks_like_institution(name) and not _looks_like_signatory(name):
                best_name = name
                # Confidence based on pattern specificity
                # "This is to certify that" is the strongest pattern
                if "certify" in pattern.pattern.lower():
                    name_confidence = 0.85
                elif "awarded" in pattern.pattern.lower():
                    name_confidence = 0.80
                elif "presented" in pattern.pattern.lower():
                    name_confidence = 0.78
                else:
                    name_confidence = 0.70

                # Boost confidence if the name is in all-caps (common on certificates)
                if name == name.upper() and len(name) > 3:
                    name_confidence = min(1.0, name_confidence + 0.15)

                # Cross-reference with OCR word confidence
                word_conf = _find_word_confidence(name, words)
                name_confidence = (name_confidence + word_conf) / 2.0

                break  # Use the first matching pattern (patterns are ordered by specificity)

    if best_name:
        # Map field name based on doc type
        field_name = "student_name"
        field_label = "Student Name"
        result.student_name = ExtractedField(
            field_name=field_name,
            field_label=field_label,
            data_type="text",
            value=best_name,
            confidence=round(name_confidence, 3),
        )
        logger.debug(
            "CERT_EXTRACT student_name=%s confidence=%.3f doc_type=%s",
            best_name,
            name_confidence,
            doc_type_key,
        )

    # ── Course / Programme ────────────────────────────────────────
    best_course: str | None = None
    course_confidence = 0.0

    for pattern in _COURSE_PATTERNS:
        m = pattern.search(normalized)
        if m:
            block = m.group(1).strip()
            course = _extract_course_from_block(block)
            if course and not _looks_like_institution(course):
                best_course = course
                # Confidence based on pattern specificity
                if "successfully completed" in pattern.pattern.lower():
                    course_confidence = 0.82
                elif "successfully completing" in pattern.pattern.lower():
                    course_confidence = 0.80
                elif "successful completion" in pattern.pattern.lower():
                    course_confidence = 0.78
                elif "programme" in pattern.pattern.lower() or "program" in pattern.pattern.lower():
                    course_confidence = 0.75
                elif "course" in pattern.pattern.lower():
                    course_confidence = 0.72
                else:
                    # "Certificate in", "Diploma in", "Bachelor of" etc.
                    course_confidence = 0.85

                # Cross-reference with OCR word confidence
                word_conf = _find_word_confidence(course, words)
                course_confidence = (course_confidence + word_conf) / 2.0

                break

    if best_course:
        # Map field name based on doc type — some types use "course",
        # others use "programme" or "qualification"
        field_name = "course"
        field_label = "Course/Programme"
        if doc_type_key in ("academic_certificate", "degree_certificate"):
            field_name = "programme"
            field_label = "Programme"
        elif doc_type_key == "diploma":
            field_name = "qualification"
            field_label = "Qualification"
        elif doc_type_key in (
            "training_certificate",
            "certificate_of_completion",
        ):
            field_name = "course"
            field_label = "Course/Training"

        result.course = ExtractedField(
            field_name=field_name,
            field_label=field_label,
            data_type="text",
            value=best_course,
            confidence=round(course_confidence, 3),
        )
        logger.debug(
            "CERT_EXTRACT course=%s confidence=%.3f doc_type=%s",
            best_course,
            course_confidence,
            doc_type_key,
        )

    # ── Institution ───────────────────────────────────────────────
    best_institution: str | None = None
    institution_confidence = 0.0

    for pattern in _INSTITUTION_PATTERNS:
        m = pattern.search(normalized)
        if m:
            block = m.group(1).strip()
            inst = _extract_course_from_block(block)  # reuse: gets first meaningful lines
            if inst and _looks_like_institution(inst):
                best_institution = inst
                institution_confidence = 0.75
                word_conf = _find_word_confidence(inst, words)
                institution_confidence = (institution_confidence + word_conf) / 2.0
                break

    # Header-based fallback: scan first 5 lines for institution names.
    # Many certificates have the institution name prominently at the top
    # without any "awarded by" or "issued by" label.
    if not best_institution:
        lines = [l.strip() for l in normalized.split("\n") if l.strip()]
        for line in lines[:5]:
            cleaned = _clean_extracted_value(line)
            if not cleaned or len(cleaned) > 200:
                continue
            if _looks_like_institution(cleaned) and not _looks_like_signatory(cleaned):
                # Avoid matching lines that are part of the certificate phrasing
                lower = cleaned.lower()
                if any(
                    phrase in lower
                    for phrase in [
                        "this is to certify",
                        "this certificate",
                        "awarded to",
                        "has successfully completed",
                        "has completed",
                    ]
                ):
                    continue
                best_institution = cleaned
                institution_confidence = 0.65
                word_conf = _find_word_confidence(cleaned, words)
                institution_confidence = (institution_confidence + word_conf) / 2.0
                break

    if best_institution:
        result.institution = ExtractedField(
            field_name="institution",
            field_label="Institution",
            data_type="text",
            value=best_institution,
            confidence=round(institution_confidence, 3),
        )
        logger.debug(
            "CERT_EXTRACT institution=%s confidence=%.3f",
            best_institution,
            institution_confidence,
        )

    # ── Date awarded ───────────────────────────────────────────────
    best_date: str | None = None
    date_confidence = 0.0

    for pattern in _DATE_PATTERNS:
        m = pattern.search(normalized)
        if m:
            date_val = _clean_extracted_value(m.group(1))
            if date_val and len(date_val) >= 4:
                best_date = date_val
                date_confidence = 0.80
                word_conf = _find_word_confidence(date_val, words)
                date_confidence = (date_confidence + word_conf) / 2.0
                break

    if best_date:
        result.date_awarded = ExtractedField(
            field_name="date_awarded",
            field_label="Date Awarded",
            data_type="date",
            value=best_date,
            confidence=round(date_confidence, 3),
        )
        logger.debug(
            "CERT_EXTRACT date_awarded=%s confidence=%.3f",
            best_date,
            date_confidence,
        )

    # ── Certificate number ────────────────────────────────────────
    best_cert_num: str | None = None
    cert_num_confidence = 0.0

    for pattern in _CERT_NUMBER_PATTERNS:
        m = pattern.search(normalized)
        if m:
            cert_num_val = _clean_extracted_value(m.group(1))
            if cert_num_val and len(cert_num_val) >= 2:
                best_cert_num = cert_num_val
                cert_num_confidence = 0.85
                word_conf = _find_word_confidence(cert_num_val, words)
                cert_num_confidence = (cert_num_confidence + word_conf) / 2.0
                break

    if best_cert_num:
        result.certificate_number = ExtractedField(
            field_name="certificate_number",
            field_label="Certificate Number",
            data_type="text",
            value=best_cert_num,
            confidence=round(cert_num_confidence, 3),
        )
        logger.debug(
            "CERT_EXTRACT certificate_number=%s confidence=%.3f",
            best_cert_num,
            cert_num_confidence,
        )

    logger.info(
        "CERT_EXTRACT_RESULT doc_type=%s name=%s course=%s institution=%s date=%s cert_num=%s",
        doc_type_key,
        bool(best_name),
        bool(best_course),
        bool(best_institution),
        bool(best_date),
        bool(best_cert_num),
    )

    return result
