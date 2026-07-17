"""Tests for the SalesRepository."""

import os
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Create a SalesRepository with a temporary SQLite database."""
    db_path = str(tmp_path / "test_repo.db")
    db_url = f"sqlite:///{db_path}"

    import config

    monkeypatch.setattr(config, "DB_URL", db_url)
    monkeypatch.setattr(config, "DB_TYPE", "sqlite")

    from database.db_setup import Base

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    from database.repositories import SalesRepository

    return SalesRepository(engine=engine)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "order_id": ["CA-001", "CA-002", "CA-003"],
            "order_date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "ship_date": pd.to_datetime(["2024-01-05", "2024-02-05", "2024-03-05"]),
            "customer_name": ["John", "Jane", "Bob"],
            "segment": ["Consumer", "Corporate", "Consumer"],
            "region": ["West", "East", "West"],
            "category": ["Furniture", "Technology", "Furniture"],
            "sub_category": ["Chairs", "Phones", "Tables"],
            "product_name": ["Chair", "Phone", "Table"],
            "sales": [500.0, 1200.0, 300.0],
            "quantity": [2, 1, 3],
            "discount": [0.1, 0.0, 0.05],
            "profit": [120.0, 300.0, 60.0],
        }
    )


def test_get_all_sales_empty(repo):
    df = repo.get_all_sales()
    assert len(df) == 0


def test_insert_and_retrieve(repo, sample_df):
    repo.insert_sales(sample_df)
    df = repo.get_all_sales()
    assert len(df) == 3


def test_get_existing_order_ids(repo, sample_df):
    repo.insert_sales(sample_df)
    ids = repo.get_existing_order_ids()
    assert "CA-001" in ids
    assert "CA-002" in ids


def test_get_kpis(repo, sample_df):
    repo.insert_sales(sample_df)
    kpis = repo.get_kpis()
    assert kpis["total_sales"] == 2000.0
    assert kpis["total_profit"] == 480.0
    assert kpis["total_orders"] == 3


def test_get_kpis_filtered_by_region(repo, sample_df):
    repo.insert_sales(sample_df)
    kpis = repo.get_kpis(region="West")
    assert kpis["total_sales"] == 800.0
    assert kpis["total_orders"] == 2


def test_get_distinct_values(repo, sample_df):
    repo.insert_sales(sample_df)
    regions = repo.get_distinct_values("region")
    assert sorted(regions) == ["East", "West"]


def test_get_distinct_values_rejects_invalid_column(repo):
    with pytest.raises(ValueError):
        repo.get_distinct_values("order_id")


def test_get_record_count(repo, sample_df):
    repo.insert_sales(sample_df)
    assert repo.get_record_count() == 3


def test_get_date_range(repo, sample_df):
    repo.insert_sales(sample_df)
    min_date, max_date = repo.get_date_range()
    assert min_date is not None
    assert max_date is not None


def test_get_sales_filtered_by_category(repo, sample_df):
    repo.insert_sales(sample_df)
    df = repo.get_sales_filtered(category="Furniture")
    assert len(df) == 2
