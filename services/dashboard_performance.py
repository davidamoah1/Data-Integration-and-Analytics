"""Dashboard Performance Layer.

Provides caching, lazy loading, and pagination for dashboard operations.

Features:
  - KPI calculation caching with TTL
  - Aggregation result caching
  - Server-side pagination for detail tables
  - Incremental rendering support
  - Efficient filter application
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached computation result."""

    value: Any
    timestamp: float
    ttl_seconds: float = 300.0  # 5 minute default TTL

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl_seconds


class DashboardPerformanceLayer:
    """Performance optimizations for dashboard operations."""

    def __init__(self, default_ttl: float = 300.0):
        self._kpi_cache: dict[str, CacheEntry] = {}
        self._agg_cache: dict[str, CacheEntry] = {}
        self._filter_cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

    def compute_kpi(
        self,
        kpi_key: str,
        df: pd.DataFrame,
        source_columns: list[str],
        aggregation: str,
        dataset_hash: str,
    ) -> float | int | None:
        """Compute a KPI value with caching.

        Args:
            kpi_key: Unique KPI identifier.
            df: DataFrame to compute from.
            source_columns: Columns to aggregate.
            aggregation: Aggregation type (sum, count, avg, etc.).
            dataset_hash: Hash of the dataset for cache keying.

        Returns:
            Computed KPI value.
        """
        cache_key = f"{dataset_hash}:{kpi_key}:{aggregation}"

        # Check cache
        if cache_key in self._kpi_cache:
            entry = self._kpi_cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"KPI cache hit: {kpi_key}")
                return entry.value

        # Compute
        value = self._compute_aggregation(df, source_columns, aggregation)

        # Cache
        self._kpi_cache[cache_key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl_seconds=self._default_ttl,
        )

        return value

    def compute_aggregation(
        self,
        df: pd.DataFrame,
        group_by: str,
        value_col: str,
        aggregation: str,
        dataset_hash: str,
        filter_hash: str = "",
    ) -> pd.DataFrame:
        """Compute a grouped aggregation with caching.

        Args:
            df: DataFrame to aggregate.
            group_by: Column to group by.
            value_col: Column to aggregate.
            aggregation: Aggregation type.
            dataset_hash: Hash of the dataset.
            filter_hash: Hash of applied filters.

        Returns:
            Aggregated DataFrame.
        """
        cache_key = f"{dataset_hash}:{filter_hash}:{group_by}:{value_col}:{aggregation}"

        if cache_key in self._agg_cache:
            entry = self._agg_cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Aggregation cache hit: {cache_key}")
                return entry.value.copy()

        # Compute
        if group_by not in df.columns or value_col not in df.columns:
            return pd.DataFrame()

        if aggregation == "sum" and pd.api.types.is_numeric_dtype(df[value_col]):
            result = df.groupby(group_by)[value_col].sum().reset_index()
        elif aggregation == "count":
            result = df.groupby(group_by).size().reset_index(name="count")
        elif aggregation == "avg" and pd.api.types.is_numeric_dtype(df[value_col]):
            result = df.groupby(group_by)[value_col].mean().reset_index()
        elif aggregation == "min":
            result = df.groupby(group_by)[value_col].min().reset_index()
        elif aggregation == "max":
            result = df.groupby(group_by)[value_col].max().reset_index()
        elif aggregation == "median":
            result = df.groupby(group_by)[value_col].median().reset_index()
        else:
            result = df.groupby(group_by).size().reset_index(name="count")

        # Cache
        self._agg_cache[cache_key] = CacheEntry(
            value=result.copy(),
            timestamp=time.time(),
            ttl_seconds=self._default_ttl,
        )

        return result

    def paginate(
        self,
        df: pd.DataFrame,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Paginate a DataFrame for server-side pagination.

        Args:
            df: DataFrame to paginate.
            page: Page number (1-indexed).
            page_size: Rows per page.

        Returns:
            Dict with data, pagination info.
        """
        total = len(df)
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start = (page - 1) * page_size
        end = start + page_size

        return {
            "data": df.iloc[start:end].to_dict("records"),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    def lazy_load_kpis(
        self,
        kpi_keys: list[str],
        df: pd.DataFrame,
        kpi_definitions: list[dict],
        dataset_hash: str,
    ) -> dict[str, Any]:
        """Lazy-load KPI values â€” only compute requested KPIs.

        Args:
            kpi_keys: KPI keys to compute (if None, compute all).
            df: Source DataFrame.
            kpi_definitions: List of KPI definition dicts.
            dataset_hash: Hash of the dataset.

        Returns:
            Dict of kpi_key â†’ value.
        """
        results: dict[str, Any] = {}
        def_map = {d["key"]: d for d in kpi_definitions}

        for key in kpi_keys:
            defn = def_map.get(key)
            if not defn:
                continue

            value = self.compute_kpi(
                kpi_key=key,
                df=df,
                source_columns=defn.get("source_columns", []),
                aggregation=defn.get("aggregation", "sum"),
                dataset_hash=dataset_hash,
            )
            if value is not None:
                results[key] = value

        return results

    def clear_cache(self, dataset_hash: str | None = None) -> int:
        """Clear cache entries.

        Args:
            dataset_hash: If provided, only clear entries for this dataset.
                         If None, clear all.

        Returns:
            Number of entries cleared.
        """
        if dataset_hash is None:
            count = len(self._kpi_cache) + len(self._agg_cache) + len(self._filter_cache)
            self._kpi_cache.clear()
            self._agg_cache.clear()
            self._filter_cache.clear()
            return count

        prefix = f"{dataset_hash}:"
        cleared = 0
        for cache in (self._kpi_cache, self._agg_cache, self._filter_cache):
            keys_to_remove = [k for k in cache if k.startswith(prefix)]
            for k in keys_to_remove:
                cache.pop(k, None)
                cleared += 1
        return cleared

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "kpi_cache_size": len(self._kpi_cache),
            "aggregation_cache_size": len(self._agg_cache),
            "filter_cache_size": len(self._filter_cache),
            "default_ttl_seconds": self._default_ttl,
        }

    @staticmethod
    def compute_dataset_hash(df: pd.DataFrame) -> str:
        """Compute a hash for a DataFrame for cache keying."""
        content = json.dumps(
            {
                "shape": list(df.shape),
                "columns": list(df.columns),
                "head_hash": hashlib.sha256(df.head(5).to_csv(index=False).encode()).hexdigest()[
                    :16
                ],
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def compute_filter_hash(filters: dict) -> str:
        """Compute a hash for filter values."""
        if not filters:
            return ""
        return hashlib.sha256(
            json.dumps(filters, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    # â”€â”€ Private â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _compute_aggregation(
        df: pd.DataFrame,
        columns: list[str],
        aggregation: str,
    ) -> float | int | None:
        """Compute a simple aggregation."""
        if not columns:
            if aggregation == "count":
                return len(df)
            return None

        col = columns[0]
        if col not in df.columns:
            return None

        if aggregation == "count":
            return int(df[col].nunique()) if col else len(df)
        elif aggregation == "sum":
            if pd.api.types.is_numeric_dtype(df[col]):
                return float(df[col].sum())
            return int(df[col].nunique())
        elif aggregation == "avg":
            if pd.api.types.is_numeric_dtype(df[col]):
                return float(df[col].mean())
            return None
        elif aggregation == "min":
            if pd.api.types.is_numeric_dtype(df[col]):
                return float(df[col].min())
            return None
        elif aggregation == "max":
            if pd.api.types.is_numeric_dtype(df[col]):
                return float(df[col].max())
            return None
        elif aggregation == "median":
            if pd.api.types.is_numeric_dtype(df[col]):
                return float(df[col].median())
            return None
        return None
