"""Repository pattern for database access.

Provides a clean abstraction over SQLAlchemy operations, separating
data access logic from business logic.
"""

from datetime import date

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import DB_TYPE
from etl.logging_config import logger
from shared.database import get_engine


class SalesRepository:
    """Repository for sales data access operations."""

    def __init__(self, engine=None):
        """Initialize with an optional engine, or create one from config.

        Args:
            engine: SQLAlchemy engine. If None, creates one from config.
        """
        if engine is not None:
            self.engine = engine
        else:
            self.engine = get_engine()

    def get_all_sales(self) -> pd.DataFrame:
        """Retrieve all sales records as a DataFrame.

        Returns:
            DataFrame containing all sales records.
        """
        with self.engine.connect() as conn:
            return pd.read_sql("SELECT * FROM sales", conn)

    def get_sales_filtered(
        self,
        region: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> pd.DataFrame:
        """Retrieve sales records with optional filters.

        Args:
            region: Filter by region name.
            category: Filter by category name.
            date_from: Filter orders from this date (inclusive).
            date_to: Filter orders up to this date (inclusive).

        Returns:
            Filtered DataFrame of sales records.
        """
        query = "SELECT * FROM sales WHERE 1=1"
        params: dict = {}

        if region:
            query += " AND region = :region"
            params["region"] = region
        if category:
            query += " AND category = :category"
            params["category"] = category
        if date_from:
            query += " AND order_date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND order_date <= :date_to"
            params["date_to"] = date_to

        with self.engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)

    def get_sales_paginated(
        self,
        region: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[pd.DataFrame, int]:
        """Retrieve a page of sales records with optional filters.

        Uses SQL-level LIMIT/OFFSET for efficient pagination instead of
        loading all records into memory.

        Args:
            region: Filter by region name.
            category: Filter by category name.
            date_from: Filter orders from this date (inclusive).
            date_to: Filter orders up to this date (inclusive).
            page: Page number (1-indexed).
            page_size: Number of records per page.

        Returns:
            Tuple of (DataFrame of page records, total count).
        """
        where = " WHERE 1=1"
        params: dict = {}

        if region:
            where += " AND region = :region"
            params["region"] = region
        if category:
            where += " AND category = :category"
            params["category"] = category
        if date_from:
            where += " AND order_date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            where += " AND order_date <= :date_to"
            params["date_to"] = date_to

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        count_query = f"SELECT COUNT(*) as total FROM sales{where}"
        data_query = (
            f"SELECT * FROM sales{where} ORDER BY order_date DESC " f"LIMIT :limit OFFSET :offset"
        )

        with self.engine.connect() as conn:
            total = int(pd.read_sql(text(count_query), conn, params=params).iloc[0]["total"])
            df = pd.read_sql(text(data_query), conn, params=params)
        return df, total

    def get_existing_order_ids(self) -> set:
        """Get the set of all order_ids currently in the database.

        Returns:
            Set of order_id strings.
        """
        with self.engine.connect() as conn:
            try:
                existing = pd.read_sql("SELECT order_id FROM sales", conn)
                return set(existing["order_id"].tolist())
            except Exception:
                return set()

    def insert_sales(self, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Insert sales records in batches.

        Args:
            df: DataFrame of records to insert.
            batch_size: Number of records per batch.

        Returns:
            Number of records inserted.
        """
        total = 0
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i : i + batch_size]
            batch.to_sql("sales", con=self.engine, if_exists="append", index=False, method="multi")
            total += len(batch)
            logger.info(f"Repository: Inserted batch {i // batch_size + 1} ({len(batch)} rows)")
        return total

    def get_kpis(
        self,
        region: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        """Compute aggregate KPIs from the database.

        Args:
            region: Optional region filter.
            category: Optional category filter.
            date_from: Optional start date.
            date_to: Optional end date.

        Returns:
            Dict with keys: total_sales, total_profit, total_orders,
            avg_order_value, margin_pct.
        """
        query = """
            SELECT
                COALESCE(SUM(sales), 0) as total_sales,
                COALESCE(SUM(profit), 0) as total_profit,
                COUNT(DISTINCT order_id) as total_orders,
                COALESCE(AVG(sales), 0) as avg_order_value
            FROM sales WHERE 1=1
        """
        params: dict = {}

        if region:
            query += " AND region = :region"
            params["region"] = region
        if category:
            query += " AND category = :category"
            params["category"] = category
        if date_from:
            query += " AND order_date >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND order_date <= :date_to"
            params["date_to"] = date_to

        with self.engine.connect() as conn:
            result = pd.read_sql(text(query), conn, params=params)
            row = result.iloc[0]
            total_sales = float(row["total_sales"])
            total_profit = float(row["total_profit"])
            total_orders = int(row["total_orders"])
            avg_order = float(row["avg_order_value"])
            margin_pct = (total_profit / total_sales * 100) if total_sales > 0 else 0.0

        return {
            "total_sales": total_sales,
            "total_profit": total_profit,
            "total_orders": total_orders,
            "avg_order_value": avg_order,
            "margin_pct": margin_pct,
        }

    def get_distinct_values(self, column: str) -> list:
        """Get distinct values for a column.

        Args:
            column: Column name (e.g., 'region', 'category').

        Returns:
            Sorted list of distinct values.
        """
        allowed = {"region", "category", "segment", "sub_category"}
        if column not in allowed:
            raise ValueError(f"Column '{column}' not allowed for distinct query.")
        query = f"SELECT DISTINCT {column} FROM sales WHERE {column} IS NOT NULL ORDER BY {column}"
        with self.engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
            return result[column].tolist()

    def get_date_range(self) -> tuple:
        """Get the min and max order dates in the database.

        Returns:
            Tuple of (min_date, max_date) or (None, None) if no data.
        """
        with self.engine.connect() as conn:
            try:
                result = pd.read_sql(
                    "SELECT MIN(order_date) as min_date, MAX(order_date) as max_date FROM sales",
                    conn,
                )
                row = result.iloc[0]
                return row["min_date"], row["max_date"]
            except Exception:
                return None, None

    def get_record_count(self) -> int:
        """Get total number of records in the sales table.

        Returns:
            Integer count of records.
        """
        with self.engine.connect() as conn:
            result = pd.read_sql("SELECT COUNT(*) as cnt FROM sales", conn)
            return int(result.iloc[0]["cnt"])


class PipelineRunRepository:
    """Repository for pipeline run metadata."""

    def __init__(self, engine=None):
        """Initialize with an optional engine.

        Args:
            engine: SQLAlchemy engine. If None, creates one from config.
        """
        if engine is not None:
            self.engine = engine
        else:
            self.engine = get_engine()

    def create_run(self, run_id: str) -> int:
        """Create a new pipeline run record.

        Args:
            run_id: Unique identifier for this run.

        Returns:
            Database row ID.
        """
        with Session(self.engine) as session:
            result = session.execute(
                text("INSERT INTO pipeline_runs (run_id, status) VALUES (:run_id, 'running')"),
                {"run_id": run_id},
            )
            session.commit()
            return result.lastrowid

    def complete_run(
        self,
        run_id: str,
        rows_extracted: int = 0,
        rows_transformed: int = 0,
        rows_loaded: int = 0,
        duplicates_removed: int = 0,
    ):
        """Mark a pipeline run as completed with metrics.

        Args:
            run_id: Unique run identifier.
            rows_extracted: Number of rows extracted.
            rows_transformed: Number of rows after transformation.
            rows_loaded: Number of rows inserted into DB.
            duplicates_removed: Number of duplicate rows removed.
        """
        with Session(self.engine) as session:
            session.execute(
                text("""UPDATE pipeline_runs
                       SET status = 'completed',
                           completed_at = CURRENT_TIMESTAMP,
                           rows_extracted = :re,
                           rows_transformed = :rt,
                           rows_loaded = :rl,
                           duplicates_removed = :dr
                       WHERE run_id = :run_id"""),
                {
                    "run_id": run_id,
                    "re": rows_extracted,
                    "rt": rows_transformed,
                    "rl": rows_loaded,
                    "dr": duplicates_removed,
                },
            )
            session.commit()

    def fail_run(self, run_id: str, error_message: str):
        """Mark a pipeline run as failed.

        Args:
            run_id: Unique run identifier.
            error_message: Error description.
        """
        with Session(self.engine) as session:
            session.execute(
                text("""UPDATE pipeline_runs
                       SET status = 'failed',
                           completed_at = CURRENT_TIMESTAMP,
                           error_message = :err
                       WHERE run_id = :run_id"""),
                {"run_id": run_id, "err": error_message[:1000]},
            )
            session.commit()

    def get_recent_runs(self, limit: int = 10) -> pd.DataFrame:
        """Get recent pipeline runs.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            DataFrame of recent pipeline runs.
        """
        with self.engine.connect() as conn:
            return pd.read_sql(
                text("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT :limit"),
                conn,
                params={"limit": limit},
            )
