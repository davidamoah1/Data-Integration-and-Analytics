from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    sort: str | None = None
    filters: dict[str, str | int | float | bool] = Field(default_factory=dict)


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class APIError(BaseModel):
    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    contract_version: str = "1.0.0"
