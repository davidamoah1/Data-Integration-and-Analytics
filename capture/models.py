"""Database models for the Smart Data Capture platform."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


class CaptureBatch(Base):
    """A group of documents uploaded together (multi-file or ZIP upload)."""

    __tablename__ = "capture_batches"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(50), nullable=True)
    total_documents = Column(Integer, default=0, nullable=False)
    processed_documents = Column(Integer, default=0, nullable=False)
    failed_documents = Column(Integer, default=0, nullable=False)
    approved_documents = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    # pending -> processing -> completed | completed_with_errors
    created_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)


class CaptureDocument(Base):
    """A single uploaded document moving through the capture pipeline."""

    __tablename__ = "capture_documents"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    batch_id = Column(BigInt, nullable=True, index=True)

    filename = Column(String(500), nullable=False)
    original_file_path = Column(String(1000), nullable=False)
    enhanced_file_path = Column(String(1000), nullable=True)
    thumbnail_path = Column(String(1000), nullable=True)
    file_type = Column(String(20), nullable=False)  # jpg, png, pdf, tiff, etc.
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, default=1, nullable=False)
    source = Column(String(20), default="web", nullable=False)  # web, mobile, api

    # Pipeline status:
    # uploaded -> preprocessing -> classifying -> extracting -> validating ->
    # ready_for_review -> approved | rejected | draft
    # (failed can occur at any stage)
    status = Column(String(30), default="uploaded", nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    industry = Column(String(50), nullable=True)
    document_type = Column(String(100), nullable=True, index=True)
    document_type_label = Column(String(200), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    needs_type_confirmation = Column(Boolean, default=False, nullable=False)

    raw_ocr_text = Column(Text, nullable=True)
    extracted_tables = Column(JSON, nullable=True)  # [{headers: [...], rows: [[...]]}]
    overall_confidence = Column(Float, nullable=True)
    duplicate_of_id = Column(BigInt, nullable=True)

    uploaded_by = Column(BigInt, nullable=False)
    reviewed_by = Column(BigInt, nullable=True)
    approved_by = Column(BigInt, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    processed_at = Column(TIMESTAMP, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    approved_at = Column(TIMESTAMP, nullable=True)
    retention_expires_at = Column(TIMESTAMP, nullable=True)

    # Certificate-specific: verification status distinguishes extraction from
    # authoritative verification. Never auto-set to "verified" — only an
    # external verification source can do that.
    # NOT_VERIFIED -> EXTRACTION_COMPLETE -> VERIFICATION_PENDING -> VERIFIED | VERIFICATION_FAILED
    verification_status = Column(String(30), default="not_verified", nullable=False, index=True)
    verification_method = Column(String(100), nullable=True)  # e.g. "institution_api", "qr_scan"
    verified_at = Column(TIMESTAMP, nullable=True)
    verified_by = Column(BigInt, nullable=True)


class CertificateVerification(Base):
    """Records of verification attempts for a certificate document.

    Verification means an authoritative source confirmed the certificate,
    NOT merely that text was extracted. Multiple attempts may be recorded
    over time (e.g. initial QR scan, later institution API check).
    """

    __tablename__ = "certificate_verifications"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    document_id = Column(BigInt, nullable=False, index=True)

    method = Column(String(100), nullable=False)  # qr_scan, institution_api, manual_check
    status = Column(String(30), nullable=False)  # pending, verified, failed, inconclusive
    verified_by = Column(BigInt, nullable=True)
    verification_source = Column(String(255), nullable=True)  # e.g. "ABC University Registry API"
    reference_number = Column(String(255), nullable=True)  # confirmation code from source
    notes = Column(Text, nullable=True)
    verified_fields = Column(JSON, nullable=True)  # which fields were confirmed

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class CaptureField(Base):
    """An individual extracted field/value belonging to a captured document."""

    __tablename__ = "capture_fields"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    document_id = Column(BigInt, nullable=False, index=True)

    field_name = Column(String(150), nullable=False)  # machine key, e.g. patient_name
    field_label = Column(String(200), nullable=False)  # display label, e.g. "Patient Name"
    field_group = Column(String(100), nullable=True)  # e.g. "row_3" for table rows
    data_type = Column(String(30), default="text", nullable=False)
    # text, number, date, phone, email, currency, enum

    raw_value = Column(Text, nullable=True)  # value as extracted from OCR
    value = Column(Text, nullable=True)  # current (possibly corrected) value
    confidence_score = Column(Float, default=0.0, nullable=False)  # 0..1
    is_low_confidence = Column(Boolean, default=False, nullable=False)
    was_corrected = Column(Boolean, default=False, nullable=False)

    is_valid = Column(Boolean, default=True, nullable=False)
    validation_message = Column(String(500), nullable=True)

    page_number = Column(Integer, default=1, nullable=False)
    bounding_box = Column(JSON, nullable=True)  # {x, y, width, height} normalized 0..1

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class CaptureTemplate(Base):
    """Learned extraction template for a recurring document layout.

    When users repeatedly correct the same field on the same document_type,
    the system stores what was learned here (keyword anchors, typical
    positions, common corrections) and applies it to future uploads of the
    same type to raise confidence and cut down repeat corrections.
    """

    __tablename__ = "capture_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True)
    template_name = Column(String(200), nullable=False)

    field_mapping = Column(JSON, nullable=False, default=dict)
    # { field_name: { "keywords": [...], "value_pattern": "...",
    #                  "correction_count": N, "sample_corrections": [...] } }

    documents_learned_from = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class CaptureCorrection(Base):
    """Log of individual user corrections — the raw learning signal."""

    __tablename__ = "capture_corrections"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    document_id = Column(BigInt, nullable=False, index=True)
    field_id = Column(BigInt, nullable=False, index=True)
    field_name = Column(String(150), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    corrected_by = Column(BigInt, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class CaptureAuditLog(Base):
    """Full audit trail of actions taken on captured documents."""

    __tablename__ = "capture_audit_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    document_id = Column(BigInt, nullable=True, index=True)
    batch_id = Column(BigInt, nullable=True, index=True)
    action = Column(String(50), nullable=False)
    # uploaded, preprocessed, classified, extracted, validated, corrected,
    # approved, rejected, retried, deleted, exported
    actor_id = Column(BigInt, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
