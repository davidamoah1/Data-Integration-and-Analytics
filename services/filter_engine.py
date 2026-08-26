"""Global Filter Engine.

Implements reusable, cross-chart filters that update all relevant
visualizations when changed.

Filter types:
  - Date range
  - Region / Department
  - Product / Customer
  - Employee / Organization
  - Custom filters

Changes propagate to all charts that reference the filtered column.
"""

from __future__ import annotations

import logging
import uuid

import pandas as pd

from services.dashboard_engine import FilterDefinition, FilterType

logger = logging.getLogger(__name__)


class GlobalFilterEngine:
    """Manages global dashboard filters."""

    def detect_filters(
        self,
        df: pd.DataFrame,
        semantic_mappings: dict | None = None,
        max_filters: int = 8,
    ) -> list[FilterDefinition]:
        """Detect applicable filters from data and semantic mappings.

        Args:
            df: The dataset DataFrame.
            semantic_mappings: Column-to-entity mapping.
            max_filters: Maximum number of filters to generate.

        Returns:
            List of FilterDefinition objects.
        """
        col_mapping = semantic_mappings or {}
        filters: list[FilterDefinition] = []
        seen_columns: set[str] = set()

        # 1. Date range filter (from datetime columns or date-like columns)
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        if not date_cols:
            # Check for date-like string columns
            for col in df.columns:
                if df[col].dtype == "object" and any(
                    kw in col.lower() for kw in ("date", "time", "timestamp")
                ):
                    try:
                        pd.to_datetime(df[col].dropna().head(10), errors="raise")
                        date_cols.append(col)
                    except Exception:
                        pass

        if date_cols:
            col = date_cols[0]
            filters.append(
                FilterDefinition(
                    id=str(uuid.uuid4()),
                    filter_type=FilterType.DATE_RANGE.value,
                    label="Date Range",
                    column=col,
                    entity=col_mapping.get(col),
                    default_value=None,
                )
            )
            seen_columns.add(col)

        # 2. Semantic entity filters
        filter_entities = [
            ("region", "Region"),
            ("country", "Country"),
            ("city", "City"),
            ("state", "State"),
            ("district", "District"),
            ("department", "Department"),
            ("department_edu", "Department"),
            ("ward", "Ward"),
            ("branch_church", "Branch"),
            ("category", "Category"),
            ("product", "Product"),
            ("course", "Course"),
            ("diagnosis", "Diagnosis"),
            ("program", "Program"),
            ("project_gov", "Project"),
            ("plan", "Plan"),
            ("ministry", "Ministry"),
        ]

        for entity, label in filter_entities:
            if len(filters) >= max_filters:
                break
            col = self._find_column_for_entity(col_mapping, entity)
            if col and col not in seen_columns and col in df.columns:
                cardinality = df[col].nunique()
                if cardinality <= 50:  # Reasonable for a filter
                    filter_type = (
                        FilterType.SINGLE_SELECT.value
                        if cardinality <= 10
                        else FilterType.MULTI_SELECT.value
                    )
                    options = df[col].dropna().unique().tolist()[:50]
                    filters.append(
                        FilterDefinition(
                            id=str(uuid.uuid4()),
                            filter_type=filter_type,
                            label=label,
                            column=col,
                            entity=entity,
                            options=options,
                        )
                    )
                    seen_columns.add(col)

        # 3. Additional categorical filters (not semantically mapped)
        for col in df.columns:
            if len(filters) >= max_filters:
                break
            if col in seen_columns:
                continue
            if df[col].dtype == "object" and not col.lower().endswith("_id"):
                cardinality = df[col].nunique()
                if 2 <= cardinality <= 20:
                    filters.append(
                        FilterDefinition(
                            id=str(uuid.uuid4()),
                            filter_type=FilterType.SINGLE_SELECT.value,
                            label=col.replace("_", " ").title(),
                            column=col,
                            entity=col_mapping.get(col),
                            options=df[col].dropna().unique().tolist()[:20],
                        )
                    )
                    seen_columns.add(col)

        return filters

    def apply_filters(
        self,
        df: pd.DataFrame,
        filter_values: dict[str, Any],
        filters: list[FilterDefinition],
    ) -> pd.DataFrame:
        """Apply filter values to a DataFrame.

        Args:
            df: The DataFrame to filter.
            filter_values: Dict of filter_id â†’ selected value(s).
            filters: List of filter definitions.

        Returns:
            Filtered DataFrame.
        """
        if not filter_values:
            return df

        filtered = df.copy()
        filter_map = {f.id: f for f in filters}

        for filter_id, value in filter_values.items():
            if not value:
                continue

            filter_def = filter_map.get(filter_id)
            if not filter_def:
                continue

            col = filter_def.column
            if col not in filtered.columns:
                continue

            if filter_def.filter_type == FilterType.DATE_RANGE.value:
                filtered = self._apply_date_filter(filtered, col, value)
            elif filter_def.filter_type == FilterType.SINGLE_SELECT.value:
                filtered = filtered[filtered[col] == value]
            elif filter_def.filter_type == FilterType.MULTI_SELECT.value:
                if isinstance(value, list) and value:
                    filtered = filtered[filtered[col].isin(value)]
            elif filter_def.filter_type == FilterType.NUMERIC_RANGE.value:
                if isinstance(value, dict):
                    min_val = value.get("min")
                    max_val = value.get("max")
                    if min_val is not None:
                        filtered = filtered[filtered[col] >= min_val]
                    if max_val is not None:
                        filtered = filtered[filtered[col] <= max_val]
            elif filter_def.filter_type == FilterType.SEARCH.value:
                if isinstance(value, str) and value:
                    filtered = filtered[
                        filtered[col].astype(str).str.contains(value, case=False, na=False)
                    ]

        return filtered

    def get_affected_charts(
        self,
        filter_id: str,
        filters: list[FilterDefinition],
        charts: list,
    ) -> list[str]:
        """Get chart IDs affected by a filter change.

        Args:
            filter_id: The changed filter's ID.
            filters: All filter definitions.
            charts: List of chart definitions.

        Returns:
            List of affected chart IDs.
        """
        filter_def = next((f for f in filters if f.id == filter_id), None)
        if not filter_def:
            return []

        affected = []
        for chart in charts:
            if (
                filter_def.column in chart.source_columns
                or chart.x_axis == filter_def.column
                or chart.y_axis == filter_def.column
                or chart.group_by == filter_def.column
            ):
                affected.append(chart.id)

        return affected

    def get_cascading_options(
        self,
        df: pd.DataFrame,
        filter_id: str,
        filters: list[FilterDefinition],
        current_values: dict[str, Any],
    ) -> dict[str, list]:
        """Get cascading filter options based on current selections.

        Args:
            df: The full DataFrame.
            filter_id: The filter that changed.
            filters: All filter definitions.
            current_values: Current filter values.

        Returns:
            Dict of filter_id â†’ updated options for dependent filters.
        """
        filter_def = next((f for f in filters if f.id == filter_id), None)
        if not filter_def:
            return {}

        # Apply current filters to get filtered data
        filtered_df = self.apply_filters(df, current_values, filters)

        # Update options for other filters
        result = {}
        for f in filters:
            if f.id == filter_id or not f.depends_on:
                continue
            if f.depends_on == filter_id and f.column in filtered_df.columns:
                result[f.id] = filtered_df[f.column].dropna().unique().tolist()[:50]

        return result

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _find_column_for_entity(col_mapping: dict, entity: str) -> str | None:
        for col, ent in col_mapping.items():
            if ent == entity:
                return col
        return None

    @staticmethod
    def _apply_date_filter(df: pd.DataFrame, col: str, value: Any) -> pd.DataFrame:
        """Apply date range filter."""
        if isinstance(value, dict):
            start = value.get("start")
            end = value.get("end")
            if start and end:
                dates = pd.to_datetime(df[col], errors="coerce")
                return df[(dates >= pd.to_datetime(start)) & (dates <= pd.to_datetime(end))]
            elif start:
                dates = pd.to_datetime(df[col], errors="coerce")
                return df[dates >= pd.to_datetime(start)]
            elif end:
                dates = pd.to_datetime(df[col], errors="coerce")
                return df[dates <= pd.to_datetime(end)]
        return df


# Type annotation fix for forward reference
from typing import Any  # noqa: E402
