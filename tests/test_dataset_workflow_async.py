"""Tests for async (job-queue) execution of the dataset workflow (C4).

Covers:
  - `_async_workflow_execution_available()` gating logic (REDIS_URL +
    serverless detection).
  - `jobs.handlers._handle_dataset_workflow`, the background job handler
    that mirrors the synchronous fallback path.
  - `POST /dataset-workflow/run` returning `202` + enqueuing a job when
    async execution is available, instead of blocking for the full
    pipeline.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import services.dataset_workflow_routes as routes_module
from jobs.handlers import _handle_dataset_workflow, register_builtin_handlers
from jobs.service import JobRepository
from services.dataset_workflow_models import DatasetWorkflowRun
from shared.database import Base
from storage.service import FileService
from storage.storage import LocalFileBackend, set_storage_backend


@pytest.fixture
def isolated_engine(tmp_path, monkeypatch):
    """A fresh in-memory SQLite engine + local temp-dir storage backend."""
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

    set_storage_backend(LocalFileBackend(base_dir=str(tmp_path / "storage")))

    yield engine
    Base.metadata.drop_all(engine)
    set_storage_backend(None)  # reset singleton override for other tests


@pytest.fixture
def sample_csv_bytes():
    df = pd.DataFrame(
        {
            "product_id": [1, 2, 3],
            "product_name": ["A", "B", "C"],
            "price": [10.0, 20.0, 30.0],
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


class TestAsyncExecutionAvailability:
    def test_unavailable_without_redis_url(self, monkeypatch):
        import config

        monkeypatch.setattr(config, "REDIS_URL", "", raising=False)
        monkeypatch.setattr(config, "IS_SERVERLESS", False)
        assert routes_module._async_workflow_execution_available() is False

    def test_unavailable_on_vercel_even_with_redis(self, monkeypatch):
        import config

        monkeypatch.setattr(config, "REDIS_URL", "redis://localhost:6379/0", raising=False)
        monkeypatch.setattr(config, "IS_SERVERLESS", True)
        assert routes_module._async_workflow_execution_available() is False

    def test_available_with_redis_and_not_serverless(self, monkeypatch):
        import config

        monkeypatch.setattr(config, "REDIS_URL", "redis://localhost:6379/0", raising=False)
        monkeypatch.setattr(config, "IS_SERVERLESS", False)

        # Mock the task queue to report Redis backend is connected
        from unittest.mock import MagicMock

        mock_queue = MagicMock()
        mock_queue.is_redis_backend = True
        import jobs.service as jobs_svc

        monkeypatch.setattr(jobs_svc, "get_task_queue", lambda: mock_queue)

        assert routes_module._async_workflow_execution_available() is True


class TestDatasetWorkflowJobHandler:
    def test_handler_runs_full_pipeline(self, isolated_engine, sample_csv_bytes):
        register_builtin_handlers()
        session = sessionmaker(bind=isolated_engine)()
        try:
            file_service = FileService(session)
            record = file_service.upload(
                organization_id=1,
                filename="widgets.csv",
                data=sample_csv_bytes,
                uploaded_by=1,
            )
            session.commit()

            result = _handle_dataset_workflow(
                job_id=1,
                payload={
                    "file_id": record.file_id,
                    "filename": "widgets.csv",
                    "admin_confirmed": False,
                    "organization_id": 1,
                    "created_by": 1,
                },
                db=session,
            )

            assert result["is_complete"] is True
            assert result["dataset_name"] == "widgets.csv"
            assert "governance" in result

            row = (
                session.query(DatasetWorkflowRun)
                .filter_by(workflow_id=result["workflow_id"])
                .one_or_none()
            )
            assert row is not None
            assert row.organization_id == 1
        finally:
            session.close()

    def test_handler_raises_on_missing_file_id(self, isolated_engine):
        session = sessionmaker(bind=isolated_engine)()
        try:
            with pytest.raises(ValueError, match="file_id is required"):
                _handle_dataset_workflow(job_id=1, payload={}, db=session)
        finally:
            session.close()


class TestRunWorkflowRouteAsyncBranch:
    def test_returns_202_and_enqueues_job_when_async_available(
        self, client, db_engine, auth_headers, sample_csv_bytes, tmp_path, monkeypatch
    ):
        register_builtin_handlers()
        set_storage_backend(LocalFileBackend(base_dir=str(tmp_path / "storage")))

        import config

        monkeypatch.setattr(config, "REDIS_URL", "redis://localhost:6379/0", raising=False)
        monkeypatch.setattr(config, "IS_SERVERLESS", False)

        # Mock the task queue to simulate Redis backend without a real Redis
        from unittest.mock import AsyncMock, MagicMock

        mock_queue = MagicMock()
        mock_queue.is_redis_backend = True
        mock_queue.enqueue = AsyncMock()
        import jobs.service as jobs_svc

        monkeypatch.setattr(jobs_svc, "get_task_queue", lambda: mock_queue)

        response = client.post(
            "/api/dataset-workflow/run",
            files={"file": ("widgets.csv", sample_csv_bytes, "text/csv")},
            headers=auth_headers,
        )

        assert response.status_code == 202
        body = response.json()
        assert body["success"] is True
        assert "job_id" in body["data"]
        assert body["data"]["status"] == "pending"

        session = sessionmaker(bind=db_engine)()
        try:
            job = JobRepository(session).get_by_id(body["data"]["job_id"])
            assert job is not None
            assert job.job_type == "dataset_workflow"
            assert job.status == "pending"
        finally:
            session.close()
            set_storage_backend(None)
