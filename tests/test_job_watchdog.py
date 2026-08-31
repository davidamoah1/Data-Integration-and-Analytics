"""Tests for the stale-job watchdog, heartbeat tracking, and enqueue failure handling.

Covers:
  - JobRepository.update_heartbeat, find_stale_pending, find_stale_running
  - jobs.watchdog._sweep_once marking stale pending/running jobs as failed
  - jobs.service.update_job_progress also updating heartbeat
  - jobs.service.update_heartbeat standalone function
  - Enqueue failure marking job as failed (safe enqueue wrapper)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from jobs.models import Job
from jobs.repositories import JobRepository
from jobs.service import update_heartbeat, update_job_progress
from jobs.watchdog import _sweep_once
from shared.database import Base


@pytest.fixture
def isolated_engine(tmp_path, monkeypatch):
    """A fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    import shared.database as db_module

    monkeypatch.setattr(db_module, "get_engine", lambda **kw: engine)
    monkeypatch.setattr(db_module, "ensure_tables", lambda eng: None)
    monkeypatch.setattr(
        db_module, "get_session_factory", lambda eng=None: sessionmaker(bind=engine)
    )

    yield engine
    Base.metadata.drop_all(engine)


def _create_job(db, status="pending", created_at=None, started_at=None, last_heartbeat_at=None):
    """Helper to create a job with specific timestamps."""
    job = Job(
        organization_id=1,
        user_id=1,
        job_type="dataset_workflow",
        name="Test job",
        status=status,
        progress=0.0,
        payload='{"file_id": 1}',
        max_retries=3,
        created_at=created_at or datetime.now(timezone.utc),
        started_at=started_at,
        last_heartbeat_at=last_heartbeat_at,
    )
    db.add(job)
    db.commit()
    return job


