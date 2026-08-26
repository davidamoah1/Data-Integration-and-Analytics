"""Repository layer for background jobs.

All database access for the Job model goes through here.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update

from jobs.models import Job
from shared.repositories import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for background job data access."""

    model = Job

    def get_by_org(self, job_id: int, organization_id: int) -> Job | None:
        return self.db.execute(
            select(Job).where(
                Job.id == job_id,
                Job.organization_id == organization_id,
            )
        ).scalar_one_or_none()

    def list_by_org(
        self,
        organization_id: int,
        *,
        status: str | None = None,
        job_type: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        stmt = select(Job).where(Job.organization_id == organization_id)
        if status:
            stmt = stmt.where(Job.status == status)
        if job_type:
            stmt = stmt.where(Job.job_type == job_type)
        if user_id:
            stmt = stmt.where(Job.user_id == user_id)
        stmt = stmt.order_by(Job.id.desc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_by_status(self, organization_id: int) -> dict[str, int]:
        results = self.db.execute(
            select(Job.status, func.count())
            .where(Job.organization_id == organization_id)
            .group_by(Job.status)
        ).all()
        return {row[0]: row[1] for row in results}

    def list_pending(self, limit: int = 100) -> list[Job]:
        return list(
            self.db.execute(
                select(Job).where(Job.status == "pending").order_by(Job.id.asc()).limit(limit)
            )
            .scalars()
            .all()
        )

    def list_active(self, organization_id: int) -> list[Job]:
        return list(
            self.db.execute(
                select(Job)
                .where(
                    Job.organization_id == organization_id,
                    Job.status.in_(["pending", "running"]),
                )
                .order_by(Job.id.desc())
            )
            .scalars()
            .all()
        )

    def mark_running(self, job_id: int) -> None:
        self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(status="running", started_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def mark_completed(self, job_id: int, result: str | None = None) -> None:
        self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status="completed",
                progress=1.0,
                result=result,
                completed_at=datetime.now(timezone.utc),
            )
        )
        self.db.flush()

    def mark_failed(self, job_id: int, error: str) -> None:
        self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status="failed",
                error=error,
                completed_at=datetime.now(timezone.utc),
            )
        )
        self.db.flush()

    def mark_cancelled(self, job_id: int) -> None:
        self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status="cancelled",
                completed_at=datetime.now(timezone.utc),
            )
        )
        self.db.flush()

    def update_progress(self, job_id: int, progress: float, message: str | None = None) -> None:
        values: dict = {"progress": progress}
        if message:
            values["progress_message"] = message
        self.db.execute(update(Job).where(Job.id == job_id).values(**values))
        self.db.flush()

    def increment_retries(self, job_id: int) -> int:
        job = self.get_by_id(job_id)
        if job:
            job.retries += 1
            self.db.flush()
            return job.retries
        return 0
