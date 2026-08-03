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
from capture.repositories import (
    CaptureAuditLogRepository,
    CaptureBatchRepository,
    CaptureDocumentRepository,
    CaptureFieldRepository,
    CaptureTemplateRepository,
)

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp"}
PDF_EXTENSIONS = {"pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS


class CaptureError(ValueError):
    """User-facing error for invalid capture requests."""


class CaptureService:
    def __init__(self, db: DbSession):
        self.db = db
        # Repository layer — all DB access goes through these
        self.doc_repo = CaptureDocumentRepository(db)
        self.field_repo = CaptureFieldRepository(db)
        self.batch_repo = CaptureBatchRepository(db)
        self.audit_repo = CaptureAuditLogRepository(db)
        self.template_repo = CaptureTemplateRepository(db)
        # File storage service (Phase 12)
        from storage.service import FileService
        self.file_service = FileService(db)

    # ── storage helpers ──────────────────────────────────────────────────

    def _doc_storage_dir(self, organization_id: int, token: str) -> str:
        return os.path.join(config.CAPTURE_STORAGE_DIR, str(organization_id), token)

    def _resolve_local_path(self, storage_key: str) -> str:
        """Resolve a storage key to a local filesystem path.

        For the local backend, this is the direct file path.
        For cloud backends (R2/S3/Supabase), the file is downloaded to a
        temporary directory and the temp path is returned.
        """
        backend = self.file_service.backend
        if backend.name == "local":
            # Local backend — key is relative to base_dir
            return os.path.join(backend.base_dir, storage_key)
        # Cloud backend — download to temp file
        import tempfile
        ext = os.path.splitext(storage_key)[1]
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        data = backend.download(storage_key)
        with open(tmp_path, "wb") as f:
            f.write(data)
        return tmp_path

    def _upload_derived(self, doc: CaptureDocument, key_suffix: str, data: bytes, content_type: str = "image/png") -> str:
        """Upload a derived file (enhanced image, thumbnail) to storage and return the key."""
        key_prefix = f"capture/{doc.organization_id}/"
        file_record = self.file_service.upload(
            organization_id=doc.organization_id,
            filename=f"{key_suffix}.png",
            data=data,
            content_type=content_type,
            uploaded_by=doc.uploaded_by,
            key_prefix=key_prefix + key_suffix + "/",
        )
        return file_record.storage_key

    def _log(self, organization_id: int, action: str, document_id: int | None = None,
              batch_id: int | None = None, actor_id: int | None = None, details: dict | None = None) -> None:
        self.audit_repo.log(
            organization_id, action,
            document_id=document_id, batch_id=batch_id,
            actor_id=actor_id, details=details,
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

        # Upload to storage layer (Phase 12 — abstract object storage)
        key_prefix = f"capture/{organization_id}/"
        file_record = self.file_service.upload(
            organization_id=organization_id,
            filename=filename,
            data=file_content,
            content_type=f"image/{ext}" if ext in IMAGE_EXTENSIONS else "application/pdf",
            uploaded_by=user_id,
            key_prefix=key_prefix,
        )
        original_path = file_record.storage_key

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
        return self.batch_repo.get_by_org(batch_id, organization_id)

    def list_batches(self, organization_id: int, limit: int = 50, offset: int = 0) -> list[CaptureBatch]:
        return self.batch_repo.list_by_org(organization_id, limit, offset)

    def process_batch(self, batch_id: int) -> None:
        """Process every pending document in a batch sequentially.

        Intended to run as a FastAPI BackgroundTask. For very large batches
        (thousands of documents) this should be swapped for a real task
        queue (e.g. the project's existing `apscheduler` worker or Celery);
        the per-document `process_document` call is already isolated and
        safe to parallelize.
        """
        batch = self.batch_repo.get_by_id(batch_id)
        if not batch:
            return

        batch.status = "processing"
        self.db.commit()

        docs = self.doc_repo.list_by_batch(batch_id)
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
        doc = self.doc_repo.get_by_id(document_id)
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
        import tempfile

        # Download original file from storage backend to local path for processing
        local_original = self._resolve_local_path(doc.original_file_path)
        work_dir = tempfile.mkdtemp(prefix="capture_preprocess_")
        enhanced_dir = os.path.join(work_dir, "enhanced")

        if doc.file_type in PDF_EXTENSIONS:
            raw_pages_dir = os.path.join(work_dir, "pages")
            raw_pages = render_pdf_to_images(local_original, raw_pages_dir)
            enhanced_paths = []
            os.makedirs(enhanced_dir, exist_ok=True)
            for i, page_path in enumerate(raw_pages, start=1):
                out_path = os.path.join(enhanced_dir, f"page_{i}.png")
                preprocessing.enhance_image(page_path, out_path)
                enhanced_paths.append(out_path)
            # Upload first enhanced page to storage
            if enhanced_paths:
                with open(enhanced_paths[0], "rb") as f:
                    doc.enhanced_file_path = self._upload_derived(doc, f"doc_{doc.id}_enhanced", f.read())
            else:
                doc.enhanced_file_path = None
            doc.page_count = len(enhanced_paths)
            thumb_source = raw_pages[0] if raw_pages else local_original
        else:
            out_path = os.path.join(enhanced_dir, "enhanced.png")
            os.makedirs(enhanced_dir, exist_ok=True)
            preprocessing.enhance_image(local_original, out_path)
            with open(out_path, "rb") as f:
                doc.enhanced_file_path = self._upload_derived(doc, f"doc_{doc.id}_enhanced", f.read())
            enhanced_paths = [out_path]
            thumb_source = local_original

        # Upload thumbnail to storage
        thumb_path = os.path.join(work_dir, "thumbnail.png")
        try:
            preprocessing.make_thumbnail(thumb_source, thumb_path)
            with open(thumb_path, "rb") as f:
                doc.thumbnail_path = self._upload_derived(doc, f"doc_{doc.id}_thumb", f.read())
        except Exception as e:
            logger.warning("Thumbnail generation failed for document %s: %s", doc.id, e)

        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
            if self.file_service.backend.name != "local" and local_original != doc.original_file_path:
                os.remove(local_original)
        except Exception:
            pass

        self._log(doc.organization_id, "preprocessed", document_id=doc.id,
                   details={"pages": len(enhanced_paths)})
        self.db.commit()
        return enhanced_paths

    def _extract_and_validate(self, doc: CaptureDocument, ocr_result) -> None:
        # Clear any existing fields (retry scenario).
        for f in self.field_repo.list_by_document(doc.id):
            self.db.delete(f)
        self.db.flush()

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
        return self.doc_repo.get_by_org(document_id, organization_id)

    def list_documents(
        self,
        organization_id: int,
        status: str | None = None,
        document_type: str | None = None,
        batch_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CaptureDocument]:
        return self.doc_repo.list_by_org(
            organization_id,
            status=status, document_type=document_type, batch_id=batch_id,
            limit=limit, offset=offset,
        )

    def get_fields(self, document_id: int) -> list[CaptureField]:
        return self.field_repo.list_by_document(document_id)

    def update_field(
        self, document_id: int, field_id: int, organization_id: int, new_value: str, user_id: int
    ) -> CaptureField:
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")

        field = self.field_repo.get_by_id_and_document(field_id, document_id)
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

    # ── database entry (export approved data to dataset) ────────────────

    def export_to_dataset(
        self,
        document_id: int,
        organization_id: int,
        user_id: int,
        dataset_name: str | None = None,
    ) -> dict:
        """Export an approved document's extracted fields as a dataset CSV.

        This is the final 'Database entry' step in the capture pipeline:
        Upload → OCR → Field detection → Validation → Review → Approval → Database entry
        """
        doc = self.get_document(document_id, organization_id)
        if not doc:
            raise CaptureError("Document not found.")
        if doc.status != "approved":
            raise CaptureError("Only approved documents can be exported to the database.")

        fields = self.get_fields(document_id)
        if not fields:
            raise CaptureError("Document has no extracted fields to export.")

        # Build a row from the document's fields
        row: dict[str, str] = {
            "document_id": str(doc.id),
            "filename": doc.filename,
            "document_type": doc.document_type or "",
            "document_type_label": doc.document_type_label or "",
            "industry": doc.industry or "",
            "approved_at": doc.approved_at.isoformat() if doc.approved_at else "",
            "approved_by": str(doc.approved_by or ""),
        }
        for f in fields:
            row[f.field_name] = f.value or ""

        # Write to CSV in the dataset storage area
        import csv
        dataset_dir = os.path.join(config.CAPTURE_STORAGE_DIR, str(organization_id), "exports")
        os.makedirs(dataset_dir, exist_ok=True)
        safe_name = (dataset_name or f"capture_export_{doc.id}").replace(" ", "_").replace("/", "_")
        csv_path = os.path.join(dataset_dir, f"{safe_name}.csv")

        file_exists = os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        # Register in dataset library if available
        try:
            from dataset_library import DatasetEntry, DataTier, get_dataset_library
            lib = get_dataset_library()
            ds_id = f"capture_export_{organization_id}_{safe_name}"
            if not lib.get(ds_id):
                entry = DatasetEntry(
                    id=ds_id,
                    name=dataset_name or f"Capture Export — {doc.document_type_label or doc.document_type or 'Unknown'}",
                    tier=DataTier.PRODUCTION,
                    file_path=csv_path,
                    metadata={
                        "source": "smart_data_capture",
                        "document_type": doc.document_type or "",
                        "industry": doc.industry or "",
                        "description": f"Exported from approved capture document #{doc.id}",
                    },
                )
                lib.register(entry)
        except Exception as e:
            logger.warning("Could not register capture export in dataset library: %s", e)

        self._log(organization_id, "exported", document_id=document_id, actor_id=user_id,
                  details={"dataset_name": safe_name, "csv_path": csv_path})
        self.db.commit()

        return {
            "document_id": doc.id,
            "csv_path": csv_path,
            "dataset_name": safe_name,
            "row_count": 1,
            "field_count": len(fields),
            "fields_exported": list(row.keys()),
        }

    def bulk_export_approved(
        self,
        organization_id: int,
        user_id: int,
        document_type: str | None = None,
        dataset_name: str | None = None,
    ) -> dict:
        """Export all approved documents for an organization to a single dataset CSV."""
        docs = self.list_documents(organization_id, status="approved", document_type=document_type, limit=10000)
        if not docs:
            raise CaptureError("No approved documents to export.")

        import csv
        dataset_dir = os.path.join(config.CAPTURE_STORAGE_DIR, str(organization_id), "exports")
        os.makedirs(dataset_dir, exist_ok=True)
        safe_name = (dataset_name or f"capture_bulk_export_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}").replace(" ", "_").replace("/", "_")
        csv_path = os.path.join(dataset_dir, f"{safe_name}.csv")

        all_field_names: set[str] = set()
        rows: list[dict[str, str]] = []

        for doc in docs:
            fields = self.get_fields(doc.id)
            row: dict[str, str] = {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type or "",
                "document_type_label": doc.document_type_label or "",
                "industry": doc.industry or "",
                "approved_at": doc.approved_at.isoformat() if doc.approved_at else "",
            }
            for f in fields:
                row[f.field_name] = f.value or ""
            all_field_names.update(row.keys())
            rows.append(row)

        # Write CSV with union of all field names
        fieldnames = ["document_id", "filename", "document_type", "document_type_label", "industry", "approved_at"]
        fieldnames.extend(sorted(all_field_names - set(fieldnames)))

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        # Register in dataset library
        try:
            from dataset_library import DatasetEntry, DataTier, get_dataset_library
            lib = get_dataset_library()
            ds_id = f"capture_export_{organization_id}_{safe_name}"
            entry = DatasetEntry(
                id=ds_id,
                name=dataset_name or f"Capture Bulk Export ({len(rows)} documents)",
                tier=DataTier.PRODUCTION,
                file_path=csv_path,
                metadata={
                    "source": "smart_data_capture",
                    "document_type": document_type or "mixed",
                    "industry": "",
                    "description": f"Bulk export of {len(rows)} approved capture documents",
                },
            )
            lib.register(entry)
        except Exception as e:
            logger.warning("Could not register bulk capture export in dataset library: %s", e)

        self._log(organization_id, "bulk_exported", actor_id=user_id,
                  details={"document_count": len(rows), "csv_path": csv_path})
        self.db.commit()

        return {
            "csv_path": csv_path,
            "dataset_name": safe_name,
            "row_count": len(rows),
            "field_count": len(fieldnames),
            "fields_exported": fieldnames,
        }

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

        # Delete files from storage backend (original, enhanced, thumbnail)
        backend = self.file_service.backend
        for key in [doc.original_file_path, doc.enhanced_file_path, doc.thumbnail_path]:
            if key:
                try:
                    backend.delete(key)
                except Exception as e:
                    logger.warning("Failed to delete storage key %s for document %s: %s", key, document_id, e)

        for f in self.field_repo.list_by_document(document_id):
            self.db.delete(f)
        self._log(organization_id, "deleted", document_id=document_id, actor_id=user_id)
        self.db.delete(doc)
        self.db.commit()

    # ── analytics / dashboard integration ───────────────────────────────

    def get_analytics_summary(self, organization_id: int) -> dict:
        """Live summary for dashboards — computed from repository queries."""
        by_status = self.doc_repo.count_by_status(organization_id)
        by_type = self.doc_repo.count_by_type(organization_id)
        by_industry = self.doc_repo.count_by_industry(organization_id)
        avg_confidence = self.doc_repo.avg_confidence(organization_id)
        total = sum(by_status.values())

        return {
            "total_documents": total,
            "approved_documents": by_status.get("approved", 0),
            "pending_review": by_status.get("ready_for_review", 0),
            "failed_documents": by_status.get("failed", 0),
            "average_confidence": avg_confidence,
            "by_status": by_status,
            "by_document_type": by_type,
            "by_industry": by_industry,
        }
