"""Test fixtures for authentication and authorization tests.

Provides a fresh in-memory SQLite database with seeded roles, permissions,
and a super admin user for each test.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set env to use sqlite for tests
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_auth.db"
os.environ["PYTEST_RUNNING"] = "1"
os.environ["SUPER_ADMIN_PASSWORD"] = "Admin@12345"

import ai.models  # noqa: F401
import analytics.models  # noqa: F401
import audit.models  # noqa: F401
import authentication.models  # noqa: F401
import enterprise.models  # noqa: F401
import enterprise.subscription  # noqa: F401
import etl.models  # noqa: F401
import notifications.models  # noqa: F401
import organizations.models  # noqa: F401
import scheduler.models  # noqa: F401
import workflows.models  # noqa: F401
from authentication.services import seed_default_data
from shared import database as db_module
from shared.database import Base, get_db


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    # Also create existing tables (sales, pipeline_runs) — they use a different Base
    from database.db_setup import Base as OldBase

    OldBase.metadata.create_all(engine)

    # Seed default data
    db = DbSession(engine)
    try:
        seed_default_data(db)
    finally:
        db.close()

    yield engine
    Base.metadata.drop_all(engine)
    OldBase.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for a test."""
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """Create a FastAPI test client with the test database."""
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    from api.main import app

    app.dependency_overrides[get_db] = override_get_db
    # Override get_engine so startup event uses the test engine
    original_get_engine = db_module.get_engine
    db_module.get_engine = lambda **kw: db_engine
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    db_module.get_engine = original_get_engine


@pytest.fixture
def admin_token(client):
    """Login as the default super admin and return the access token."""
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@dataflow.io",
            "password": "Admin@12345",
        },
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """Return authorization headers for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
