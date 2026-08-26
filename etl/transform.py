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

    if "sales" in df.columns:
        neg_sales = (df["sales"] < 0).sum()
        if neg_sales > 0:
            warnings.append(f"{neg_sales} rows have negative sales values")

    if "profit" in df.columns and "sales" in df.columns:
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

        # Drop full duplicate rows (use all columns if no ID column exists)
        before = len(df)
        id_col = None
        for candidate in ("order_id", "id", "record_id", "transaction_id"):
            if candidate in df.columns:
                id_col = candidate
                break
        if id_col:
            df = df.drop_duplicates(subset=[id_col], keep="first")
        else:
            df = df.drop_duplicates(keep="first")
        after = len(df)
        logger.info(f"Transform: Removed {before - after} duplicate rows.")

        # Drop rows where key identifier columns are missing (only if they exist)
        # Only drop if order_id exists â€” don't assume sales/order_date are present
        if "order_id" in df.columns:
            df = df.dropna(subset=["order_id"])
        # For sales-specific datasets, also drop rows missing critical sales data
        if "sales" in df.columns and "order_date" in df.columns:
            df = df.dropna(subset=["sales", "order_date"])

        # Fix data types â€” only for columns that exist
        numeric_cols = ("sales", "quantity", "discount", "profit")
        for col in numeric_cols:
            if col in df.columns:
                if col == "quantity":
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Standardize date format for any column that looks like a date
        for date_col in (
            "order_date",
            "ship_date",
            "sale_date",
            "transaction_date",
            "admission_date",
            "visit_date",
            "enrollment_date",
            "date",
        ):
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

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
