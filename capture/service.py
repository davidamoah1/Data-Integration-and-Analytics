"""Orchestration service for the Smart Data Capture platform.

Implements the full pipeline:
    Upload -> Preprocess -> Classify -> Extract -> Validate ->
    (Human Review) -> Approve/Reject -> Analytics update

Single documents are processed synchronously (target: under ~10s) so the
upload endpoint can return a ready-to-review result immediately. Batches are
processed document-by-document via FastAPI `BackgroundTasks` so large
uploads don't block the request; `CaptureBatch` counters track progress for
polling from the UI.
"""

from __future__ import annotations

import io
import logging
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

import config
from capture import classifier, extractors, preprocessing, template_service, validators
from capture.document_types import get_document_type
from capture.models import (
    CaptureAuditLog,
    CaptureBatch,
    CaptureDocument,
    CaptureField,
)
from capture.ocr_engine import OcrUnavailableError, is_ocr_available, render_pdf_to_images, run_ocr_on_document

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp"}
PDF_EXTENSIONS = {"pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS


class CaptureError(ValueError):
    """User-facing error for invalid capture requests."""


class CaptureService:
    def __init__(self, db: DbSession):
        self.db = db

    # ── storage helpers ──────────────────────────────────────────────────

    def _doc_storage_dir(self, organization_id: int, token: str) -> str:
        return os.path.join(config.CAPTURE_STORAGE_DIR, str(organization_id), token)

    def _log(self, organization_id: int, action: str, document_id: int | None = None,
              batch_id: int | None = None, actor_id: int | None = None, details: dict | None = None) -> None:
        self.db.add(
            CaptureAuditLog(
                organization_id=organization_id,
                document_id=document_id,
                batch_id=batch_id,
                action=action,
                actor_id=actor_id,
                details=details or {},
            )
        )

    # ── upload ───────────────────────────────────────────────────────────

    def upload_document(
        self,
        organization_id: int,
        user_id: int,
        filename: str,
        file_content: bytes,
        source: str = "web",
        batch_id: int | None = None,
    ) -> CaptureDocument:
        ext = (os.path.splitext(filename)[1] or "").lstrip(".").lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise CaptureError(
                f"Unsupported file type '.{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
            )

        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > config.CAPTURE_MAX_FILE_SIZE_MB:
            raise CaptureError(
                f"File exceeds maximum size of {config.CAPTURE_MAX_FILE_SIZE_MB}MB."
            )

        token = uuid.uuid4().hex[:16]
        storage_dir = self._doc_storage_dir(organization_id, token)
        os.makedirs(storage_dir, exist_ok=True)
        original_path = os.path.join(storage_dir, f"original.{ext}")
        with open(original_path, "wb") as f:
            f.write(file_content)

        retention_expires = datetime.now(timezone.utc) + timedelta(days=config.CAPTURE_RETENTION_DAYS)

        doc = CaptureDocument(
            organization_id=organization_id,
            batch_id=batch_id,
            filename=filename,
            original_file_path=original_path,
            file_type=ext,
            file_size_bytes=len(file_content),
            source=source,
            status="uploaded",
            uploaded_by=user_id,
            retention_expires_at=retention_expires,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        self._log(organization_id, "uploaded", document_id=doc.id, batch_id=batch_id, actor_id=user_id,
                   details={"filename": filename, "size_bytes": len(file_content)})
        self.db.commit()

        return doc

    def upload_zip_batch(
        self,
        organization_id: int,
        user_id: int,
        zip_filename: str,
        zip_content: bytes,
        batch_name: str | None = None,
        industry: str | None = None,
    ) -> tuple[CaptureBatch, list[CaptureDocument]]:
        batch = self.create_batch(organization_id, user_id, batch_name or zip_filename, industry)

        documents: list[CaptureDocument] = []
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = (os.path.splitext(info.filename)[1] or "").lstrip(".").lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                content = zf.read(info.filename)
                try:
                    doc = self.upload_document(
                        organization_id, user_id, os.path.basename(info.filename), content,
                        source="web", batch_id=batch.id,
                    )
                    documents.append(doc)
                except CaptureError as e:
                    logger.warning("Skipped %s in batch upload: %s", info.filename, e)

        batch.total_documents = len(documents)
        self.db.commit()

        return batch, documents

    # ── batches ──────────────────────────────────────────────────────────

    def create_batch(self, organization_id: int, user_id: int, name: str, industry: str | None = None) -> CaptureBatch:
        batch = CaptureBatch(organization_id=organization_id, name=name, industry=industry, created_by=user_id)
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_batch(self, batch_id: int, organization_id: int) -> CaptureBatch | None:
        return (
            self.db.query(CaptureBatch)
            .filter(CaptureBatch.id == batch_id, CaptureBatch.organization_id == organization_id)
            .first()
        )

    def list_batches(self, organization_id: int, limit: int = 50, offset: int = 0) -> list[CaptureBatch]:
        return (
            self.db.query(CaptureBatch)
            .filter(CaptureBatch.organization_id == organization_id)
            .order_by(CaptureBatch.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def process_batch(self, batch_id: int) -> None:
        """Process every pending document in a batch sequentially.

        Intended to run as a FastAPI BackgroundTask. For very large batches
        (thousands of documents) this should be swapped for a real task
        queue (e.g. the project's existing `apscheduler` worker or Celery);
        the per-document `process_document` call is already isolated and
        safe to parallelize.
        """
        batch = self.db.query(CaptureBatch).filter(CaptureBatch.id == batch_id).first()
        if not batch:
            return

        batch.status = "processing"
        self.db.commit()

        docs = self.db.query(CaptureDocument).filter(CaptureDocument.batch_id == batch_id).all()
        for doc in docs:
            try:
                self.process_document(doc.id)
                batch.processed_documents += 1
            except Exception as e:
                logger.exception("Batch document %s failed: %s", doc.id, e)
                batch.failed_documents += 1
            self.db.commit()

        batch.status = "completed_with_errors" if batch.failed_documents else "completed"
        batch.completed_at = datetime.now(timezone.utc)
        self.db.commit()

    # ── pipeline ─────────────────────────────────────────────────────────

    def process_document(self, document_id: int) -> CaptureDocument:
        doc = self.db.query(CaptureDocument).filter(CaptureDocument.id == document_id).first()
        if not doc:
            raise CaptureError("Document not found.")

        try:
            doc.status = "preprocessing"
            self.db.commit()

            page_image_paths = self._preprocess(doc)

            if not is_ocr_available():
                doc.status = "failed"
                doc.error_message = (
                    "OCR engine unavailable: the Tesseract OCR binary is not installed on this "
                    "server. Install it (see https://github.com/tesseract-ocr/tesseract) and retry."
                )
                self._log(doc.organization_id, "failed", document_id=doc.id,
                          details={"reason": "ocr_unavailable"})
                self.db.commit()
                return doc

            doc.status = "extracting"
            self.db.commit()

            ocr_result = run_ocr_on_document(page_image_paths)
            doc.raw_ocr_text = ocr_result.full_text
            doc.page_count = ocr_result.page_count or 1

            doc.status = "classifying"
            self.db.commit()

            classification = classifier.classify_text(ocr_result.full_text)
            if classification.document_type:
                doc.document_type = classification.document_type.key
                doc.document_type_label = classification.document_type.label
                doc.industry = classification.document_type.industry
            doc.classification_confidence = classification.confidence
            doc.needs_type_confirmation = classification.needs_confirmation

            doc.status = "validating"
            self.db.commit()

            self._extract_and_validate(doc, ocr_result)

            # Table detection
            tables = extractors.detect_tables(ocr_result)
            doc.extracted_tables = tables

            doc.status = "ready_for_review"
            doc.processed_at = datetime.now(timezone.utc)
            self._log(doc.organization_id, "extracted", document_id=doc.id,
                      details={"document_type": doc.document_type, "confidence": doc.classification_confidence})
            self.db.commit()
            return doc

        except OcrUnavailableError as e:
            doc.status = "failed"
            doc.error_message = str(e)
            self._log(doc.organization_id, "failed", document_id=doc.id, details={"error": str(e)})
            self.db.commit()
            return doc
        except Exception as e:
            logger.exception("Processing failed for document %s: %s", document_id, e)
            doc.status = "failed"
            doc.error_message = f"Processing error: {e}"
            self._log(doc.organization_id, "failed", document_id=doc.id, details={"error": str(e)})
            self.db.commit()
            return doc

    def _preprocess(self, doc: CaptureDocument) -> list[str]:
        storage_dir = os.path.dirname(doc.original_file_path)
        enhanced_dir = os.path.join(storage_dir, "enhanced")

        if doc.file_type in PDF_EXTENSIONS:
            raw_pages_dir = os.path.join(storage_dir, "pages")
            raw_pages = render_pdf_to_images(doc.original_file_path, raw_pages_dir)
            enhanced_paths = []
            os.makedirs(enhanced_dir, exist_ok=True)
            for i, page_path in enumerate(raw_pages, start=1):
                out_path = os.path.join(enhanced_dir, f"page_{i}.png")
                preprocessing.enhance_image(page_path, out_path)
                enhanced_paths.append(out_path)
            doc.enhanced_file_path = enhanced_paths[0] if enhanced_paths else None
            doc.page_count = len(enhanced_paths)
            thumb_source = raw_pages[0] if raw_pages else doc.original_file_path
        else:
            out_path = os.path.join(enhanced_dir, "enhanced.png")
            preprocessing.enhance_image(doc.original_file_path, out_path)
            doc.enhanced_file_path = out_path
            enhanced_paths = [out_path]
            thumb_source = doc.original_file_path

        thumb_path = os.path.join(storage_dir, "thumbnail.png")
        try:
            preprocessing.make_thumbnail(thumb_source, thumb_path)
            doc.thumbnail_path = thumb_path
        except Exception as e:
            logger.warning("Thumbnail generation failed for document %s: %s", doc.id, e)

        self._log(doc.organization_id, "preprocessed", document_id=doc.id,
                   details={"pages": len(enhanced_paths)})
        self.db.commit()
        return enhanced_paths

    def _extract_and_validate(self, doc: CaptureDocument, ocr_result) -> None:
        # Clear any existing fields (retry scenario).
        self.db.query(CaptureField).filter(CaptureField.document_id == doc.id).delete()

        doc_type_spec = get_document_type(doc.document_type) if doc.document_type else None
        template_boost = template_service.get_template_boost(self.db, doc.organization_id, doc.document_type)

        extracted = extractors.extract_fields(ocr_result, doc_type_spec, template_boost)

        confidences = []
        field_values: dict[str, str] = {}

        for item in extracted:
            enum_values = None
            if doc_type_spec:
                spec = next((f for f in doc_type_spec.fields if f.name == item.field_name), None)
                enum_values = spec.enum_values if spec else None

            is_valid, message = validators.validate_field(item.field_name, item.value, item.data_type, enum_values)
            is_low_conf = item.confidence < config.CAPTURE_LOW_CONFIDENCE_THRESHOLD

            # Suggest standardized spelling for known vocabularies without overwriting.
            if item.field_name == "diagnosis" and item.value:
                suggestion = validators.suggest_standard_spelling(item.value, validators.DIAGNOSIS_MASTER_LIST)
                if suggestion and suggestion.lower() != item.value.lower():
                    message = (message + " " if message else "") + f"Did you mean '{suggestion}'?"
            if item.field_name in ("drug_name",) and item.value:
                suggestion = validators.suggest_standard_spelling(item.value, validators.DRUG_MASTER_LIST)
                if suggestion and suggestion.lower() != item.value.lower():
                    message = (message + " " if message else "") + f"Did you mean '{suggestion}'?"

            field = CaptureField(
                document_id=doc.id,
                field_name=item.field_name,
                field_label=item.field_label,
                data_type=item.data_type,
                raw_value=item.value,
                value=item.value,
                confidence_score=item.confidence,
                is_low_confidence=is_low_conf,
                is_valid=is_valid,
                validation_message=message,
                page_number=item.page,
            )
            self.db.add(field)

            if item.value:
                confidences.append(item.confidence)
                field_values[item.field_name] = item.value

        doc.overall_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        duplicate_id = validators.find_duplicate_document(
            self.db, doc.organization_id, doc.document_type, field_values
        )
        doc.duplicate_of_id = duplicate_id

        self.db.commit()

    # ── review ───────────────────────────────────────────────────────────

    def get_document(self, document_id: int, organization_id: int) -> CaptureDocument | None:
        return (
            self.db.query(CaptureDocument)
            .filter(CaptureDocument.id == document_id, CaptureDocument.organization_id == organization_id)
            .first()
        )

    def list_documents(
        self,
        organization_id: int,
        status: str | None = None,
        document_type: str | None = None,
        batch_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CaptureDocument]:
        q = self.db.query(CaptureDocument).filter(CaptureDocument.organization_id == organization_id)
        if status:
            q = q.filter(CaptureDocument.status == status)
        if document_type:
            q = q.filter(CaptureDocument.document_type == document_type)
        if batch_id:
            q = q.filter(CaptureDocument.batch_id == batch_id)
        return q.order_by(CaptureDocument.id.desc()).offset(offset).limit(limit).all()

    def get_fields(self, document_id: int) -> list[CaptureField]:
        return (
            self.db.query(CaptureField)
            .filter(CaptureField.document_id == document_id)
            .order_by(CaptureField.id.asc())
            .all()
        )

    def update_field(
        self, document_id: int, field_id: int, organization_id: int, new_value: str, user_id: int
    ) -> CaptureField:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")

        field = (
            self.db.query(CaptureField)
            .filter(CaptureField.id == field_id, CaptureField.document_id == document_id)
            .first()
        )
        if not field:
            raise CaptureError("Field not found.")

        old_value = field.value
        field.value = new_value
        field.was_corrected = True
        field.confidence_score = 1.0
        field.is_low_confidence = False

        doc_type_spec = get_document_type(doc.document_type) if doc.document_type else None
        enum_values = None
        if doc_type_spec:
            spec = next((f for f in doc_type_spec.fields if f.name == field.field_name), None)
            enum_values = spec.enum_values if spec else None
        is_valid, message = validators.validate_field(field.field_name, new_value, field.data_type, enum_values)
        field.is_valid = is_valid
        field.validation_message = message

        self.db.commit()

        template_service.record_correction(
            self.db, organization_id, document_id, field_id, field.field_name,
            doc.document_type, old_value, new_value, user_id,
        )
        self._log(organization_id, "corrected", document_id=document_id, actor_id=user_id,
                   details={"field_name": field.field_name, "old_value": old_value, "new_value": new_value})
        self.db.commit()

        return field

    def set_document_type(self, document_id: int, organization_id: int, document_type_key: str, user_id: int) -> CaptureDocument:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")

        spec = get_document_type(document_type_key)
        if not spec:
            raise CaptureError(f"Unknown document type '{document_type_key}'.")

        doc.document_type = spec.key
        doc.document_type_label = spec.label
        doc.industry = spec.industry
        doc.needs_type_confirmation = False
        doc.classification_confidence = 1.0  # user-confirmed
        self.db.commit()

        if doc.raw_ocr_text:
            from capture.ocr_engine import OcrResult
            # Re-extract using the confirmed type. Word-level boxes aren't
            # re-derived here (text-only re-run); re-processing from images
            # via `retry_document` gives full fidelity if needed.
            ocr_result = OcrResult(full_text=doc.raw_ocr_text, words=[], mean_confidence=doc.overall_confidence or 0.0)
            self._extract_and_validate(doc, ocr_result)

        self._log(organization_id, "type_confirmed", document_id=document_id, actor_id=user_id,
                   details={"document_type": spec.key})
        self.db.commit()
        return doc

    def approve_document(self, document_id: int, organization_id: int, user_id: int) -> CaptureDocument:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")
        if doc.status not in ("ready_for_review", "draft"):
            raise CaptureError(f"Document cannot be approved from status '{doc.status}'.")

        doc.status = "approved"
        doc.approved_by = user_id
        doc.approved_at = datetime.now(timezone.utc)
        doc.reviewed_by = user_id
        doc.reviewed_at = datetime.now(timezone.utc)
        self._log(organization_id, "approved", document_id=document_id, actor_id=user_id)
        self.db.commit()
        return doc

    def reject_document(self, document_id: int, organization_id: int, user_id: int, reason: str | None = None) -> CaptureDocument:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")

        doc.status = "rejected"
        doc.reviewed_by = user_id
        doc.reviewed_at = datetime.now(timezone.utc)
        if reason:
            doc.error_message = reason
        self._log(organization_id, "rejected", document_id=document_id, actor_id=user_id, details={"reason": reason})
        self.db.commit()
        return doc

    def save_draft(self, document_id: int, organization_id: int, user_id: int) -> CaptureDocument:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")
        doc.status = "draft"
        doc.reviewed_by = user_id
        doc.reviewed_at = datetime.now(timezone.utc)
        self._log(organization_id, "saved_draft", document_id=document_id, actor_id=user_id)
        self.db.commit()
        return doc

    def retry_document(self, document_id: int, organization_id: int) -> CaptureDocument:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")
        doc.status = "uploaded"
        doc.error_message = None
        self.db.commit()
        return self.process_document(document_id)

    def delete_document(self, document_id: int, organization_id: int, user_id: int) -> None:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")

        storage_dir = os.path.dirname(doc.original_file_path)
        try:
            import shutil
            if os.path.isdir(storage_dir):
                shutil.rmtree(storage_dir, ignore_errors=True)
        except Exception as e:
            logger.warning("Failed to remove storage for document %s: %s", document_id, e)

        self.db.query(CaptureField).filter(CaptureField.document_id == document_id).delete()
        self._log(organization_id, "deleted", document_id=document_id, actor_id=user_id)
        self.db.delete(doc)
        self.db.commit()

    # ── analytics / dashboard integration ───────────────────────────────

    def get_analytics_summary(self, organization_id: int) -> dict:
        """Live summary for dashboards — no manual import/sync required
        since it's computed directly from current capture records."""
        docs = self.db.query(CaptureDocument).filter(CaptureDocument.organization_id == organization_id).all()

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_industry: dict[str, int] = {}
        total_confidence = 0.0
        confidence_count = 0

        for d in docs:
            by_status[d.status] = by_status.get(d.status, 0) + 1
            if d.document_type_label:
                by_type[d.document_type_label] = by_type.get(d.document_type_label, 0) + 1
            if d.industry:
                by_industry[d.industry] = by_industry.get(d.industry, 0) + 1
            if d.overall_confidence is not None:
                total_confidence += d.overall_confidence
                confidence_count += 1

        approved = by_status.get("approved", 0)
        avg_confidence = round(total_confidence / confidence_count, 3) if confidence_count else 0.0

        return {
            "total_documents": len(docs),
            "approved_documents": approved,
            "pending_review": by_status.get("ready_for_review", 0),
            "failed_documents": by_status.get("failed", 0),
            "average_confidence": avg_confidence,
            "by_status": by_status,
            "by_document_type": by_type,
            "by_industry": by_industry,
        }
