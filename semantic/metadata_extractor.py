"""MODULE 1 â€” Metadata Extraction.

Automatically discovers schema, data types, constraints, statistics,
and value distributions from a pandas DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd


@dataclass
class ColumnMetadata:
    """Metadata for a single column."""

    name: str
    dtype: str
    nullable: bool = True
    unique_count: int = 0
    null_count: int = 0
    null_pct: float = 0.0
    unique_pct: float = 0.0
    cardinality: str = "unknown"  # low, medium, high
    min_value: object | None = None
    max_value: object | None = None
    mean_value: float | None = None
    std_value: float | None = None
    sample_values: list = field(default_factory=list)
    value_distribution: dict = field(default_factory=dict)
    is_primary_key: bool = False
    is_foreign_key: bool = False
    constraints: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "nullable": self.nullable,
            "unique_count": self.unique_count,
            "null_count": self.null_count,
            "null_pct": round(self.null_pct, 2),
            "unique_pct": round(self.unique_pct, 2),
            "cardinality": self.cardinality,
            "min_value": str(self.min_value) if self.min_value is not None else None,
            "max_value": str(self.max_value) if self.max_value is not None else None,
            "mean_value": round(self.mean_value, 4) if self.mean_value is not None else None,
            "std_value": round(self.std_value, 4) if self.std_value is not None else None,
            "sample_values": [str(v) for v in self.sample_values[:10]],
            "value_distribution": {
                str(k): v for k, v in list(self.value_distribution.items())[:20]
            },
            "is_primary_key": self.is_primary_key,
            "is_foreign_key": self.is_foreign_key,
            "constraints": self.constraints,
        }


@dataclass
class TableMetadata:
    """Metadata for an entire table/dataset."""

    name: str
    row_count: int
    column_count: int
    columns: list[ColumnMetadata] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[dict] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [c.to_dict() for c in self.columns],
            "primary_keys": self.primary_keys,
            "foreign_keys": self.foreign_keys,
            "indexes": self.indexes,
            "created_at": self.created_at,
        }


class MetadataExtractor:
    """Extracts metadata from a pandas DataFrame."""

    @staticmethod
    def extract(df: pd.DataFrame, table_name: str = "uploaded_dataset") -> TableMetadata:
        """Extract full metadata from a DataFrame.

        Args:
            df: The DataFrame to analyze.
            table_name: Name to assign to the table.

        Returns:
            TableMetadata with all discovered information.
        """
        columns = []
        primary_keys = []

        for col_name in df.columns:
            col_meta = MetadataExtractor._extract_column(df, col_name)
            columns.append(col_meta)
            if col_meta.is_primary_key:
                primary_keys.append(col_name)

        # Detect foreign keys heuristically
        foreign_keys = MetadataExtractor._detect_foreign_keys(df, columns)

        return TableMetadata(
            name=table_name,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            indexes=[],  # Not applicable for DataFrames
        )

    @staticmethod
    def _extract_column(df: pd.DataFrame, col_name: str) -> ColumnMetadata:
        """Extract metadata for a single column."""
        series = df[col_name]
        dtype = str(series.dtype)
        null_count = int(series.isnull().sum())
        unique_count = int(series.nunique())
        row_count = len(df)
        null_pct = (null_count / row_count * 100) if row_count > 0 else 0.0
        unique_pct = (unique_count / row_count * 100) if row_count > 0 else 0.0

        # Cardinality classification
        if unique_pct < 1:
            cardinality = "low"
        elif unique_pct < 20:
            cardinality = "medium"
        else:
            cardinality = "high"

        # Primary key detection: unique, non-null, integer-like
        is_pk = (
            null_count == 0
            and unique_count == row_count
            and row_count > 1
            and (
                np.issubdtype(series.dtype, np.integer)
                or col_name.lower().endswith("_id")
                or col_name.lower() == "id"
            )
        )

        # Numeric stats
        min_val = max_val = mean_val = std_val = None
        if np.issubdtype(series.dtype, np.number):
            min_val = float(series.min())
            max_val = float(series.max())
            mean_val = float(series.mean())
            std_val = float(series.std()) if row_count > 1 else 0.0

        # Sample values
        non_null = series.dropna()
        sample_values = non_null.head(10).tolist() if len(non_null) > 0 else []

        # Value distribution for categorical/low-cardinality
        value_dist = {}
        if cardinality in ("low", "medium") and not np.issubdtype(series.dtype, np.number):
            vc = series.value_counts().head(20)
            value_dist = {k: int(v) for k, v in vc.items()}

        # Constraints
        constraints = []
        if null_count == 0:
            constraints.append("NOT NULL")
        if is_pk:
            constraints.append("PRIMARY KEY")
        if unique_count == row_count and not is_pk:
            constraints.append("UNIQUE")

        return ColumnMetadata(
            name=col_name,
            dtype=dtype,
            nullable=null_count > 0,
            unique_count=unique_count,
            null_count=null_count,
            null_pct=null_pct,
            unique_pct=unique_pct,
            cardinality=cardinality,
            min_value=min_val,
            max_value=max_val,
            mean_value=mean_val,
            std_value=std_val,
            sample_values=sample_values,
            value_distribution=value_dist,
            is_primary_key=is_pk,
            constraints=constraints,
        )

    @staticmethod
    def _detect_foreign_keys(df: pd.DataFrame, columns: list[ColumnMetadata]) -> list[dict]:
        """Heuristically detect foreign key columns."""
        fks = []
        for col in columns:
            name_lower = col.name.lower()
            if name_lower.endswith("_id") and not col.is_primary_key:
                ref_table = name_lower[:-3]  # Remove _id suffix
                fks.append(
                    {
                        "column": col.name,
                        "references_table": ref_table,
                        "references_column": "id",
                        "confidence": "heuristic",
                    }
                )
            elif name_lower.endswith("_code") and col.cardinality != "high":
                fks.append(
                    {
                        "column": col.name,
                        "references_table": name_lower[:-5],
                        "references_column": "code",
                        "confidence": "heuristic",
                    }
                )
        return fks
