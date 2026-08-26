"""Base service layer â€” business logic abstraction.

Services orchestrate business rules, validation, and cross-cutting
concerns. They receive repositories via constructor injection and
never touch the database session directly.

Architecture layer:
    API Routes â†’ Service Layer â†’ Repository Layer â†’ Database

Services raise domain exceptions (from shared.exceptions) which the
API layer catches and converts to HTTP responses.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session as DbSession

from shared.exceptions import NotFoundError, ValidationError
from shared.repositories import BaseRepository

T = TypeVar("T")
R = TypeVar("R", bound=BaseRepository)


class BaseService(Generic[R]):
    """Base service providing common business logic patterns.

    Subclasses provide the repository class and implement domain-specific
    methods on top of the standard CRUD operations.

    Usage:
        class CaptureDocumentService(BaseService[DocumentRepository]):
            repository_class = DocumentRepository

            def approve_document(self, doc_id, org_id, user_id):
                ...
    """

    repository_class: type[BaseRepository]

    def __init__(self, db: DbSession):
        self.db = db
        self.repository: BaseRepository = self.repository_class(db)

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _get_or_404(self, id: int, message: str = "Resource not found") -> Any:
        instance = self.repository.get_by_id(id)
        if not instance:
            raise NotFoundError(message)
        return instance

    def _validate_required(self, data: dict, fields: list[str]) -> None:
        for field in fields:
            if field not in data or data[field] is None or data[field] == "":
                raise ValidationError(f"Field '{field}' is required")

    def commit(self) -> None:
        self.db.commit()

    # â”€â”€ Standard CRUD (can be overridden) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get(self, id: int) -> Any:
        return self._get_or_404(id)

    def list(self, **kwargs) -> list[Any]:
        return self.repository.list(**kwargs)

    def list_paginated(self, **kwargs) -> tuple[list[Any], int]:
        return self.repository.list_paginated(**kwargs)

    def create(self, **kwargs) -> Any:
        return self.repository.create(**kwargs)

    def update(self, id: int, **kwargs) -> Any:
        instance = self._get_or_404(id)
        return self.repository.update_instance(instance, **kwargs)

    def delete(self, id: int) -> bool:
        return self.repository.delete(id)
