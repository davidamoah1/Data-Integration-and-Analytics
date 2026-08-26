"""Drilldown Engine.

Enables hierarchical navigation:
  KPI â†’ Chart â†’ Detail Table â†’ Record View

Supports breadcrumb navigation and drill-through.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from services.dashboard_engine import DrilldownLevel

logger = logging.getLogger(__name__)


@dataclass
class DrilldownPath:
    """Represents a drilldown navigation path."""

    levels: list[DrilldownLevel] = field(default_factory=list)
    current_level: int = 0
    breadcrumbs: list[dict] = field(default_factory=list)
    filter_context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "levels": [l.to_dict() for l in self.levels],
            "current_level": self.current_level,
            "breadcrumbs": self.breadcrumbs,
            "filter_context": self.filter_context,
        }


class DrilldownEngine:
    """Manages drilldown navigation for dashboards."""

    def generate_drilldowns(
        self,
        df: pd.DataFrame,
        kpis: list,
        charts: list,
        semantic_mappings: dict | None = None,
    ) -> list[DrilldownLevel]:
        """Generate drilldown levels from dashboard data.

        Args:
            df: The dataset DataFrame.
            kpis: List of KPI definitions.
            charts: List of chart definitions.
            semantic_mappings: Column-to-entity mapping.

        Returns:
            List of DrilldownLevel objects.
        """
        levels: list[DrilldownLevel] = []

        # Level 0: KPI summary
        levels.append(
            DrilldownLevel(
                level=0,
                label="Summary",
                chart_id=None,
                table_columns=[],
            )
        )

        # Level 1: Primary chart (e.g., revenue over time)
        primary_charts = [c for c in charts if c.section == "primary_charts"]
        if primary_charts:
            chart = primary_charts[0]
            levels.append(
                DrilldownLevel(
                    level=1,
                    label=chart.title,
                    chart_id=chart.id,
                    table_columns=chart.source_columns,
                    parent_column=None,
                )
            )

            # Level 2: Grouped detail (e.g., revenue by category)
            if chart.group_by or chart.x_axis:
                group_col = chart.group_by or chart.x_axis
                levels.append(
                    DrilldownLevel(
                        level=2,
                        label=f"Detail by {group_col.replace('_', ' ').title()}",
                        chart_id=None,
                        table_columns=[group_col, chart.y_axis] if chart.y_axis else [group_col],
                        parent_column=chart.x_axis,
                        target_column=group_col,
                    )
                )

        # Level 3: Record-level detail
        detail_cols = [
            c for c in df.columns if not c.lower().endswith("_id") or c.lower().endswith("_id")
        ][:10]
        levels.append(
            DrilldownLevel(
                level=3,
                label="Record Details",
                chart_id=None,
                table_columns=detail_cols,
            )
        )

        return levels

    def drill_down(
        self,
        path: DrilldownPath,
        target_level: int,
        filter_value: dict | None = None,
    ) -> DrilldownPath:
        """Drill down to a specific level.

        Args:
            path: Current drilldown path.
            target_level: Target level to drill to.
            filter_value: Filter context for the drilldown.

        Returns:
            Updated DrilldownPath.
        """
        if target_level < 0 or target_level >= len(path.levels):
            return path

        path.current_level = target_level
        if filter_value:
            path.filter_context.update(filter_value)

        # Update breadcrumbs
        path.breadcrumbs = []
        for i in range(target_level + 1):
            if i < len(path.levels):
                level = path.levels[i]
                path.breadcrumbs.append(
                    {
                        "level": i,
                        "label": level.label,
                    }
                )

        return path

    def drill_up(self, path: DrilldownPath, to_level: int | None = None) -> DrilldownPath:
        """Drill up (go back) to a higher level.

        Args:
            path: Current drilldown path.
            to_level: Target level (default: one level up).

        Returns:
            Updated DrilldownPath.
        """
        if to_level is None:
            to_level = max(0, path.current_level - 1)

        if to_level < 0:
            to_level = 0

        path.current_level = to_level
        path.breadcrumbs = path.breadcrumbs[: to_level + 1]

        # Remove filter context for levels below
        levels_to_remove = [
            k
            for k, v in path.filter_context.items()
            if isinstance(v, dict) and v.get("level", 0) > to_level
        ]
        for key in levels_to_remove:
            path.filter_context.pop(key, None)

        return path

    def get_detail_data(
        self,
        df: pd.DataFrame,
        path: DrilldownPath,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get detail table data for the current drilldown level.

        Args:
            df: The full DataFrame.
            path: Current drilldown path.
            filters: Additional filters to apply.
            page: Page number for pagination.
            page_size: Number of rows per page.

        Returns:
            Dict with data, pagination info, and breadcrumbs.
        """
        if path.current_level >= len(path.levels):
            return {"data": [], "total": 0, "page": 1, "pages": 1}

        level = path.levels[path.current_level]
        filtered = df.copy()

        # Apply drilldown filter context
        for _key, value in path.filter_context.items():
            if isinstance(value, dict):
                col = value.get("column")
                val = value.get("value")
                if col and col in filtered.columns and val is not None:
                    filtered = filtered[filtered[col] == val]

        # Apply additional filters
        if filters:
            for col, val in filters.items():
                if col in filtered.columns:
                    if isinstance(val, list):
                        filtered = filtered[filtered[col].isin(val)]
                    else:
                        filtered = filtered[filtered[col] == val]

        # Select columns for this level
        if level.table_columns:
            available_cols = [c for c in level.table_columns if c in filtered.columns]
            if available_cols:
                filtered = filtered[available_cols]

        # Paginate
        total = len(filtered)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = filtered.iloc[start:end]

        return {
            "data": page_data.to_dict("records"),
            "total": total,
            "page": page,
            "pages": total_pages,
            "page_size": page_size,
            "columns": level.table_columns,
            "breadcrumbs": path.breadcrumbs,
            "current_level": path.current_level,
            "current_label": level.label,
        }

    def create_path(self, levels: list[DrilldownLevel]) -> DrilldownPath:
        """Create a new drilldown path from levels."""
        path = DrilldownPath(levels=levels)
        if levels:
            path.breadcrumbs = [{"level": 0, "label": levels[0].label}]
        return path
