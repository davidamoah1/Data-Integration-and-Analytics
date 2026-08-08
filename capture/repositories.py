"""Repository layer for the Smart Data Capture module.

All database access for capture documents, fields, batches, templates,
corrections, and audit logs goes through these repositories. The
service layer calls these — it never touches the SQLAlchemy session
directly.

Architecture:
    routes.py (API) → service.py (Business) → repositories.py (Data) → models.py (ORM)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from capture.models import (
    CaptureAuditLog,
    CaptureBatch,
    CaptureCorrection,
    CaptureDocument,
    CaptureField,
    CaptureTemplate,
)
from shared.repositories import BaseRepository


class CaptureDocumentRepository(BaseRepository[CaptureDocument]):
    """Repository for capture document data access."""

    model = CaptureDocument

    def get_by_org(self, document_id: int, organization_id: int) -> CaptureDocument | None:
        return self.db.execute(
            select(CaptureDocument).where(
                CaptureDocument.id == document_id,
                CaptureDocument.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def list_by_org(
        self,
        organization_id: int,
        *,
        status: str | None = None,
        document_type: str | None = None,
        batch_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CaptureDocument]:
        stmt = select(CaptureDocument).where(CaptureDocument.organization_id == organization_id)
        if status:
            stmt = stmt.where(CaptureDocument.status == status)
        if document_type:
            stmt = stmt.where(CaptureDocument.document_type == document_type)
        if batch_id:
            stmt = stmt.where(CaptureDocument.batch_id == batch_id)
        stmt = stmt.order_by(CaptureDocument.id.desc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def list_by_batch(self, batch_id: int) -> list[CaptureDocument]:
        return list(
            self.db.execute(
                select(CaptureDocument)
                .where(CaptureDocument.batch_id == batch_id)
                .order_by(CaptureDocument.id.asc())
            )
            .scalars()
            .all()
        )

    def count_by_status(self, organization_id: int) -> dict[str, int]:
        results = self.db.execute(
            select(CaptureDocument.status, func.count())
            .where(CaptureDocument.organization_id == organization_id)
            .group_by(CaptureDocument.status)
        ).all()
        return {row[0]: row[1] for row in results}

    def count_by_type(self, organization_id: int) -> dict[str, int]:
        results = self.db.execute(
            select(CaptureDocument.document_type_label, func.count())
            .where(
                CaptureDocument.organization_id == organization_id,
                CaptureDocument.document_type_label.isnot(None),
            )
            .group_by(CaptureDocument.document_type_label)
        ).all()
        return {row[0]: row[1] for row in results}

    def count_by_industry(self, organization_id: int) -> dict[str, int]:
        results = self.db.execute(
            select(CaptureDocument.industry, func.count())
            .where(
                CaptureDocument.organization_id == organization_id,
                CaptureDocument.industry.isnot(None),
            )
            .group_by(CaptureDocument.industry)
        ).all()
        return {row[0]: row[1] for row in results}

    def avg_confidence(self, organization_id: int) -> float:
        result = self.db.execute(
            select(func.avg(CaptureDocument.overall_confidence)).where(
                CaptureDocument.organization_id == organization_id,
                CaptureDocument.overall_confidence.isnot(None),
            )
        ).scalar()
        return round(result or 0.0, 3)

    def list_all_by_org(self, organization_id: int) -> list[CaptureDocument]:
        return list(
            self.db.execute(
                select(CaptureDocument).where(CaptureDocument.organization_id == organization_id)
            )
            .scalars()
            .all()
        )


class CaptureFieldRepository(BaseRepository[CaptureField]):
    """Repository for capture field data access."""

    model = CaptureField

    def list_by_document(self, document_id: int) -> list[CaptureField]:
        return list(
            self.db.execute(
                select(CaptureField)
                .where(CaptureField.document_id == document_id)
                .order_by(CaptureField.id.asc())
            )
            .scalars()
            .all()
        )

    def get_by_id_and_document(self, field_id: int, document_id: int) -> CaptureField | None:
        return self.db.execute(
            select(CaptureField).where(
                CaptureField.id == field_id,
                CaptureField.document_id == document_id,
            )
        ).scalar_one_or_none()

    def delete_by_document(self, document_id: int) -> None:
        self.db.execute(select(CaptureField).where(CaptureField.document_id == document_id))
        for field in self.list_by_document(document_id):
            self.db.delete(field)
        self.db.flush()


class CaptureBatchRepository(BaseRepository[CaptureBatch]):
    """Repository for capture batch data access."""

    model = CaptureBatch

    def get_by_org(self, batch_id: int, organization_id: int) -> CaptureBatch | None:
        return self.db.execute(
            select(CaptureBatch).where(
                CaptureBatch.id == batch_id,
                CaptureBatch.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def list_by_org(
        self, organization_id: int, limit: int = 50, offset: int = 0
    ) -> list[CaptureBatch]:
        return list(
            self.db.execute(
                select(CaptureBatch)
                .where(CaptureBatch.organization_id == organization_id)
                .order_by(CaptureBatch.id.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def increment_processed(self, batch_id: int) -> None:
        batch = self.get_by_id(batch_id)
        if batch:
            batch.processed_documents += 1
            self.db.flush()

    def increment_failed(self, batch_id: int) -> None:
        batch = self.get_by_id(batch_id)
        if batch:
            batch.failed_documents += 1
            self.db.flush()

    def mark_completed(self, batch_id: int, has_errors: bool = False) -> None:
        batch = self.get_by_id(batch_id)
        if batch:
            batch.status = "completed_with_errors" if has_errors else "completed"
            batch.completed_at = datetime.now(timezone.utc)
            self.db.flush()


class CaptureAuditLogRepository(BaseRepository[CaptureAuditLog]):
    """Repository for capture audit log data access."""

    model = CaptureAuditLog

    def list_by_document(self, document_id: int, organization_id: int) -> list[CaptureAuditLog]:
        return list(
            self.db.execute(
                select(CaptureAuditLog)
                .where(
                    CaptureAuditLog.document_id == document_id,
                    CaptureAuditLog.organization_id == organization_id,
                )
                .order_by(CaptureAuditLog.id.asc())
            )
            .scalars()
            .all()
        )

    def log(
        self,
        organization_id: int,
        action: str,
        *,
        document_id: int | None = None,
        batch_id: int | None = None,
        actor_id: int | None = None,
        details: dict | None = None,
    ) -> CaptureAuditLog:
        return self.create(
            organization_id=organization_id,
            document_id=document_id,
            batch_id=batch_id,
            action=action,
            actor_id=actor_id,
            details=details or {},
        )


class CaptureTemplateRepository(BaseRepository[CaptureTemplate]):
    """Repository for capture template data access."""

    model = CaptureTemplate

    def get_by_org_and_type(
        self, organization_id: int, document_type: str
    ) -> CaptureTemplate | None:
        return self.db.execute(
            select(CaptureTemplate).where(
                CaptureTemplate.organization_id == organization_id,
                CaptureTemplate.document_type == document_type,
                CaptureTemplate.is_active == True,  # noqa: E712
            )
        ).scalar_one_or_none()


class CaptureCorrectionRepository(BaseRepository[CaptureCorrection]):
    """Repository for capture correction data access."""

    model = CaptureCorrection

    def list_by_document(self, document_id: int) -> list[CaptureCorrection]:
        return list(
            self.db.execute(
                select(CaptureCorrection)
                .where(CaptureCorrection.document_id == document_id)
                .order_by(CaptureCorrection.id.asc())
            )
            .scalars()
            .all()
        )
