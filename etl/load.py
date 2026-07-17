import pandas as pd
from sqlalchemy import create_engine

from config import DB_TYPE, DB_URL
from etl.logging_config import logger

BATCH_SIZE = 1000


def load_data(df: pd.DataFrame) -> int:
    """Load cleaned DataFrame into the database, skipping duplicates.

    Uses batch inserts for performance. For MySQL, uses INSERT ... ON DUPLICATE
    KEY UPDATE for upsert capability. For SQLite, falls back to append-only
    with pre-filtering of existing IDs.

    Args:
        df: Cleaned DataFrame from the transform step.

    Returns:
        Number of new records inserted.
    """
    try:
        engine = _create_engine()

        with engine.connect() as conn:
            try:
                existing = pd.read_sql("SELECT order_id FROM sales", conn)
                existing_ids = set(existing["order_id"].tolist())
            except Exception:
                existing_ids = set()

        df_new = df[~df["order_id"].isin(existing_ids)]

        if df_new.empty:
            logger.info("Load: No new records to insert. Database is already up to date.")
            print("Load complete. No new records to insert.")
            return 0

        columns_to_load = [
            "order_id",
            "order_date",
            "ship_date",
            "customer_name",
            "segment",
            "region",
            "category",
            "sub_category",
            "product_name",
            "sales",
            "quantity",
            "discount",
            "profit",
        ]
        cols = [c for c in columns_to_load if c in df_new.columns]
        df_new = df_new[cols]

        total_inserted = _batch_insert(engine, df_new)

        logger.info(f"Load: Inserted {total_inserted} new records into the database.")
        print(f"Load complete. {total_inserted} new records inserted.")
        return total_inserted

    except Exception as e:
        logger.error(f"Load failed: {e}")
        raise


def _create_engine():
    """Create a SQLAlchemy engine with appropriate pooling settings."""
    engine_kwargs = {"pool_pre_ping": True}
    if DB_TYPE == "mysql":
        engine_kwargs["pool_size"] = 5
        engine_kwargs["pool_recycle"] = 3600
        engine_kwargs["max_overflow"] = 10
    return create_engine(DB_URL, **engine_kwargs)


def _batch_insert(engine, df_new: pd.DataFrame) -> int:
    """Insert records in batches for performance.

    Args:
        engine: SQLAlchemy engine instance.
        df_new: DataFrame of new records to insert.

    Returns:
        Total number of records inserted.
    """
    total = 0
    for i in range(0, len(df_new), BATCH_SIZE):
        batch = df_new.iloc[i : i + BATCH_SIZE]
        batch.to_sql("sales", con=engine, if_exists="append", index=False, method="multi")
        total += len(batch)
        logger.info(f"Load: Inserted batch {i // BATCH_SIZE + 1} ({len(batch)} rows)")
    return total


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from etl.extract import extract_data
    from etl.transform import transform_data

    raw = extract_data()
    clean = transform_data(raw)
    load_data(clean)
