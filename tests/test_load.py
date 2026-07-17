"""Tests for the load module."""

import os
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_sqlite_db(tmp_path, monkeypatch):
    """Create a temporary SQLite database and patch config."""
    db_path = str(tmp_path / "test.db")
    db_url = f"sqlite:///{db_path}"

    import config

    monkeypatch.setattr(config, "DB_URL", db_url)
    monkeypatch.setattr(config, "DB_TYPE", "sqlite")

    # Patch DB_URL in modules that imported it at module level
    from etl import load as load_mod

    monkeypatch.setattr(load_mod, "DB_URL", db_url)
    monkeypatch.setattr(load_mod, "DB_TYPE", "sqlite")

    from database.db_setup import Base

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    return db_url


@pytest.fixture
def sample_clean_df():
    """Return a cleaned DataFrame ready for loading."""
    return pd.DataFrame(
        {
            "order_id": ["CA-001", "CA-002", "CA-003"],
            "order_date": pd.to_datetime(["2024-01-01", "2024-02-15", "2024-03-20"]),
            "ship_date": pd.to_datetime(["2024-01-05", "2024-02-20", "2024-03-25"]),
            "customer_name": ["John Doe", "Jane Smith", "Bob Wilson"],
            "segment": ["Consumer", "Corporate", "Consumer"],
            "region": ["West", "East", "Central"],
            "category": ["Furniture", "Technology", "Office Supplies"],
            "sub_category": ["Chairs", "Phones", "Paper"],
            "product_name": ["Office Chair", "Samsung Phone", "A4 Paper"],
            "sales": [500.0, 1200.0, 50.0],
            "quantity": [2, 1, 5],
            "discount": [0.1, 0.0, 0.2],
            "profit": [120.0, 300.0, 15.0],
        }
    )


def test_load_inserts_new_records(temp_sqlite_db, sample_clean_df):
    from etl.load import load_data

    count = load_data(sample_clean_df)
    assert count == 3


def test_load_skips_duplicates(temp_sqlite_db, sample_clean_df):
    from etl.load import load_data

    load_data(sample_clean_df)
    count = load_data(sample_clean_df)
    assert count == 0


def test_load_returns_zero_for_empty(temp_sqlite_db, sample_clean_df):
    from etl.load import load_data

    load_data(sample_clean_df)
    empty_df = sample_clean_df.iloc[0:0]
    count = load_data(empty_df)
    assert count == 0
