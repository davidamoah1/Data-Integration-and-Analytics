"""Base API controller — thin route layer with standard patterns.

Controllers handle HTTP concerns only: request parsing, dependency
injection, response serialization, and exception translation. All
business logic lives in services.

Architecture layer:
    API Routes (Controller) → Service Layer → Repository Layer → Database

Usage:
    class CaptureController(BaseController):
        service_class = CaptureDocumentService

        @router.get("/documents")
        async def list_documents(self, ...):
            return self.handle_list(...)
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from shared.exceptions import AppException, NotFoundError, ValidationError
from shared.response import success_response
from shared.services import BaseService
from shared.tenant import get_current_organization_id


class BaseController:
    """Base controller providing common HTTP handling patterns.

    Subclasses bind a service class and define routes. The controller
    handles:
      - Auth dependency injection
      - Tenant scoping (organization_id)
      - Exception → HTTP status translation
      - Standard response formatting
    """

    service_class: type[BaseService]

    def __init__(self, db: DbSession, current_user: dict | None = None):
        self.db = db
        self.current_user = current_user
        self.service: BaseService = self.service_class(db)

    @property
    def org_id(self) -> int:
        if not self.current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return get_current_organization_id(self.current_user, self.db)

    @property
    def user_id(self) -> int:
        if not self.current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return self.current_user["id"]

    # ── Response helpers ────────────────────────────────────────────────

    @staticmethod
    def ok(data: Any = None, message: str = "OK") -> dict:
        return success_response(data, message)

    @staticmethod
    def created(data: Any = None, message: str = "Created") -> dict:
        return success_response(data, message)

    @staticmethod
    def deleted(message: str = "Deleted") -> dict:
        return success_response(None, message)

    # ── Exception translation ───────────────────────────────────────────

    @staticmethod
    def handle_error(e: Exception) -> None:
        if isinstance(e, AppException):
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        if isinstance(e, NotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        if isinstance(e, ValidationError):
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def get_controller(controller_class: type[BaseController]):
    """FastAPI dependency factory for controller injection.

    Usage in routes:
        @router.get("/items")
        async def list_items(ctrl: MyController = Depends(get_controller(MyController))):
            return ctrl.ok(ctrl.service.list())
    """

    def _create(
        db: DbSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ) -> BaseController:
        return controller_class(db, current_user)

    return _create
