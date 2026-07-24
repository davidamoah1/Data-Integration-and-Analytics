import os

import pandas as pd

from config import PROCESSED_DATA_PATH
from etl.logging_config import logger


def _validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Validate the DataFrame for data quality issues.

    Args:
        df: DataFrame to validate.

    Returns:
        List of validation warning messages.
    """
    warnings = []

    required_cols = ["order_id", "sales", "order_date"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        warnings.append(f"Missing required columns: {missing}")

    if "sales" in df.columns:
        neg_sales = (df["sales"] < 0).sum()
        if neg_sales > 0:
            warnings.append(f"{neg_sales} rows have negative sales values")

    if "profit" in df.columns:
        extreme_profit = (df["profit"].abs() > df["sales"] * 10).sum()
        if extreme_profit > 0:
            warnings.append(f"{extreme_profit} rows have profit values exceeding 10x sales")

    if "quantity" in df.columns:
        neg_qty = (df["quantity"] < 0).sum()
        if neg_qty > 0:
            warnings.append(f"{neg_qty} rows have negative quantity values")

    if "discount" in df.columns:
        bad_discount = ((df["discount"] < 0) | (df["discount"] > 1)).sum()
        if bad_discount > 0:
            warnings.append(f"{bad_discount} rows have discount values outside [0, 1]")

    return warnings


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform the raw DataFrame.

    Performs column standardization, duplicate removal, missing value handling,
    type conversion, date parsing, and string trimming. Validates data quality
    and logs warnings for anomalies.

    Args:
        df: Raw DataFrame from the extract step.

    Returns:
        Cleaned and processed DataFrame.
    """
    try:
        # Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")

        # Drop full duplicate rows
        before = len(df)
        df = df.drop_duplicates(subset=["order_id"], keep="first")
        after = len(df)
        logger.info(f"Transform: Removed {before - after} duplicate rows.")

        # Drop rows where key columns are missing
        df = df.dropna(subset=["order_id", "sales", "order_date"])

        # Fix data types
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0.0)
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)

        # Standardize date format (keep as datetime for proper DB Date columns)
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")

        # Trim whitespace from string columns
        str_cols = [
            "customer_name",
            "segment",
            "region",
            "category",
            "sub_category",
            "product_name",
        ]
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Validate data quality
        warnings = _validate_dataframe(df)
        for w in warnings:
            logger.warning(f"Transform validation: {w}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)

        # Save processed data
        df.to_csv(PROCESSED_DATA_PATH, index=False)
        logger.info(f"Transform complete. {len(df)} rows cleaned and saved.")
        return df

    except Exception as e:
        logger.error(f"Transform failed: {e}")
        raise


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from etl.extract import extract_data

    raw = extract_data()
    clean = transform_data(raw)
    print(clean.head())
