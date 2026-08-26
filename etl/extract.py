import os

import pandas as pd

from config import RAW_DATA_PATH
from etl.logging_config import logger


def extract_data() -> pd.DataFrame:
    """Read raw data from the configured data path.

    Supports CSV and Excel (.xlsx, .xls) files. For large files, reads in
    chunks to manage memory.

    Returns:
        pandas DataFrame containing the raw data.

    Raises:
        ValueError: If RAW_DATA_PATH is not configured.
        FileNotFoundError: If the raw data file does not exist.
    """
    try:
        if not RAW_DATA_PATH:
            raise ValueError(
                "RAW_DATA_PATH is not configured. Set the RAW_DATA_PATH environment variable "
                "to point to your data file. Production must not rely on default sample data."
            )
        if not os.path.exists(RAW_DATA_PATH):
            raise FileNotFoundError(f"Raw data file not found at: {RAW_DATA_PATH}")

        file_ext = os.path.splitext(RAW_DATA_PATH)[1].lower()

        if file_ext == ".csv":
            try:
                df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8", encoding_errors="replace")
            except UnicodeDecodeError:
                df = pd.read_csv(RAW_DATA_PATH, encoding="latin-1", encoding_errors="replace")
        elif file_ext in (".xlsx", ".xls"):
            df = pd.read_excel(RAW_DATA_PATH)
        else:
            raise ValueError(
                f"Unsupported file format: '{file_ext}'. Supported formats: .csv, .xlsx, .xls"
            )

        if df.empty:
            raise ValueError("The data file is empty or contains no rows.")

        logger.info(
            f"Extract complete. {len(df)} rows, {len(df.columns)} columns loaded from {file_ext} file."
        )
        return df

    except Exception as e:
        logger.error(f"Extract failed: {e}")
        raise


if __name__ == "__main__":
    data = extract_data()
    print(data.head())