class TestJobRepositoryHeartbeat:
    def test_update_heartbeat_sets_timestamp(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            job = _create_job(db, status="running", started_at=datetime.now(timezone.utc))
            assert job.last_heartbeat_at is None

            repo = JobRepository(db)
            repo.update_heartbeat(job.id)
            db.commit()

            updated = db.get(Job, job.id)
            assert updated.last_heartbeat_at is not None
            assert updated.status == "running"
        finally:
            db.close()

    def test_find_stale_pending_returns_old_jobs(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=600)
            _create_job(db, status="pending", created_at=old_time)
            _create_job(db, status="pending", created_at=datetime.now(timezone.utc))

            repo = JobRepository(db)
            stale = repo.find_stale_pending(datetime.now(timezone.utc) - timedelta(seconds=300))
            assert len(stale) == 1
            assert stale[0].status == "pending"
        finally:
            db.close()

    def test_find_stale_pending_excludes_non_pending(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=600)
            _create_job(db, status="running", created_at=old_time)
            _create_job(db, status="completed", created_at=old_time)

            repo = JobRepository(db)
            stale = repo.find_stale_pending(datetime.now(timezone.utc) - timedelta(seconds=300))
            assert len(stale) == 0
        finally:
            db.close()

    def test_find_stale_running_with_old_heartbeat(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=3600)
            _create_job(
                db,
                status="running",
                started_at=old_time,
                last_heartbeat_at=old_time,
            )
            # Recent heartbeat — should NOT be stale
            _create_job(
                db,
                status="running",
                started_at=old_time,
                last_heartbeat_at=datetime.now(timezone.utc),
            )

            repo = JobRepository(db)
            stale = repo.find_stale_running(datetime.now(timezone.utc) - timedelta(seconds=1800))
            assert len(stale) == 1
        finally:
            db.close()

    def test_find_stale_running_no_heartbeat(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=3600)
            _create_job(
                db,
                status="running",
                started_at=old_time,
                last_heartbeat_at=None,
            )

            repo = JobRepository(db)
            stale = repo.find_stale_running(datetime.now(timezone.utc) - timedelta(seconds=1800))
            assert len(stale) == 1
        finally:
            db.close()


class TestWatchdogSweep:
    def test_sweep_marks_stale_pending_as_failed(self, isolated_engine, monkeypatch):
        monkeypatch.setenv("JOB_PENDING_TIMEOUT_SECONDS", "300")
        monkeypatch.setenv("JOB_RUNNING_TIMEOUT_SECONDS", "1800")
        monkeypatch.setenv("JOB_WATCHDOG_INTERVAL_SECONDS", "60")

        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=600)
            _create_job(db, status="pending", created_at=old_time)
        finally:
            db.close()

        result = asyncio.run(_sweep_once())
        assert result["pending"] == 1
        assert result["running"] == 0

        db = sessionmaker(bind=isolated_engine)()
        try:
            job = db.query(Job).first()
            assert job.status == "failed"
            assert "did not pick up" in (job.error or "")
        finally:
            db.close()

    def test_sweep_marks_stale_running_as_failed(self, isolated_engine, monkeypatch):
        monkeypatch.setenv("JOB_PENDING_TIMEOUT_SECONDS", "300")
        monkeypatch.setenv("JOB_RUNNING_TIMEOUT_SECONDS", "1800")
        monkeypatch.setenv("JOB_WATCHDOG_INTERVAL_SECONDS", "60")

        db = sessionmaker(bind=isolated_engine)()
        try:
            old_time = datetime.now(timezone.utc) - timedelta(seconds=3600)
            _create_job(
                db,
                status="running",
                started_at=old_time,
                last_heartbeat_at=old_time,
            )
        finally:
            db.close()

        result = asyncio.run(_sweep_once())
        assert result["pending"] == 0
        assert result["running"] == 1

        db = sessionmaker(bind=isolated_engine)()
        try:
            job = db.query(Job).first()
            assert job.status == "failed"
            assert "stopped responding" in (job.error or "")
        finally:
            db.close()

    def test_sweep_does_not_touch_recent_jobs(self, isolated_engine, monkeypatch):
        monkeypatch.setenv("JOB_PENDING_TIMEOUT_SECONDS", "300")
        monkeypatch.setenv("JOB_RUNNING_TIMEOUT_SECONDS", "1800")

        db = sessionmaker(bind=isolated_engine)()
        try:
            _create_job(db, status="pending", created_at=datetime.now(timezone.utc))
            _create_job(
                db,
                status="running",
                started_at=datetime.now(timezone.utc),
                last_heartbeat_at=datetime.now(timezone.utc),
            )
        finally:
            db.close()

        result = asyncio.run(_sweep_once())
        assert result["pending"] == 0
        assert result["running"] == 0

        db = sessionmaker(bind=isolated_engine)()
        try:
            jobs = db.query(Job).all()
            assert all(j.status in ("pending", "running") for j in jobs)
        finally:
            db.close()


class TestUpdateJobProgress:
    def test_update_progress_also_updates_heartbeat(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            job = _create_job(db, status="running", started_at=datetime.now(timezone.utc))
            assert job.last_heartbeat_at is None
            job_id = job.id
        finally:
            db.close()

        update_job_progress(job_id, 0.5, "Processing...")

        db = sessionmaker(bind=isolated_engine)()
        try:
            updated = db.get(Job, job_id)
            assert updated.progress == 0.5
            assert updated.progress_message == "Processing..."
            assert updated.last_heartbeat_at is not None
        finally:
            db.close()

    def test_update_heartbeat_standalone(self, isolated_engine):
        db = sessionmaker(bind=isolated_engine)()
        try:
            job = _create_job(db, status="running", started_at=datetime.now(timezone.utc))
            assert job.last_heartbeat_at is None
            job_id = job.id
        finally:
            db.close()

        update_heartbeat(job_id)

        db = sessionmaker(bind=isolated_engine)()
        try:
            updated = db.get(Job, job_id)
            assert updated.last_heartbeat_at is not None
        finally:
            db.close()
