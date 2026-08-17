"""Automatic Filter Engine.

Intelligently selects useful filters for dashboard interaction.

Rules:
  - Date range filter for time columns
  - Single-select for low-cardinality dimensions (<=20)
  - Multi-select for medium-cardinality dimensions (21-100)
  - No filters for identifier columns
  - No filters for high-cardinality text columns (>100)
  - Maximum 6 filters
"""

from __future__ import annotations

import logging

import pandas as pd

from services.auto.analysis_engine import DatasetUnderstanding, SemanticRole
from services.auto.chart_specification import FilterSpecification

logger = logging.getLogger(__name__)


class AutomaticFilterEngine:
    """Automatically detects useful filters for dashboard interaction."""

    MAX_FILTERS = 6
    SINGLE_SELECT_MAX = 20
    MULTI_SELECT_MAX = 100

    def select_filters(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[FilterSpecification]:
        """Detect and generate useful filters.

        Args:
            df: The dataset DataFrame.
            understanding: DatasetUnderstanding from AutomaticAnalysisEngine.

        Returns:
            List of FilterSpecification objects.
        """
        filters: list[FilterSpecification] = []
        order = 0

        # 1. Date range filter
        if understanding.time_columns:
            time_col = understanding.time_columns[0]
            if time_col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                    dates = df[time_col].dropna()
                else:
                    dates = pd.to_datetime(df[time_col], errors="coerce").dropna()

                if len(dates) > 0:
                    filters.append(
                        FilterSpecification(
                            filter_type="date_range",
                            label=f"Date Range ({self._label(time_col)})",
                            column=time_col,
                            default_value={
                                "start": dates.min().strftime("%Y-%m-%d"),
                                "end": dates.max().strftime("%Y-%m-%d"),
                            },
                            order=order,
                        )
                    )
                    order += 1

        # 2. Dimension filters
        for col_u in understanding.columns:
            if len(filters) >= self.MAX_FILTERS:
                break

            if col_u.semantic_role not in (
                SemanticRole.CATEGORY,
                SemanticRole.GEOGRAPHY,
                SemanticRole.BOOLEAN,
            ):
                continue
            if col_u.name not in df.columns:
                continue
            if col_u.missing_percentage > 80:
                continue

            cardinality = col_u.cardinality

            if cardinality < 2:
                continue

            if cardinality <= self.SINGLE_SELECT_MAX:
                filter_type = "single_select"
                options = [
                    str(v) for v in df[col_u.name].dropna().unique()[: self.SINGLE_SELECT_MAX]
                ]
            elif cardinality <= self.MULTI_SELECT_MAX:
                filter_type = "multi_select"
                options = [
                    str(v) for v in df[col_u.name].dropna().unique()[: self.MULTI_SELECT_MAX]
                ]
            else:
                # Too many values — skip
                continue

            filters.append(
                FilterSpecification(
                    filter_type=filter_type,
                    label=self._label(col_u.name),
                    column=col_u.name,
                    entity=col_u.semantic_role,
                    options=options,
                    order=order,
                )
            )
            order += 1

        return filters[: self.MAX_FILTERS]

    @staticmethod
    def _label(col: str) -> str:
        return col.replace("_", " ").title()
