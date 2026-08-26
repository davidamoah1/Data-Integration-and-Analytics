"""FastAPI routes for Smart Onboarding â€” Phase 7.

Endpoints:
  - GET  /api/onboarding/status    â€” Get onboarding status & flow
  - POST /api/onboarding/complete   â€” Complete a specific step
  - POST /api/onboarding/skip       â€” Skip onboarding
  - POST /api/onboarding/reset      â€” Reset onboarding progress
  - GET  /api/onboarding/next-action â€” Get next recommended action
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from authentication.repositories import UserRepository
from services.onboarding_service import OnboardingService
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])
_service = OnboardingService()


class CompleteStepRequest(BaseModel):
    step_key: str


@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
):
    """Get the current user's onboarding status and flow definition."""
    status = _service.get_status(current_user)
    return success_response(status)


@router.post("/complete")
async def complete_onboarding_step(
    request: CompleteStepRequest,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Mark a specific onboarding step as completed."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        updated_data = _service.complete_step(
            {
                "id": user.id,
                "roles": current_user.get("roles", []),
                "onboarding_data": user.onboarding_data,
            },
            request.step_key,
        )
        user_repo.update(user.id, onboarding_data=updated_data)
        db.commit()

        # Return updated status
        status = _service.get_status(
            {
                "roles": current_user.get("roles", []),
                "onboarding_data": updated_data,
            }
        )
        return success_response(status, f"Step '{request.step_key}' completed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/skip")
async def skip_onboarding(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Skip onboarding entirely."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_data = _service.skip_onboarding(
        {
            "onboarding_data": user.onboarding_data,
        }
    )
    user_repo.update(user.id, onboarding_data=updated_data, onboarding_completed=1)
    db.commit()

    return success_response({"skipped": True}, "Onboarding skipped")


@router.post("/reset")
async def reset_onboarding(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Reset onboarding progress."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_data = _service.reset_onboarding(
        {
            "onboarding_data": user.onboarding_data,
        }
    )
    user_repo.update(user.id, onboarding_data=updated_data, onboarding_completed=0)
    db.commit()

    status = _service.get_status(
        {
            "roles": current_user.get("roles", []),
            "onboarding_data": updated_data,
        }
    )
    return success_response(status, "Onboarding reset")


@router.get("/next-action")
async def get_next_action(
    current_user: dict = Depends(get_current_user),
):
    """Get the next recommended onboarding action for the user."""
    action = _service.get_next_action(current_user)
    if not action:
        return success_response(None, "Onboarding complete â€” no pending actions")
    return success_response(action)
