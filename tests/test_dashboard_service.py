"""Tests for the DashboardDataService."""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.dashboard_data_service import DashboardDataService


def test_detect_columns_finds_sales():
    df = pd.DataFrame({"Revenue": [100], "Profit": [20], "Order Date": ["2024-01-01"]})
    mapping = DashboardDataService.detect_columns(df)
    assert "sales" in mapping
    assert mapping["sales"] == "Revenue"
    assert "profit" in mapping
    assert "order_date" in mapping


def test_detect_columns_handles_spaces():
    df = pd.DataFrame({"Total Sales": [100], "Order ID": ["A1"]})
    mapping = DashboardDataService.detect_columns(df)
    assert "sales" in mapping
    assert "order_id" in mapping


def test_detect_columns_returns_empty_for_no_match():
    df = pd.DataFrame({"foo": [1], "bar": [2]})
    mapping = DashboardDataService.detect_columns(df)
    assert "sales" not in mapping


def test_clean_df_standardizes_columns():
    df = pd.DataFrame(
        {
            "Order ID": ["A1", "A2", "A1"],
            "Sales": ["100.0", "200.0", "100.0"],
            "Order Date": ["2024-01-01", "2024-02-01", "2024-01-01"],
        }
    )
    mapping = DashboardDataService.detect_columns(df)
    cleaned = DashboardDataService.clean_df(df, mapping)
    assert "order_id" in cleaned.columns
    assert "sales" in cleaned.columns
    assert len(cleaned) == 2  # duplicate removed


def test_clean_df_converts_types():
    df = pd.DataFrame(
        {
            "Order ID": ["A1"],
            "Sales": ["100.5"],
            "Quantity": ["3"],
            "Order Date": ["2024-01-01"],
        }
    )
    mapping = DashboardDataService.detect_columns(df)
    cleaned = DashboardDataService.clean_df(df, mapping)
    assert cleaned["sales"].dtype == float
    assert cleaned["quantity"].dtype == int
    assert pd.api.types.is_datetime64_any_dtype(cleaned["order_date"])
