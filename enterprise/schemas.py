"""Pydantic schemas for platform domain — templates, collaboration, branding."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --- Template schemas --------------------------------------------------------


class TemplateCreate(BaseModel):
    template_type: str = Field(min_length=1, max_length=50)
    industry: str | None = Field(None, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    author: str | None = None
    version: str = "1.0.0"
    content: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    is_public: bool = True
    is_featured: bool = False


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    content: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_public: bool | None = None
    is_featured: bool | None = None


class TemplateResponse(BaseModel):
    id: int
    template_type: str
    industry: str | None
    name: str
    description: str | None
    author: str | None
    version: str
    tags: list[str]
    is_public: bool
    is_featured: bool
    install_count: int
    rating: float
    created_at: datetime
    updated_at: datetime


# --- Comment schemas ---------------------------------------------------------


class CommentCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=50)
    resource_id: int
    parent_id: int | None = None
    body: str = Field(min_length=1)
    mentions: list[int] = Field(default_factory=list)


class CommentResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: int
    author_id: int
    parent_id: int | None
    body: str
    mentions: list[int]
    is_resolved: bool
    created_at: datetime
    updated_at: datetime


# --- Share schemas -----------------------------------------------------------


class ShareCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=50)
    resource_id: int
    shared_with_type: str = Field(default="user", max_length=20)
    shared_with_id: int
    permission: str = Field(default="view", max_length=20)


class ShareResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: int
    shared_by: int
    shared_with_type: str
    shared_with_id: int
    permission: str
    created_at: datetime


# --- Activity schemas --------------------------------------------------------


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    resource_type: str | None
    resource_id: int | None
    metadata: dict[str, Any]
    created_at: datetime


# --- Branding schemas --------------------------------------------------------


class BrandingCreate(BaseModel):
    logo_url: str | None = Field(None, max_length=500)
    primary_color: str | None = Field(None, max_length=20)
    secondary_color: str | None = Field(None, max_length=20)
    accent_color: str | None = Field(None, max_length=20)
    theme_mode: str = Field(default="dark", max_length=20)
    company_name: str | None = Field(None, max_length=255)
    company_tagline: str | None = Field(None, max_length=500)
    email_footer: str | None = None
    report_header_text: str | None = Field(None, max_length=255)
    report_footer_text: str | None = Field(None, max_length=255)
    custom_css: str | None = None


class BrandingUpdate(BrandingCreate):
    pass


class BrandingResponse(BaseModel):
    id: int
    organization_id: int
    logo_url: str | None
    primary_color: str | None
    secondary_color: str | None
    accent_color: str | None
    theme_mode: str
    company_name: str | None
    company_tagline: str | None
    email_footer: str | None
    report_header_text: str | None
    report_footer_text: str | None
    custom_css: str | None
    created_at: datetime
    updated_at: datetime


# --- Search schemas ----------------------------------------------------------


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    resource_types: list[str] | None = None
    limit: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    resource_type: str
    resource_id: int
    title: str
    description: str | None
    url: str | None
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
