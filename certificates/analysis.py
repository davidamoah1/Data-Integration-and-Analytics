"""Certificate analysis engine.

Analyzes extracted certificate fields to produce:
  - Completeness assessment (required vs. optional fields filled)
  - Consistency checks (e.g. date_awarded vs. graduation_date)
  - Academic performance summary (GPA, grade, class)
  - Qualification and institution summary
  - Anomaly detection (suspicious dates, low-confidence fields, duplicates)
  - Actionable recommendations

This module is **read-only** â€” it never modifies documents or fields.
It operates on data passed to it and returns a structured analysis result.
No data is fabricated; if a field is missing, it is reported as missing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from capture.document_types import get_document_type

# â”€â”€ Data classes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@dataclass
class FieldAnalysis:
    field_name: str
    field_label: str
    value: str | None
    raw_value: str | None
    confidence: float
    is_low_confidence: bool
    is_present: bool
    is_required: bool
    is_valid: bool
    validation_message: str | None
    was_corrected: bool


@dataclass
class CompletenessResult:
    total_fields: int
    required_fields: int
    required_filled: int
    optional_fields: int
    optional_filled: int
    completeness_pct: float  # 0..100 â€” required fields filled
    overall_pct: float  # 0..100 â€” all fields filled
    missing_required: list[str]  # field labels
    missing_optional: list[str]  # field labels


@dataclass
class ConsistencyCheck:
    check_name: str
    description: str
    passed: bool
    severity: str  # "info", "warning", "error"
    detail: str


@dataclass
class AcademicPerformance:
    gpa: str | None
    grade: str | None
    qualification: str | None
    programme: str | None
    has_performance_data: bool
    summary: str


@dataclass
class Anomaly:
    anomaly_type: str  # "low_confidence", "suspicious_date", "duplicate", "validation_failed"
    field_name: str | None
    description: str
    severity: str  # "warning", "error"


@dataclass
class Recommendation:
    action: str
    description: str
    priority: str  # "high", "medium", "low"


@dataclass
class CertificateAnalysis:
    document_type: str | None
    document_type_label: str | None
    classification_confidence: float | None
    overall_confidence: float | None
    fields: list[FieldAnalysis]
    completeness: CompletenessResult
    consistency_checks: list[ConsistencyCheck]
    academic_performance: AcademicPerformance
    anomalies: list[Anomaly]
    recommendations: list[Recommendation]
    summary: str
    verification_status: str
    is_duplicate: bool
    duplicate_of_id: int | None


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _field_dict(fields: list[dict]) -> dict[str, dict]:
    """Convert a list of field dicts (from DB serialization) into a lookup."""
    return {f["field_name"]: f for f in fields}


# â”€â”€ Completeness â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def assess_completeness(
    doc_type_key: str | None,
    field_values: dict[str, dict],
) -> CompletenessResult:
    """Assess how complete the certificate data is against the type spec."""
    spec = get_document_type(doc_type_key) if doc_type_key else None
    if not spec:
        # No spec â€” treat all provided fields as optional
        total = len(field_values)
        filled = sum(1 for f in field_values.values() if f.get("value"))
        return CompletenessResult(
            total_fields=total,
            required_fields=0,
            required_filled=0,
            optional_fields=total,
            optional_filled=filled,
            completeness_pct=100.0 if total == 0 else round(filled / total * 100, 1),
            overall_pct=100.0 if total == 0 else round(filled / total * 100, 1),
            missing_required=[],
            missing_optional=[],
        )

    required_specs = [f for f in spec.fields if f.required]
    optional_specs = [f for f in spec.fields if not f.required]

    required_filled = 0
    missing_required: list[str] = []
    for spec_field in required_specs:
        fdata = field_values.get(spec_field.name)
        if fdata and fdata.get("value"):
            required_filled += 1
        else:
            missing_required.append(spec_field.label)

    optional_filled = 0
    missing_optional: list[str] = []
    for spec_field in optional_specs:
        fdata = field_values.get(spec_field.name)
        if fdata and fdata.get("value"):
            optional_filled += 1
        else:
            missing_optional.append(spec_field.label)

    total = len(spec.fields)
    filled = required_filled + optional_filled

    req_pct = round(required_filled / len(required_specs) * 100, 1) if required_specs else 100.0
    overall_pct = round(filled / total * 100, 1) if total else 100.0

    return CompletenessResult(
        total_fields=total,
        required_fields=len(required_specs),
        required_filled=required_filled,
        optional_fields=len(optional_specs),
        optional_filled=optional_filled,
        completeness_pct=req_pct,
        overall_pct=overall_pct,
        missing_required=missing_required,
        missing_optional=missing_optional,
    )


# â”€â”€ Consistency checks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def check_consistency(
    doc_type_key: str | None,
    field_values: dict[str, dict],
) -> list[ConsistencyCheck]:
    """Run cross-field consistency checks on the certificate data."""
    checks: list[ConsistencyCheck] = []

    def _get(name: str) -> str | None:
        fdata = field_values.get(name)
        return fdata.get("value") if fdata else None

    # 1. date_awarded vs. graduation_date â€” should be close or identical
    date_awarded = _get("date_awarded")
    graduation_date = _get("graduation_date")
    if date_awarded and graduation_date:
        d1 = _parse_date(date_awarded)
        d2 = _parse_date(graduation_date)
        if d1 and d2:
            diff_days = abs((d1 - d2).days)
            if diff_days > 365:
                checks.append(
                    ConsistencyCheck(
                        check_name="date_awarded_vs_graduation",
                        description="Date awarded and graduation date differ by more than 1 year",
                        passed=False,
                        severity="warning",
                        detail=f"Date awarded: {date_awarded}, Graduation date: {graduation_date} ({diff_days} days apart)",
                    )
                )
            else:
                checks.append(
                    ConsistencyCheck(
                        check_name="date_awarded_vs_graduation",
                        description="Date awarded and graduation date are within 1 year",
                        passed=True,
                        severity="info",
                        detail=f"Dates are {diff_days} days apart",
                    )
                )

    # 2. date_issued vs. expiry_date â€” expiry must be after issue
    date_issued = _get("date_issued")
    expiry_date = _get("expiry_date")
    if date_issued and expiry_date:
        d1 = _parse_date(date_issued)
        d2 = _parse_date(expiry_date)
        if d1 and d2 and d2 <= d1:
            checks.append(
                ConsistencyCheck(
                    check_name="expiry_before_issue",
                    description="Expiry date is on or before the issue date",
                    passed=False,
                    severity="error",
                    detail=f"Issued: {date_issued}, Expiry: {expiry_date}",
                )
            )
        elif d1 and d2:
            checks.append(
                ConsistencyCheck(
                    check_name="expiry_after_issue",
                    description="Expiry date is after issue date",
                    passed=True,
                    severity="info",
                    detail=f"Valid for {(d2 - d1).days} days",
                )
            )

    # 3. GPA range check
    gpa = _get("gpa")
    if gpa:
        try:
            gpa_val = float(re.search(r"(\d+\.?\d*)", gpa).group(1))
            if gpa_val > 10:
                checks.append(
                    ConsistencyCheck(
                        check_name="gpa_range",
                        description="GPA/CGPA value exceeds typical maximum (10.0)",
                        passed=False,
                        severity="warning",
                        detail=f"GPA value: {gpa_val}",
                    )
                )
            elif gpa_val < 0:
                checks.append(
                    ConsistencyCheck(
                        check_name="gpa_range",
                        description="GPA/CGPA value is negative",
                        passed=False,
                        severity="error",
                        detail=f"GPA value: {gpa_val}",
                    )
                )
            else:
                checks.append(
                    ConsistencyCheck(
                        check_name="gpa_range",
                        description="GPA/CGPA value is within valid range",
                        passed=True,
                        severity="info",
                        detail=f"GPA: {gpa_val:.2f}",
                    )
                )
        except (ValueError, AttributeError):
            pass

    # 4. Certificate number present for academic/degree certificates
    cert_number = _get("certificate_number")
    if doc_type_key in ("academic_certificate", "degree_certificate", "diploma"):
        if not cert_number:
            checks.append(
                ConsistencyCheck(
                    check_name="certificate_number_present",
                    description="Certificate number is missing for an academic certificate",
                    passed=False,
                    severity="warning",
                    detail="A certificate number helps with verification and traceability",
                )
            )
        else:
            checks.append(
                ConsistencyCheck(
                    check_name="certificate_number_present",
                    description="Certificate number is present",
                    passed=True,
                    severity="info",
                    detail=f"Number: {cert_number}",
                )
            )

    # 5. Full name format â€” should not contain digits
    full_name = _get("full_name")
    if full_name:
        if re.search(r"\d", full_name):
            checks.append(
                ConsistencyCheck(
                    check_name="name_format",
                    description="Full name contains numeric characters â€” possible OCR error",
                    passed=False,
                    severity="warning",
                    detail=f"Name value: '{full_name}'",
                )
            )
        else:
            checks.append(
                ConsistencyCheck(
                    check_name="name_format",
                    description="Full name format appears valid",
                    passed=True,
                    severity="info",
                    detail=f"Name: {full_name}",
                )
            )

    return checks


# â”€â”€ Academic performance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def summarize_academic_performance(
    field_values: dict[str, dict],
) -> AcademicPerformance:
    """Summarize academic performance from available fields."""

    def _get(name: str) -> str | None:
        fdata = field_values.get(name)
        return fdata.get("value") if fdata else None

    gpa = _get("gpa")
    grade = _get("grade")
    qualification = _get("qualification") or _get("degree")
    programme = _get("programme")

    has_data = bool(gpa or grade or qualification)

    parts: list[str] = []
    if qualification:
        parts.append(f"Qualification: {qualification}")
    if programme:
        parts.append(f"Programme: {programme}")
    if grade:
        parts.append(f"Grade/Class: {grade}")
    if gpa:
        parts.append(f"GPA/CGPA: {gpa}")

    summary = " | ".join(parts) if parts else "No academic performance data extracted"

    return AcademicPerformance(
        gpa=gpa,
        grade=grade,
        qualification=qualification,
        programme=programme,
        has_performance_data=has_data,
        summary=summary,
    )


# â”€â”€ Anomaly detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def detect_anomalies(
    field_values: dict[str, dict],
    completeness: CompletenessResult,
    consistency_checks: list[ConsistencyCheck],
    is_duplicate: bool,
    duplicate_of_id: int | None,
    classification_confidence: float | None,
) -> list[Anomaly]:
    """Detect anomalies in the certificate data."""
    anomalies: list[Anomaly] = []

    # Low-confidence fields
    for fname, fdata in field_values.items():
        conf = fdata.get("confidence_score", 1.0) or 1.0
        is_low = fdata.get("is_low_confidence", False)
        if is_low and fdata.get("value"):
            anomalies.append(
                Anomaly(
                    anomaly_type="low_confidence",
                    field_name=fname,
                    description=f"Field '{fdata.get('field_label', fname)}' has low extraction confidence ({conf:.0%})",
                    severity="warning",
                )
            )

    # Validation failures
    for fname, fdata in field_values.items():
        if fdata.get("value") and not fdata.get("is_valid", True):
            anomalies.append(
                Anomaly(
                    anomaly_type="validation_failed",
                    field_name=fname,
                    description=f"Field '{fdata.get('field_label', fname)}' failed validation: {fdata.get('validation_message', '')}",
                    severity="warning",
                )
            )

    # Failed consistency checks
    for check in consistency_checks:
        if not check.passed and check.severity == "error":
            anomalies.append(
                Anomaly(
                    anomaly_type="consistency_error",
                    field_name=None,
                    description=check.detail,
                    severity="error",
                )
            )

    # Duplicate
    if is_duplicate and duplicate_of_id:
        anomalies.append(
            Anomaly(
                anomaly_type="duplicate",
                field_name=None,
                description=f"This certificate appears to be a duplicate of document #{duplicate_of_id}",
                severity="warning",
            )
        )

    # Low classification confidence
    if classification_confidence is not None and classification_confidence < 0.35:
        anomalies.append(
            Anomaly(
                anomaly_type="low_classification_confidence",
                field_name=None,
                description=f"Document type classification confidence is low ({classification_confidence:.0%})",
                severity="warning",
            )
        )

    # Missing required fields
    if completeness.missing_required:
        anomalies.append(
            Anomaly(
                anomaly_type="missing_required_fields",
                field_name=None,
                description=f"{len(completeness.missing_required)} required field(s) missing: {', '.join(completeness.missing_required[:3])}",
                severity="warning",
            )
        )

    return anomalies


# â”€â”€ Recommendations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def generate_recommendations(
    completeness: CompletenessResult,
    anomalies: list[Anomaly],
    verification_status: str,
    consistency_checks: list[ConsistencyCheck],
) -> list[Recommendation]:
    """Generate actionable recommendations based on the analysis."""
    recs: list[Recommendation] = []

    # Missing required fields
    if completeness.missing_required:
        recs.append(
            Recommendation(
                action="review_missing_fields",
                description=f"Review and manually fill {len(completeness.missing_required)} required field(s): {', '.join(completeness.missing_required[:3])}",
                priority="high",
            )
        )

    # Low confidence fields
    low_conf_count = sum(1 for a in anomalies if a.anomaly_type == "low_confidence")
    if low_conf_count:
        recs.append(
            Recommendation(
                action="verify_low_confidence_fields",
                description=f"{low_conf_count} field(s) have low extraction confidence â€” verify against the source document",
                priority="high",
            )
        )

    # Validation failures
    val_fail_count = sum(1 for a in anomalies if a.anomaly_type == "validation_failed")
    if val_fail_count:
        recs.append(
            Recommendation(
                action="fix_validation_errors",
                description=f"{val_fail_count} field(s) failed validation â€” correct the values or confirm they are accurate",
                priority="medium",
            )
        )

    # Consistency errors
    consistency_errors = [c for c in consistency_checks if not c.passed and c.severity == "error"]
    if consistency_errors:
        recs.append(
            Recommendation(
                action="resolve_consistency_errors",
                description=f"{len(consistency_errors)} consistency error(s) detected â€” review date and value relationships",
                priority="high",
            )
        )

    # Verification
    if verification_status == "not_verified":
        recs.append(
            Recommendation(
                action="initiate_verification",
                description="Certificate has not been verified â€” initiate verification through an authoritative source",
                priority="medium",
            )
        )
    elif verification_status == "verification_pending":
        recs.append(
            Recommendation(
                action="follow_up_verification",
                description="Verification is pending â€” follow up with the verification source",
                priority="medium",
            )
        )
    elif verification_status == "verification_failed":
        recs.append(
            Recommendation(
                action="reverify_certificate",
                description="Previous verification attempt failed â€” consider re-verifying with a different method",
                priority="high",
            )
        )

    # Duplicate
    dup_anomalies = [a for a in anomalies if a.anomaly_type == "duplicate"]
    if dup_anomalies:
        recs.append(
            Recommendation(
                action="review_duplicate",
                description="This certificate may be a duplicate â€” compare with the linked document before approving",
                priority="high",
            )
        )

    # Approve if everything looks good
    if (
        not completeness.missing_required
        and not low_conf_count
        and not val_fail_count
        and not consistency_errors
        and not dup_anomalies
    ):
        recs.append(
            Recommendation(
                action="approve_certificate",
                description="All required fields are present, confidence is acceptable, and no anomalies detected â€” ready for approval",
                priority="low",
            )
        )

    return recs


# â”€â”€ Main analysis function â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def analyze_certificate(
    document: dict,
    fields: list[dict],
) -> CertificateAnalysis:
    """Run the full analysis pipeline on a certificate document.

    Args:
        document: Serialized CaptureDocument dict with keys:
            document_type, document_type_label, classification_confidence,
            overall_confidence, verification_status, duplicate_of_id, status
        fields: List of serialized CaptureField dicts with keys:
            field_name, field_label, value, raw_value, confidence_score,
            is_low_confidence, is_valid, validation_message, was_corrected

    Returns:
        CertificateAnalysis with all sub-analyses populated.
    """
    doc_type = document.get("document_type")
    doc_type_label = document.get("document_type_label")
    class_conf = document.get("classification_confidence")
    overall_conf = document.get("overall_confidence")
    verification_status = document.get("verification_status", "not_verified")
    duplicate_of_id = document.get("duplicate_of_id")
    is_duplicate = duplicate_of_id is not None

    # Build field lookup
    field_values = _field_dict(fields)

    # Field-level analysis
    spec = get_document_type(doc_type) if doc_type else None

    field_analyses: list[FieldAnalysis] = []
    for f in fields:
        fname = f.get("field_name", "")
        is_required = False
        if spec:
            spec_field = next((sf for sf in spec.fields if sf.name == fname), None)
            is_required = spec_field.required if spec_field else False
        field_analyses.append(
            FieldAnalysis(
                field_name=fname,
                field_label=f.get("field_label", fname),
                value=f.get("value"),
                raw_value=f.get("raw_value"),
                confidence=f.get("confidence_score", 0.0) or 0.0,
                is_low_confidence=f.get("is_low_confidence", False),
                is_present=bool(f.get("value")),
                is_required=is_required,
                is_valid=f.get("is_valid", True),
                validation_message=f.get("validation_message"),
                was_corrected=f.get("was_corrected", False),
            )
        )

    # Sub-analyses
    completeness = assess_completeness(doc_type, field_values)
    consistency_checks = check_consistency(doc_type, field_values)
    academic_perf = summarize_academic_performance(field_values)
    anomalies = detect_anomalies(
        field_values,
        completeness,
        consistency_checks,
        is_duplicate,
        duplicate_of_id,
        class_conf,
    )
    recommendations = generate_recommendations(
        completeness,
        anomalies,
        verification_status,
        consistency_checks,
    )

    # Build summary
    summary_parts: list[str] = []
    if doc_type_label:
        summary_parts.append(doc_type_label)
    if academic_perf.qualification:
        summary_parts.append(academic_perf.qualification)
    full_name = field_values.get("full_name", {}).get("value")
    if full_name:
        summary_parts.append(f"Holder: {full_name}")
    institution = field_values.get("institution", {}).get("value")
    if institution:
        summary_parts.append(f"Institution: {institution}")
    summary_parts.append(f"Completeness: {completeness.completeness_pct:.0f}%")
    summary_parts.append(f"Verification: {verification_status}")
    summary = " | ".join(summary_parts)

    return CertificateAnalysis(
        document_type=doc_type,
        document_type_label=doc_type_label,
        classification_confidence=class_conf,
        overall_confidence=overall_conf,
        fields=field_analyses,
        completeness=completeness,
        consistency_checks=consistency_checks,
        academic_performance=academic_perf,
        anomalies=anomalies,
        recommendations=recommendations,
        summary=summary,
        verification_status=verification_status,
        is_duplicate=is_duplicate,
        duplicate_of_id=duplicate_of_id,
    )


def analyze_batch(
    documents: list[dict], fields_by_doc: dict[int, list[dict]]
) -> list[CertificateAnalysis]:
    """Analyze a batch of certificate documents.

    Args:
        documents: List of serialized CaptureDocument dicts
        fields_by_doc: Mapping of document_id -> list of field dicts

    Returns:
        List of CertificateAnalysis, one per document
    """
    results: list[CertificateAnalysis] = []
    for doc in documents:
        doc_id = doc.get("id")
        fields = fields_by_doc.get(doc_id, [])
        results.append(analyze_certificate(doc, fields))
    return results


# â”€â”€ Batch-level analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@dataclass
class BatchAnalytics:
    total: int
    by_type: dict[str, int]
    by_verification: dict[str, int]
    by_completeness_tier: dict[str, int]  # high (>80%), medium (50-80%), low (<50%)
    avg_completeness: float
    avg_confidence: float
    total_anomalies: int
    total_duplicates: int
    common_anomalies: dict[str, int]
    institutions: dict[str, int]
    qualifications: dict[str, int]
    summary: str


def batch_analytics(analyses: list[CertificateAnalysis]) -> BatchAnalytics:
    """Compute aggregate analytics across a set of certificate analyses."""
    total = len(analyses)
    if total == 0:
        return BatchAnalytics(
            total=0,
            by_type={},
            by_verification={},
            by_completeness_tier={},
            avg_completeness=0.0,
            avg_confidence=0.0,
            total_anomalies=0,
            total_duplicates=0,
            common_anomalies={},
            institutions={},
            qualifications={},
            summary="No certificates to analyze",
        )

    by_type: dict[str, int] = {}
    by_verification: dict[str, int] = {}
    by_completeness_tier: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    institutions: dict[str, int] = {}
    qualifications: dict[str, int] = {}
    anomaly_counts: dict[str, int] = {}
    total_anomalies = 0
    total_duplicates = 0
    completeness_sum = 0.0
    confidence_sum = 0.0

    for a in analyses:
        # Type
        type_label = a.document_type_label or a.document_type or "Unknown"
        by_type[type_label] = by_type.get(type_label, 0) + 1

        # Verification
        by_verification[a.verification_status] = by_verification.get(a.verification_status, 0) + 1

        # Completeness tier
        pct = a.completeness.completeness_pct
        completeness_sum += pct
        if pct >= 80:
            by_completeness_tier["high"] += 1
        elif pct >= 50:
            by_completeness_tier["medium"] += 1
        else:
            by_completeness_tier["low"] += 1

        # Confidence
        if a.overall_confidence is not None:
            confidence_sum += a.overall_confidence

        # Anomalies
        total_anomalies += len(a.anomalies)
        for anomaly in a.anomalies:
            anomaly_counts[anomaly.anomaly_type] = anomaly_counts.get(anomaly.anomaly_type, 0) + 1

        # Duplicates
        if a.is_duplicate:
            total_duplicates += 1

        # Institutions and qualifications from field analysis
        for fa in a.fields:
            if fa.field_name == "institution" and fa.value:
                inst = fa.value.strip()
                institutions[inst] = institutions.get(inst, 0) + 1
            if fa.field_name in ("qualification", "degree") and fa.value:
                qual = fa.value.strip()
                qualifications[qual] = qualifications.get(qual, 0) + 1

    avg_completeness = round(completeness_sum / total, 1)
    avg_confidence = round(confidence_sum / total, 3) if total else 0.0

    summary = (
        f"{total} certificates analyzed. "
        f"Average completeness: {avg_completeness:.0f}%. "
        f"Average confidence: {avg_confidence:.0%}. "
        f"{total_anomalies} anomalies detected. "
        f"{total_duplicates} duplicates found."
    )

    return BatchAnalytics(
        total=total,
        by_type=by_type,
        by_verification=by_verification,
        by_completeness_tier=by_completeness_tier,
        avg_completeness=avg_completeness,
        avg_confidence=avg_confidence,
        total_anomalies=total_anomalies,
        total_duplicates=total_duplicates,
        common_anomalies=anomaly_counts,
        institutions=institutions,
        qualifications=qualifications,
        summary=summary,
    )
