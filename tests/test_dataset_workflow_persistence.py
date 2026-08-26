"""Tests for durable dataset workflow state persistence (C3).

Covers the `_persist_workflow_state` progress callback registered on the
routes-module `_orchestrator` singleton in
`services/dataset_workflow_routes.py`, and the `_get_workflow_state_dict`
DB-fallback lookup used by every read endpoint.

Uses a fresh in-memory SQLite engine per test (monkeypatching
`shared.database.get_engine`) so these tests do not depend on test
execution order or leave state behind in a shared file-based DB.
"""

from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import services.dataset_workflow_routes as routes_module
from services.dataset_workflow import WorkflowStage
from services.dataset_workflow_models import DatasetWorkflowRun
from shared.database import Base


@pytest.fixture
def isolated_engine(monkeypatch):
    """A fresh in-memory SQLite engine, wired into shared.database for this test."""
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


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "product_id": [1, 2, 3],
            "product_name": ["A", "B", "C"],
            "price": [10.0, 20.0, 30.0],
        }
    )


def test_workflow_run_persisted_to_db(isolated_engine, sample_df):
    """Running a workflow through the routes-module orchestrator persists it."""
    state = routes_module._orchestrator.start(sample_df, dataset_name="widgets.csv")

    session = sessionmaker(bind=isolated_engine)()
    try:
        row = (
            session.query(DatasetWorkflowRun).filter_by(workflow_id=state.workflow_id).one_or_none()
        )
        assert row is not None
        assert row.dataset_name == "widgets.csv"
        assert row.is_complete is True
        assert row.has_errors is False
        assert WorkflowStage.ANALYSIS_COMPLETE.value in row.stages
    finally:
        session.close()


def test_get_workflow_state_dict_falls_back_to_db(isolated_engine, sample_df):
    """State is still readable via the DB fallback even if purged from memory."""
    state = routes_module._orchestrator.start(sample_df, dataset_name="widgets.csv")
    workflow_id = state.workflow_id

    # Simulate a restart / different worker process: remove from the
    # in-process dict but leave the persisted DB row intact.
    del routes_module._orchestrator._workflows[workflow_id]
    assert routes_module._orchestrator.get_state(workflow_id) is None

    session = sessionmaker(bind=isolated_engine)()
    try:
        current_user = {"id": 1, "roles": ["super_admin"]}
        state_dict = routes_module._get_workflow_state_dict(workflow_id, current_user, session)
    finally:
        session.close()

    assert state_dict["workflow_id"] == workflow_id
    assert state_dict["dataset_name"] == "widgets.csv"
    assert state_dict["is_complete"] is True
    profile = routes_module._stage_result(state_dict, WorkflowStage.PROFILED)
    assert profile is not None
    assert profile["row_count"] == 3


def test_get_workflow_state_dict_404_when_nowhere(isolated_engine):
    from fastapi import HTTPException

    session = sessionmaker(bind=isolated_engine)()
    try:
        current_user = {"id": 1, "roles": ["super_admin"]}
        with pytest.raises(HTTPException) as exc_info:
            routes_module._get_workflow_state_dict("nonexistent-id", current_user, session)
        assert exc_info.value.status_code == 404
    finally:
        session.close()
