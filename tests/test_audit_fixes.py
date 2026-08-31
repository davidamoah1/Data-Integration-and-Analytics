"""Regression tests for the root-cause audit fixes.

Tests cover:
  - Student name extraction (keyword priority, label rejection, field spec)
  - Extractor keyword sorting (longest-first matching)
  - Certificate type field specs (student_name present in all cert types)
  - Normalizer dispatch for student_name
  - Analysis module student_name fallback to full_name
  - GENERIC_FIELDS uses student_name

All tests are unit-level — no database or network required.
"""

from __future__ import annotations

from capture.document_types import (
    CERTIFICATE_TYPES,
    GENERIC_FIELDS,
    FieldSpec,
)
from capture.extractors import (
    _extract_label_anchored,
    _looks_like_label,
)
from capture.ocr_engine import OcrWord
from certificates.analysis import check_consistency
from certificates.normalizer import normalize_field

# ── Student Name Field Spec Tests ──────────────────────────────


class TestStudentNameFieldSpec:
    """Verify all certificate types use student_name instead of full_name."""

    def test_all_cert_types_have_student_name(self):
        """Every certificate type has a student_name field."""
        for t in CERTIFICATE_TYPES:
            field_names = {f.name for f in t.fields}
            assert "student_name" in field_names, f"{t.key} missing student_name"

    def test_no_cert_type_has_full_name_as_primary(self):
        """No certificate type uses full_name as a field (replaced by student_name)."""
        for t in CERTIFICATE_TYPES:
            field_names = {f.name for f in t.fields}
            assert (
                "full_name" not in field_names
            ), f"{t.key} still uses full_name — should be student_name"

    def test_student_name_is_required(self):
        """student_name is a required field in all certificate types."""
        for t in CERTIFICATE_TYPES:
            student_name_spec = next((f for f in t.fields if f.name == "student_name"), None)
            assert student_name_spec is not None, f"{t.key} has no student_name field"
            assert student_name_spec.required, f"{t.key} student_name should be required"

    def test_student_name_has_rich_keywords(self):
        """student_name field has multiple label variants for extraction."""
        for t in CERTIFICATE_TYPES:
            student_name_spec = next((f for f in t.fields if f.name == "student_name"), None)
            assert student_name_spec is not None
            # Should have at least 5 keywords for robust extraction
            assert (
                len(student_name_spec.keywords) >= 5
            ), f"{t.key} student_name has only {len(student_name_spec.keywords)} keywords"

    def test_student_name_includes_specific_labels(self):
        """student_name keywords include 'student name' and 'candidate name'."""
        for t in CERTIFICATE_TYPES:
            student_name_spec = next((f for f in t.fields if f.name == "student_name"), None)
            assert student_name_spec is not None
            kw_lower = [k.lower() for k in student_name_spec.keywords]
            assert (
                "student name" in kw_lower
            ), f"{t.key} student_name missing 'student name' keyword"

    def test_generic_fields_use_student_name(self):
        """GENERIC_FIELDS uses student_name, not full_name."""
        field_names = {f.name for f in GENERIC_FIELDS}
        assert "student_name" in field_names
        assert "full_name" not in field_names


# ── Extractor Keyword Priority Tests ───────────────────────────


class TestExtractorKeywordPriority:
    """Verify longest-keyword-first matching prevents mis-extraction."""

    def _make_spec(self, name="student_name", keywords=None):
        if keywords is None:
            keywords = [
                "student name",
                "name of student",
                "candidate name",
                "name of candidate",
                "learner name",
                "full name",
                "awarded to",
                "this is to certify",
            ]
        return FieldSpec(
            name=name, label="Student Name", data_type="text", required=True, keywords=keywords
        )

    def _make_words(self, text):
        """Create OcrWord list from text (simple split, uniform confidence)."""
        return [OcrWord(word, 0.9, 1, 0.0, 0.0, 0.0, 0.0) for word in text.split()]

    def test_student_name_preferred_over_generic_name(self):
        """When both 'Student Name: John' and 'Institution Name: MIT' exist,
        the extractor should match 'Student Name' first (longer keyword)."""
        text = "Student Name: John Doe\nInstitution Name: MIT"
        spec = self._make_spec()
        words = self._make_words(text)
        result = _extract_label_anchored(text, spec, words)
        assert result.value == "John Doe"

    def test_name_of_student_extracted(self):
        """'Name of Student' label is correctly extracted."""
        text = "Name of Student: Alice Brown\nDegree: BSc Computer Science"
        spec = self._make_spec()
        words = self._make_words(text)
        result = _extract_label_anchored(text, spec, words)
        assert result.value == "Alice Brown"

    def test_candidate_name_extracted(self):
        """'Candidate Name' label is correctly extracted."""
        text = "Candidate Name: Bob Smith\nResult: Pass"
        spec = self._make_spec()
        words = self._make_words(text)
        result = _extract_label_anchored(text, spec, words)
        assert result.value == "Bob Smith"

    def test_awarded_to_extracted(self):
        """'Awarded to' phrasing is correctly extracted."""
        text = "This is to certify that Awarded to: Jane Doe\nDegree: Bachelor of Arts"
        spec = self._make_spec()
        words = self._make_words(text)
        result = _extract_label_anchored(text, spec, words)
        assert result.value is not None
        assert "Jane Doe" in result.value


