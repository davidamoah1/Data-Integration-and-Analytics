import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_extract_returns_dataframe(tmp_path, monkeypatch):
    dummy_csv = tmp_path / "superstore.csv"
    dummy_csv.write_text(
        "Order ID,Order Date,Ship Date,Customer Name,Segment,Region,Category,Sub-Category,Product Name,Sales,Quantity,Discount,Profit\n"
        "CA-001,2024-01-01,2024-01-05,John Doe,Consumer,West,Furniture,Chairs,Office Chair,500.0,2,0.1,120.0\n"
    )

    from etl import extract

    monkeypatch.setattr(extract, "RAW_DATA_PATH", str(dummy_csv))

    df = extract.extract_data()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_extract_raises_if_file_missing(monkeypatch):
    from etl import extract

    monkeypatch.setattr(extract, "RAW_DATA_PATH", "/nonexistent/path.csv")

    with pytest.raises(FileNotFoundError):
        extract.extract_data()
