import os

import pandas as pd

from config import RAW_DATA_PATH
from etl.logging_config import logger


def extract_data() -> pd.DataFrame:
    """Read raw CSV data from the configured data path.

    Returns:
        pandas DataFrame containing the raw data.

    Raises:
        FileNotFoundError: If the raw data file does not exist.
    """
    try:
        if not os.path.exists(RAW_DATA_PATH):
            raise FileNotFoundError(f"Raw data file not found at: {RAW_DATA_PATH}")

        df = pd.read_csv(RAW_DATA_PATH, encoding="latin-1")
        logger.info(f"Extract complete. {len(df)} rows loaded.")
        return df

    except Exception as e:
        logger.error(f"Extract failed: {e}")
        raise


if __name__ == "__main__":
    data = extract_data()
    print(data.head())
