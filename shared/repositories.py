"""Base repository layer — generic CRUD operations for SQLAlchemy models.

All domain repositories inherit from BaseRepository to get standard
create, read, update, delete, and list operations for free. Domain-
specific queries are added in subclasses.

Architecture layer:
    API Routes → Service Layer → Repository Layer → Database

The repository layer is the ONLY place that touches SQLAlchemy session
objects directly. Services receive repositories via dependency injection
and never execute raw queries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session as DbSession

from shared.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository providing CRUD operations for a SQLAlchemy model.

    Usage:
        class DocumentRepository(BaseRepository[CaptureDocument]):
            model = CaptureDocument

            def get_by_batch(self, batch_id, ...):
                ...
    """

    model: type[T]

    def __init__(self, db: DbSession):
        self.db = db

    # ── Read ────────────────────────────────────────────────────────────

    def get_by_id(self, id: int) -> T | None:
        return self.db.execute(
            select(self.model).where(self.model.id == id)
        ).scalar_one_or_none()

    def get_by_field(self, field: str, value: Any) -> T | None:
        column = getattr(self.model, field)
        return self.db.execute(
            select(self.model).where(column == value)
        ).scalar_one_or_none()

    def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[T]:
        stmt = select(self.model)
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                stmt = stmt.order_by(column.desc() if order_desc else column)
        else:
            stmt = stmt.order_by(self.model.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, *, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        return self.db.execute(stmt).scalar() or 0

    def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> tuple[list[T], int]:
        offset = (page - 1) * page_size
        items = self.list(
            filters=filters, order_by=order_by, order_desc=order_desc,
            limit=page_size, offset=offset,
        )
        total = self.count(filters=filters)
        return items, total

    def exists(self, id: int) -> bool:
        return self.get_by_id(id) is not None

    # ── Create ──────────────────────────────────────────────────────────

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        return instance

    def create_from_model(self, instance: T) -> T:
        self.db.add(instance)
        self.db.flush()
        return instance

    # ── Update ──────────────────────────────────────────────────────────

    def update(self, id: int, **kwargs) -> T | None:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        self.db.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        self.db.flush()
        return self.get_by_id(id)

    def update_instance(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.flush()
        return instance

    # ── Delete ──────────────────────────────────────────────────────────

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if not instance:
            return False
        self.db.delete(instance)
        self.db.flush()
        return True

    def delete_hard(self, instance: T) -> None:
        self.db.delete(instance)
        self.db.flush()

    # ── Bulk ────────────────────────────────────────────────────────────

    def bulk_create(self, instances: list[T]) -> list[T]:
        self.db.add_all(instances)
        self.db.flush()
        return instances

    def bulk_update(self, ids: list[int], **kwargs) -> int:
        if not ids:
            return 0
        result = self.db.execute(
            update(self.model).where(self.model.id.in_(ids)).values(**kwargs)
        )
        self.db.flush()
        return result.rowcount

    # ── Session ─────────────────────────────────────────────────────────

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: T) -> T:
        self.db.refresh(instance)
        return instance
