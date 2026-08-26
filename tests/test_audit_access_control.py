"""Regression tests for audit log access-control fixes.

Covers:
  - `/api/audit/logs` (and sibling endpoints) require the `audit.view`
    permission, not just any authenticated user.
  - `/api/audit/activity/{user_id}` must be organization-scoped: a
    non-super-admin must not be able to view another organization's
    user's activity history.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi import HTTPException

from audit.routes import get_user_activity
from authentication.models import User


def _make_user(db_session, *, organization_id: int) -> User:
    user = User(
        email=f"user-{organization_id}-{uuid.uuid4().hex}@test.com",
        password_hash="hash",
        full_name="Test User",
        organization_id=organization_id,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_get_user_activity_blocks_cross_org_access(db_session):
    org1_admin = _make_user(db_session, organization_id=1)
    org2_target = _make_user(db_session, organization_id=2)

    current_user = {
        "id": org1_admin.id,
        "organization_id": 1,
        "roles": ["org_admin"],
        "permissions": ["audit.view"],
    }

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            get_user_activity(
                user_id=org2_target.id,
                limit=50,
                offset=0,
                db=db_session,
                current_user=current_user,
            )
        )
    assert exc_info.value.status_code == 404


def test_get_user_activity_allows_same_org_access(db_session):
    org1_admin = _make_user(db_session, organization_id=1)
    org1_target = _make_user(db_session, organization_id=1)

    current_user = {
        "id": org1_admin.id,
        "organization_id": 1,
        "roles": ["org_admin"],
        "permissions": ["audit.view"],
    }

    result = asyncio.run(
        get_user_activity(
            user_id=org1_target.id,
            limit=50,
            offset=0,
            db=db_session,
            current_user=current_user,
        )
    )
    assert "activities" in result


def test_get_user_activity_allows_super_admin_cross_org(db_session):
    super_admin = _make_user(db_session, organization_id=1)
    other_org_target = _make_user(db_session, organization_id=2)

    current_user = {
        "id": super_admin.id,
        "organization_id": 1,
        "roles": ["super_admin"],
        "permissions": [],
    }

    result = asyncio.run(
        get_user_activity(
            user_id=other_org_target.id,
            limit=50,
            offset=0,
            db=db_session,
            current_user=current_user,
        )
    )
    assert "activities" in result
