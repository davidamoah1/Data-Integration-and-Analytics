"""Tests for the certificate-specific field extraction engine.

Tests cover:
  - Student name extraction from various certificate phrasings
  - Course/programme extraction
  - Institution extraction
  - Confidence scoring
  - Disambiguation (signatory vs student, institution vs person)
  - Edge cases (empty text, missing fields, OCR noise)
"""

from __future__ import annotations

from capture.ocr_engine import OcrResult, OcrWord
from certificates.extractor import (
    _clean_extracted_value,
    _extract_course_from_block,
    _extract_name_from_block,
    _looks_like_institution,
    _looks_like_signatory,
    _normalize_text,
    extract_certificate_fields,
)


def _make_ocr_result(text: str, words: list[OcrWord] | None = None) -> OcrResult:
    """Helper to build an OcrResult from text."""
    if words is None:
        words = []
    return OcrResult(full_text=text, words=words, mean_confidence=0.8, page_count=1)


# ── Student name extraction ─────────────────────────────────────────


class TestStudentNameExtraction:
    """Test student name extraction from various certificate phrasings."""

    def test_this_is_to_certify_that_same_line(self):
        """Name on same line as 'This is to certify that'."""
        text = (
            "This is to certify that John Doe\n"
            "has successfully completed the course\n"
            "Data Science Fundamentals"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert result.student_name.value is not None
        assert "John Doe" in result.student_name.value
        assert result.student_name.confidence > 0.5

    def test_this_is_to_certify_that_next_line(self):
        """Name on the next line after 'This is to certify that'."""
        text = (
            "This is to certify that\n"
            "JANE SMITH\n"
            "has successfully completed\n"
            "Bachelor of Science in Computer Science"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "JANE SMITH" in result.student_name.value
        assert result.student_name.confidence > 0.5

    def test_awarded_to(self):
        text = (
            "This certificate is awarded to\n"
            "Kwame Mensah\n"
            "for successfully completing\n"
            "Advanced Diploma in Network Engineering"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "Kwame Mensah" in result.student_name.value

    def test_presented_to(self):
        text = (
            "This is proudly presented to\n"
            "Mary Johnson\n"
            "for successful completion of\n"
            "Certificate in Data Analytics"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "Mary Johnson" in result.student_name.value

    def test_certify_that_short_form(self):
        text = (
            "We hereby certify that\n"
            "ABENA OSEI\n"
            "has completed\n"
            "Diploma in Business Administration"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "ABENA OSEI" in result.student_name.value

    def test_name_in_all_caps_boosts_confidence(self):
        text = (
            "This is to certify that\n"
            "JOHN KWAME DOE\n"
            "has successfully completed\n"
            "Certificate in Web Development"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert result.student_name.confidence >= 0.8

    def test_name_with_apostrophe(self):
        text = (
            "This is to certify that\n"
            "O'Brien Kofi\n"
            "has successfully completed\n"
            "Certificate in Plumbing"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "O'Brien" in result.student_name.value

    def test_name_with_hyphen(self):
        text = (
            "This is to certify that\n"
            "Kwame-Mensah Yaw\n"
            "has successfully completed\n"
            "Certificate in Electrical Engineering"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "Kwame-Mensah" in result.student_name.value

    def test_no_name_found(self):
        text = "Some random text without certificate phrasing"
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is None

    def test_empty_text(self):
        result = extract_certificate_fields(_make_ocr_result(""))
        assert result.student_name is None
        assert result.course is None

    def test_skip_signatory_label(self):
        """Should not extract 'Registrar' as the student name."""
        text = (
            "This is to certify that\n"
            "Sarah Williams\n"
            "has successfully completed\n"
            "Certificate in Nursing\n"
            "Registrar: Dr. James Brown\n"
            "Dean: Prof. Alice Green"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "Sarah Williams" in result.student_name.value
        assert "Registrar" not in result.student_name.value
        assert "James Brown" not in result.student_name.value

    def test_skip_institution_as_name(self):
        """Should not extract institution name as student name."""
        text = (
            "This is to certify that\n"
            "Michael Asante\n"
            "has successfully completed\n"
            "awarded by Ghana Technology University"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "Michael Asante" in result.student_name.value
        assert "University" not in result.student_name.value


# ── Course/programme extraction ─────────────────────────────────────


class TestCourseExtraction:
    """Test course/programme extraction."""

    def test_has_successfully_completed(self):
        text = (
            "This is to certify that\n"
            "John Doe\n"
            "has successfully completed\n"
            "Data Science Fundamentals\n"
            "awarded by Tech Institute"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Data Science Fundamentals" in result.course.value

    def test_has_completed(self):
        text = (
            "This is to certify that\n"
            "Jane Smith\n"
            "has completed\n"
            "Advanced Network Security\n"
            "issued by Cisco Academy"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Advanced Network Security" in result.course.value

    def test_for_successfully_completing(self):
        text = (
            "This certificate is awarded to\n"
            "Kofi Asante\n"
            "for successfully completing\n"
            "Project Management Professional\n"
            "issued by PMI Institute"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Project Management Professional" in result.course.value

    def test_certificate_in(self):
        text = "Certificate in Data Analytics\n" "awarded to\n" "John Smith\n" "by Tech Institute"
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Data Analytics" in result.course.value

    def test_diploma_in(self):
        text = (
            "Diploma in Business Administration\n"
            "awarded to\n"
            "Sarah Jones\n"
            "by Business College"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Business Administration" in result.course.value

    def test_bachelor_of(self):
        text = (
            "This is to certify that\n"
            "Michael Brown\n"
            "has successfully completed\n"
            "Bachelor of Science in Computer Science\n"
            "awarded by University of Ghana"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Computer Science" in result.course.value

    def test_programme_label(self):
        text = "Programme: Software Engineering\n" "Student: John Doe\n" "Date: 15 January 2024"
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Software Engineering" in result.course.value

    def test_course_label(self):
        text = "Course: Advanced Python Programming\n" "Student: Jane Smith\n" "Date: 20 March 2024"
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is not None
        assert "Advanced Python Programming" in result.course.value

    def test_no_course_found(self):
        text = "Some random text without course phrasing"
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.course is None


# ── Institution extraction ──────────────────────────────────────────


class TestInstitutionExtraction:
    """Test institution extraction."""

    def test_awarded_by(self):
        text = (
            "This is to certify that\n"
            "John Doe\n"
            "has successfully completed\n"
            "Data Science\n"
            "awarded by University of Ghana"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.institution is not None
        assert "University of Ghana" in result.institution.value

    def test_issued_by(self):
        text = (
            "This is to certify that\n"
            "Jane Smith\n"
            "has successfully completed\n"
            "Network Security\n"
            "issued by Cisco Networking Academy"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.institution is not None
        assert "Cisco Networking Academy" in result.institution.value


# ── Combined extraction ─────────────────────────────────────────────


class TestCombinedExtraction:
    """Test that all three fields are extracted together."""

    def test_full_certificate(self):
        text = (
            "This is to certify that\n"
            "JOHN KWAME DOE\n"
            "has successfully completed\n"
            "Certificate in Data Analytics\n"
            "awarded by Ghana Technology University\n"
            "Date: 15 January 2024"
        )
        result = extract_certificate_fields(_make_ocr_result(text), "academic_certificate")
        assert result.student_name is not None
        assert "JOHN KWAME DOE" in result.student_name.value
        assert result.course is not None
        assert "Data Analytics" in result.course.value
        assert result.institution is not None
        assert "Ghana Technology University" in result.institution.value

    def test_doc_type_field_mapping_academic(self):
        text = (
            "This is to certify that\n"
            "Jane Smith\n"
            "has successfully completed\n"
            "Bachelor of Science in Information Technology\n"
            "awarded by University of Ghana"
        )
        result = extract_certificate_fields(_make_ocr_result(text), "academic_certificate")
        assert result.course is not None
        assert result.course.field_name == "programme"

    def test_doc_type_field_mapping_training(self):
        text = (
            "This is to certify that\n"
            "John Doe\n"
            "has successfully completed\n"
            "Advanced Python Programming\n"
            "issued by Tech Training Institute"
        )
        result = extract_certificate_fields(_make_ocr_result(text), "training_certificate")
        assert result.course is not None
        assert result.course.field_name == "course"


# ── Helper function tests ───────────────────────────────────────────


class TestHelpers:
    """Test internal helper functions."""

    def test_clean_extracted_value_strips_punctuation(self):
        assert _clean_extracted_value("  John Doe  ") == "John Doe"
        assert _clean_extracted_value("·John Doe·") == "John Doe"
        assert _clean_extracted_value(":John Doe:") == "John Doe"

    def test_clean_extracted_value_collapses_whitespace(self):
        assert _clean_extracted_value("John   Doe") == "John Doe"

    def test_normalize_text(self):
        assert _normalize_text("Hello  World") == "Hello World"
        assert _normalize_text("Line 1\n\nLine 2") == "Line 1\n\nLine 2"
        assert _normalize_text("") == ""

    def test_looks_like_institution(self):
        assert _looks_like_institution("University of Ghana") is True
        assert _looks_like_institution("Tech Training Institute") is True
        assert _looks_like_institution("John Doe") is False

    def test_looks_like_signatory(self):
        assert _looks_like_signatory("Registrar") is True
        assert _looks_like_signatory("Dr. James Brown") is True
        assert _looks_like_signatory("Dean of Students") is True
        assert _looks_like_signatory("John Doe") is False

    def test_extract_name_from_block_simple(self):
        assert _extract_name_from_block("John Doe") == "John Doe"

    def test_extract_name_from_block_multiline(self):
        block = "\nJOHN DOE\nhas successfully completed"
        name = _extract_name_from_block(block)
        assert name is not None
        assert "JOHN DOE" in name

    def test_extract_name_from_block_empty(self):
        assert _extract_name_from_block("") is None
        assert _extract_name_from_block("\n\n") is None

    def test_extract_course_from_block_simple(self):
        course = _extract_course_from_block("Data Science Fundamentals")
        assert course is not None
        assert "Data Science Fundamentals" in course

    def test_extract_course_from_block_stops_at_date(self):
        block = "Data Science\nDate: 15 January 2024"
        course = _extract_course_from_block(block)
        assert course is not None
        assert "Data Science" in course
        assert "Date" not in course


# ── OCR noise resilience ────────────────────────────────────────────


class TestOcrNoiseResilience:
    """Test that extraction is resilient to common OCR artifacts."""

    def test_extra_whitespace(self):
        text = (
            "This  is  to  certify  that\n"
            "JOHN   DOE\n"
            "has  successfully  completed\n"
            "Certificate  in  Data  Analytics"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "JOHN DOE" in result.student_name.value or "JOHN   DOE" in result.student_name.value

    def test_unicode_normalization(self):
        text = (
            "This is to certify that\n"
            "José García\n"
            "has successfully completed\n"
            "Certificate in Data Analytics"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert (
            "José García" in result.student_name.value or "Jose Garcia" in result.student_name.value
        )

    def test_mixed_case_name(self):
        text = (
            "This is to certify that\n"
            "McDonald Smith\n"
            "has successfully completed\n"
            "Certificate in Web Development"
        )
        result = extract_certificate_fields(_make_ocr_result(text))
        assert result.student_name is not None
        assert "McDonald" in result.student_name.value
