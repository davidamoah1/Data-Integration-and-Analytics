"""Load engine — insert, update, upsert, incremental, batch load with transactions."""

from enum import Enum

import pandas as pd
from sqlalchemy import text

from config import DB_TYPE
from etl.logging_config import logger
from shared.database import get_engine
from shared.security import validate_sql_identifier


class LoadMode(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    UPSERT = "upsert"
    INCREMENTAL = "incremental"
    FULL = "full"
    BATCH = "batch"


class LoadEngine:
    """Handles loading DataFrames into database tables with multiple modes."""

    def __init__(self, engine=None, batch_size: int = 1000):
        self._engine = engine or get_engine()
        self.batch_size = batch_size

    @property
    def engine(self):
        return self._engine

    def load(
        self,
        df: pd.DataFrame,
        table: str,
        mode: LoadMode = LoadMode.INSERT,
        conflict_columns: list[str] | None = None,
        incremental_column: str | None = None,
        last_value: str | None = None,
    ) -> dict:
        """Load a DataFrame into a database table.

        Args:
            df: DataFrame to load.
            table: Target table name.
            mode: Load mode (insert, update, upsert, incremental, full, batch).
            conflict_columns: Columns to detect conflicts for upsert/update.
            incremental_column: Column for incremental loading (e.g. timestamp).
            last_value: Last loaded value for incremental mode.

        Returns:
            Dict with rows_inserted, rows_updated, rows_skipped.
        """
        if mode == LoadMode.FULL:
            return self._load_full(df, table)
        elif mode == LoadMode.INSERT or mode == LoadMode.BATCH:
            return self._load_batch(df, table)
        elif mode == LoadMode.UPSERT:
            return self._load_upsert(df, table, conflict_columns or [])
        elif mode == LoadMode.INCREMENTAL:
            return self._load_incremental(df, table, incremental_column, last_value)
        elif mode == LoadMode.UPDATE:
            return self._load_update(df, table, conflict_columns or [])
        else:
            raise ValueError(f"Unknown load mode: {mode}")

    def _load_full(self, df: pd.DataFrame, table: str) -> dict:
        validate_sql_identifier(table)
        with self._engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {table}")
            )  # nosec B608 — table validated by validate_sql_identifier above
        result = self._load_batch(df, table)
        result["mode"] = "full"
        return result

    def _load_batch(self, df: pd.DataFrame, table: str) -> dict:
        total = 0
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i : i + self.batch_size]
            batch.to_sql(table, con=self._engine, if_exists="append", index=False, method="multi")
            total += len(batch)
            logger.info(f"Load: Inserted batch {i // self.batch_size + 1} ({len(batch)} rows)")
        return {"rows_inserted": total, "rows_updated": 0, "rows_skipped": 0, "mode": "batch"}

    def _load_upsert(self, df: pd.DataFrame, table: str, conflict_columns: list[str]) -> dict:
        if not conflict_columns:
            raise ValueError("Upsert mode requires conflict_columns")
        validate_sql_identifier(table)
        for col in conflict_columns:
            validate_sql_identifier(col)

        with self._engine.connect() as conn:
            try:
                existing = pd.read_sql(
                    f"SELECT {', '.join(conflict_columns)} FROM {table}", conn
                )  # nosec B608 — table and columns validated by validate_sql_identifier above
                existing_keys = (
                    existing[conflict_columns].astype(str).agg("|".join, axis=1).tolist()
                )
            except Exception:
                existing_keys = []

        for col in df.columns:
            validate_sql_identifier(col)
        df_keys = df[conflict_columns].astype(str).agg("|".join, axis=1)
        is_new = ~df_keys.isin(existing_keys)

        new_rows = df[is_new]
        update_rows = df[~is_new]

        inserted = 0
        updated = 0

        if len(new_rows) > 0:
            result = self._load_batch(new_rows, table)
            inserted = result["rows_inserted"]

        if len(update_rows) > 0:
            if DB_TYPE == "mysql":
                for _, row in update_rows.iterrows():
                    update_cols = [c for c in df.columns if c not in conflict_columns]
                    if not update_cols:
                        continue
                    set_clause = ", ".join(f"{c} = :{c}" for c in update_cols)
                    where_clause = " AND ".join(f"{c} = :{c}" for c in conflict_columns)
                    sql = text(
                        f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                    )  # nosec B608 — table and columns validated by validate_sql_identifier, values parameterized
                    params = {c: row[c] for c in df.columns}
                    with self._engine.begin() as conn:
                        result = conn.execute(sql, params)
                        updated += result.rowcount
            else:
                for _, row in update_rows.iterrows():
                    set_clause = ", ".join(
                        f"{c} = :{c}" for c in df.columns if c not in conflict_columns
                    )
                    where_clause = " AND ".join(f"{c} = :{c}" for c in conflict_columns)
                    if not set_clause:
                        continue
                    sql = text(
                        f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                    )  # nosec B608 — table and columns validated by validate_sql_identifier, values parameterized
                    params = {c: row[c] for c in df.columns}
                    with self._engine.begin() as conn:
                        conn.execute(sql, params)
                    updated += 1

        return {
            "rows_inserted": inserted,
            "rows_updated": updated,
            "rows_skipped": 0,
            "mode": "upsert",
        }

    def _load_incremental(
        self, df: pd.DataFrame, table: str, incremental_column: str | None, last_value: str | None
    ) -> dict:
        validate_sql_identifier(table)
        if incremental_column:
            validate_sql_identifier(incremental_column)
        if not incremental_column:
            return self._load_batch(df, table)

        if last_value is not None:
            df[incremental_column] = pd.to_datetime(df[incremental_column], errors="coerce")
            last_dt = pd.to_datetime(last_value)
            df = df[df[incremental_column] > last_dt]

        result = self._load_batch(df, table)
        result["mode"] = "incremental"
        return result

    def _load_update(self, df: pd.DataFrame, table: str, conflict_columns: list[str]) -> dict:
        if not conflict_columns:
            raise ValueError("Update mode requires conflict_columns")
        validate_sql_identifier(table)
        for col in conflict_columns:
            validate_sql_identifier(col)
        for col in df.columns:
            validate_sql_identifier(col)
        updated = 0
        for _, row in df.iterrows():
            update_cols = [c for c in df.columns if c not in conflict_columns]
            if not update_cols:
                continue
            set_clause = ", ".join(f"{c} = :{c}" for c in update_cols)
            where_clause = " AND ".join(f"{c} = :{c}" for c in conflict_columns)
            sql = text(
                f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            )  # nosec B608 — table and columns validated by validate_sql_identifier, values parameterized
            params = {c: row[c] for c in df.columns}
            with self._engine.begin() as conn:
                result = conn.execute(sql, params)
                updated += result.rowcount
        return {"rows_inserted": 0, "rows_updated": updated, "rows_skipped": 0, "mode": "update"}

    def rollback(self, table: str, backup_table: str | None = None):
        """Restore a table from a backup or truncate it."""
        validate_sql_identifier(table)
        if backup_table:
            validate_sql_identifier(backup_table)
        with self._engine.begin() as conn:
            if backup_table:
                conn.execute(
                    text(f"DELETE FROM {table}")
                )  # nosec B608 — table validated by validate_sql_identifier
                conn.execute(
                    text(f"INSERT INTO {table} SELECT * FROM {backup_table}")
                )  # nosec B608 — table and backup_table validated by validate_sql_identifier
            else:
                conn.execute(
                    text(f"DELETE FROM {table}")
                )  # nosec B608 — table validated by validate_sql_identifier
        logger.info(f"Load: Rolled back table {table}")