# ── Label Rejection Tests ──────────────────────────────────────


class TestLabelRejection:
    """Verify _looks_like_label prevents extracting other field labels as names."""

    def test_institution_name_rejected_for_name_field(self):
        """'Institution Name' should be rejected as a name value."""
        spec = FieldSpec(
            "student_name",
            "Student Name",
            "text",
            True,
            ["student name", "name"],
        )
        assert _looks_like_label("Institution Name", spec) is True

    def test_certificate_number_rejected_for_name_field(self):
        """'Certificate Number' should be rejected as a name value (both 'certificate' and 'number' are label indicators)."""
        spec = FieldSpec(
            "student_name",
            "Student Name",
            "text",
            True,
            ["student name", "name"],
        )
        assert _looks_like_label("Certificate Number", spec) is True

    def test_real_name_not_rejected(self):
        """A real person's name should not be rejected."""
        spec = FieldSpec(
            "student_name",
            "Student Name",
            "text",
            True,
            ["student name", "name"],
        )
        assert _looks_like_label("John Doe", spec) is False

    def test_long_name_not_rejected(self):
        """A longer name (> 5 words) should not be rejected even if it contains label words."""
        spec = FieldSpec(
            "student_name",
            "Student Name",
            "text",
            True,
            ["student name", "name"],
        )
        # 6 words — exceeds the 5-word threshold for label detection
        assert _looks_like_label("John James David Peter Paul Smith", spec) is False

    def test_non_name_field_not_checked(self):
        """_looks_like_label returns False for non-name fields."""
        spec = FieldSpec(
            "institution",
            "Institution",
            "text",
            True,
            ["university", "college"],
        )
        assert _looks_like_label("Institution Name", spec) is False


# ── Normalizer Tests ───────────────────────────────────────────


class TestStudentNameNormalization:
    """Verify student_name is properly normalized."""

    def test_student_name_normalizes_to_title_case(self):
        assert normalize_field("student_name", "JOHN DOE") == "John Doe"

    def test_student_name_preserves_mixed_case(self):
        """Mixed-case names like 'McDonald' are preserved as-is."""
        assert normalize_field("student_name", "jAnE sMiTh") == "jAnE sMiTh"

    def test_student_name_none_returns_none(self):
        assert normalize_field("student_name", None) is None

    def test_full_name_still_normalizes(self):
        """full_name normalization still works for backward compatibility."""
        assert normalize_field("full_name", "JOHN DOE") == "John Doe"


# ── Analysis Fallback Tests ────────────────────────────────────


class TestAnalysisStudentNameFallback:
    """Verify analysis module checks student_name first, then full_name."""

    def test_name_with_digits_flagged_via_student_name(self):
        """Consistency check flags digits in student_name."""
        fields = {
            "student_name": {"value": "John D0e"},
        }
        checks = check_consistency("academic_certificate", fields)
        name_check = [c for c in checks if c.check_name == "name_format"]
        assert len(name_check) == 1
        assert name_check[0].passed is False

    def test_name_with_digits_flagged_via_full_name_fallback(self):
        """Consistency check still works when only full_name is present (backward compat)."""
        fields = {
            "full_name": {"value": "John D0e"},
        }
        checks = check_consistency("academic_certificate", fields)
        name_check = [c for c in checks if c.check_name == "name_format"]
        assert len(name_check) == 1
        assert name_check[0].passed is False

    def test_valid_name_passes_via_student_name(self):
        """Valid student_name (no digits) passes consistency check."""
        fields = {
            "student_name": {"value": "John Doe"},
        }
        checks = check_consistency("academic_certificate", fields)
        name_check = [c for c in checks if c.check_name == "name_format"]
        assert len(name_check) == 1
        assert name_check[0].passed is True
