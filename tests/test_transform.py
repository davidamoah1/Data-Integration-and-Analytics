import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.transform import _validate_dataframe, transform_data


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "Order ID": ["CA-001", "CA-002", "CA-001"],
            "Order Date": ["01/01/2024", "02/15/2024", "01/01/2024"],
            "Ship Date": ["01/05/2024", "02/20/2024", "01/05/2024"],
            "Customer Name": ["  John Doe  ", "Jane Smith", "John Doe"],
            "Segment": ["Consumer", "Corporate", "Consumer"],
            "Region": ["West", "East", "West"],
            "Category": ["Furniture", "Technology", "Furniture"],
            "Sub-Category": ["Chairs", "Phones", "Chairs"],
            "Product Name": ["Office Chair", "Samsung Phone", "Office Chair"],
            "Sales": ["500.0", "1200.0", "500.0"],
            "Quantity": ["2", "1", "2"],
            "Discount": ["0.1", "0.0", "0.1"],
            "Profit": ["120.0", "300.0", "120.0"],
        }
    )


@pytest.fixture(autouse=True)
def mock_processed_path(tmp_path, monkeypatch):
    """Redirect PROCESSED_DATA_PATH to a temp file so tests don't write to disk."""
    import config

    monkeypatch.setattr(config, "PROCESSED_DATA_PATH", str(tmp_path / "cleaned.csv"))


def test_removes_duplicates(sample_dataframe):
    result = transform_data(sample_dataframe)
    assert len(result) == 2


def test_strips_whitespace(sample_dataframe):
    result = transform_data(sample_dataframe)
    assert result["customer_name"].str.startswith(" ").sum() == 0


def test_sales_is_float(sample_dataframe):
    result = transform_data(sample_dataframe)
    assert result["sales"].dtype == float


def test_quantity_is_int(sample_dataframe):
    result = transform_data(sample_dataframe)
    assert result["quantity"].dtype == int


def test_order_date_is_datetime(sample_dataframe):
    result = transform_data(sample_dataframe)
    assert pd.api.types.is_datetime64_any_dtype(result["order_date"])


def test_validation_detects_negative_sales():
    df = pd.DataFrame(
        {
            "order_id": ["A", "B"],
            "sales": [-100, 200],
            "order_date": ["2024-01-01", "2024-01-02"],
            "quantity": [1, 2],
            "discount": [0.1, 0.0],
            "profit": [10, 50],
        }
    )
    warnings = _validate_dataframe(df)
    assert any("negative sales" in w for w in warnings)


def test_validation_detects_bad_discount():
    df = pd.DataFrame(
        {
            "order_id": ["A"],
            "sales": [100],
            "order_date": ["2024-01-01"],
            "quantity": [1],
            "discount": [1.5],
            "profit": [10],
        }
    )
    warnings = _validate_dataframe(df)
    assert any("discount" in w for w in warnings)


def test_validation_passes_clean_data():
    df = pd.DataFrame(
        {
            "order_id": ["A"],
            "sales": [100],
            "order_date": ["2024-01-01"],
            "quantity": [1],
            "discount": [0.1],
            "profit": [10],
        }
    )
    warnings = _validate_dataframe(df)
    assert len(warnings) == 0
