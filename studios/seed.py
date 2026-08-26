"""Seed data for Data Intelligence Studios."""

from __future__ import annotations

from sqlalchemy.orm import Session as DbSession

from studios.industry_service import seed_industry_data


def seed_studios_data(db: DbSession) -> None:
    """Seed all studios data (industry KPIs, templates)."""
    seed_industry_data(db)
