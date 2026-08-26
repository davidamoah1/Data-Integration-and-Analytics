"""Repository for file metadata records."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update

from shared.repositories import BaseRepository
from storage.models import FileRecord


class FileRepository(BaseRepository[FileRecord]):
    """Repository for file metadata data access."""

    model = FileRecord

    def get_by_file_id(self, file_id: str) -> FileRecord | None:
        return self.db.execute(
            select(FileRecord).where(FileRecord.file_id == file_id)
        ).scalar_one_or_none()

    def get_by_org(self, file_id: str, organization_id: int) -> FileRecord | None:
        return self.db.execute(
            select(FileRecord).where(
                FileRecord.file_id == file_id,
                FileRecord.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def list_by_org(
        self,
        organization_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FileRecord]:
        return list(
            self.db.execute(
                select(FileRecord)
                .where(
                    FileRecord.organization_id == organization_id,
                    FileRecord.deleted_at.is_(None),
                )
                .order_by(FileRecord.id.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def count_by_org(self, organization_id: int) -> int:
        result = self.db.execute(
            select(func.count())
            .select_from(FileRecord)
            .where(
                FileRecord.organization_id == organization_id,
                FileRecord.deleted_at.is_(None),
            )
        )
        return int(result.scalar() or 0)

    def mark_accessed(self, file_id: int) -> None:
        self.db.execute(
            update(FileRecord)
            .where(FileRecord.id == file_id)
            .values(accessed_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def soft_delete(self, file_id: int) -> None:
        self.db.execute(
            update(FileRecord)
            .where(FileRecord.id == file_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def get_by_storage_key(self, storage_key: str) -> FileRecord | None:
        return self.db.execute(
            select(FileRecord).where(FileRecord.storage_key == storage_key)
        ).scalar_one_or_none()
