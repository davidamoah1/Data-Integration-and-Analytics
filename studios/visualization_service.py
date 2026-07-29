"""Visualization Engine — intelligent chart selection and recommendation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import ChartRecommendation


class VisualizationEngine:
    """Intelligent chart recommendation engine.

    Decides which chart best explains the data — quality over quantity.
    """

    def __init__(self, db: DbSession):
        self.db = db

    # ─── Chart Type Selection Logic ──────────────────────────

    @staticmethod
    def recommend_chart(
        df: pd.DataFrame,
        columns: list[str] | None = None,
        intent: str | None = None,
    ) -> dict:
        """Recommend the best chart type for the given data and intent.

        Args:
            df: Input dataframe.
            columns: Columns to visualize. If None, auto-selects.
            intent: What the user wants to see (trend, comparison, distribution, relationship, composition, geographic).
        """
        if columns is None:
            # Auto-select interesting columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
            columns = numeric_cols[:3] + categorical_cols[:2]

        col_types = {}
        for col in columns:
            if col not in df.columns:
                continue
            if df[col].dtype in ("int64", "float64"):
                col_types[col] = "numeric"
            elif pd.to_datetime(df[col], errors="coerce").notna().sum() > len(df) * 0.8:
                col_types[col] = "datetime"
            else:
                col_types[col] = "categorical"

        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        categorical_cols = [c for c, t in col_types.items() if t == "categorical"]
        datetime_cols = [c for c, t in col_types.items() if t == "datetime"]

        # Intent-based recommendation
        if intent:
            intent = intent.lower()
            if intent in ("trend", "time", "over time"):
                return VisualizationEngine._recommend_trend(df, datetime_cols, numeric_cols)
            elif intent in ("compare", "comparison", "vs", "versus"):
                return VisualizationEngine._recommend_comparison(df, categorical_cols, numeric_cols)
            elif intent in ("distribution", "spread", "histogram"):
                return VisualizationEngine._recommend_distribution(df, numeric_cols)
            elif intent in ("relationship", "correlation", "scatter"):
                return VisualizationEngine._recommend_relationship(df, numeric_cols)
            elif intent in ("composition", "breakdown", "parts", "proportion"):
                return VisualizationEngine._recommend_composition(df, categorical_cols, numeric_cols)
            elif intent in ("geographic", "map", "location"):
                return VisualizationEngine._recommend_geographic(df, columns)

        # Auto-detect best chart based on data characteristics
        return VisualizationEngine._auto_recommend(df, numeric_cols, categorical_cols, datetime_cols)

    @staticmethod
    def _auto_recommend(df, numeric_cols, categorical_cols, datetime_cols) -> dict:
        """Automatically select the best chart type."""
        # Time series + numeric → line chart
        if datetime_cols and numeric_cols:
            return VisualizationEngine._recommend_trend(df, datetime_cols, numeric_cols)

        # Categorical + numeric → bar chart
        if categorical_cols and numeric_cols:
            return VisualizationEngine._recommend_comparison(df, categorical_cols, numeric_cols)

        # Two numeric → scatter
        if len(numeric_cols) >= 2:
            return VisualizationEngine._recommend_relationship(df, numeric_cols)

        # Single numeric → distribution
        if len(numeric_cols) == 1:
            return VisualizationEngine._recommend_distribution(df, numeric_cols)

        # Categorical only → pie/bar
        if categorical_cols:
            return VisualizationEngine._recommend_composition(df, categorical_cols, [])

        return {
            "chart_type": "table",
            "chart_category": "business",
            "title": "Data Table View",
            "reasoning": "No suitable chart could be determined. Showing data as a table.",
            "config": {"columns": df.columns.tolist()[:10]},
        }

    @staticmethod
    def _recommend_trend(df, datetime_cols, numeric_cols) -> dict:
        time_col = datetime_cols[0]
        value_col = numeric_cols[0]
        return {
            "chart_type": "line",
            "chart_category": "business",
            "title": f"Trend of {value_col} over {time_col}",
            "reasoning": f"Line chart is ideal for showing how {value_col} changes over time. "
                        f"Time column '{time_col}' on X-axis, '{value_col}' on Y-axis.",
            "config": {
                "x": time_col,
                "y": value_col,
                "additional_y": numeric_cols[1:3],
                "smooth": True,
                "markers": True,
            },
            "data_summary": {
                "time_range": f"{df[time_col].min()} to {df[time_col].max()}",
                "value_range": [float(df[value_col].min()), float(df[value_col].max())],
                "trend_direction": "increasing" if df[value_col].iloc[-1] > df[value_col].iloc[0] else "decreasing",
            },
        }

    @staticmethod
    def _recommend_comparison(df, categorical_cols, numeric_cols) -> dict:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        n_categories = df[cat_col].nunique()

        if n_categories <= 6:
            chart_type = "bar"
            reasoning = f"Bar chart clearly compares {num_col} across {n_categories} categories of {cat_col}."
        else:
            chart_type = "horizontal_bar"
            reasoning = f"Horizontal bar chart handles {n_categories} categories of {cat_col} better than vertical bars."

        return {
            "chart_type": chart_type,
            "chart_category": "business",
            "title": f"{num_col} by {cat_col}",
            "reasoning": reasoning,
            "config": {
                "x": cat_col,
                "y": num_col,
                "sort_by": "value",
                "sort_order": "descending",
            },
            "data_summary": {
                "n_categories": int(n_categories),
                "top_category": str(df.groupby(cat_col)[num_col].sum().idxmax()),
                "value_range": [float(df[num_col].min()), float(df[num_col].max())],
            },
        }

    @staticmethod
    def _recommend_distribution(df, numeric_cols) -> dict:
        col = numeric_cols[0]
        n = len(df[col].dropna())

        if n > 1000:
            chart_type = "histogram"
            reasoning = f"Histogram shows the distribution shape of {col} for {n} data points."
        else:
            chart_type = "box"
            reasoning = f"Box plot shows distribution, median, quartiles, and outliers for {col}."

        return {
            "chart_type": chart_type,
            "chart_category": "statistical",
            "title": f"Distribution of {col}",
            "reasoning": reasoning,
            "config": {
                "column": col,
                "bins": 30 if chart_type == "histogram" else None,
                "show_outliers": True,
            },
            "data_summary": {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "skewness": float(df[col].skew()),
                "n": int(n),
            },
        }

    @staticmethod
    def _recommend_relationship(df, numeric_cols) -> dict:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        correlation = df[[x_col, y_col]].corr().iloc[0, 1]

        if abs(correlation) > 0.7:
            insight = f"Strong {'positive' if correlation > 0 else 'negative'} correlation (r={correlation:.3f})"
        elif abs(correlation) > 0.4:
            insight = f"Moderate {'positive' if correlation > 0 else 'negative'} correlation (r={correlation:.3f})"
        else:
            insight = f"Weak or no linear correlation (r={correlation:.3f})"

        return {
            "chart_type": "scatter",
            "chart_category": "statistical",
            "title": f"Relationship: {x_col} vs {y_col}",
            "reasoning": f"Scatter plot reveals the relationship between {x_col} and {y_col}. {insight}.",
            "config": {
                "x": x_col,
                "y": y_col,
                "trendline": True,
                "color_by": numeric_cols[2] if len(numeric_cols) > 2 else None,
            },
            "data_summary": {
                "correlation": float(correlation),
                "insight": insight,
                "n_points": int(len(df[[x_col, y_col]].dropna())),
            },
        }

    @staticmethod
    def _recommend_composition(df, categorical_cols, numeric_cols) -> dict:
        cat_col = categorical_cols[0]
        n_categories = df[cat_col].nunique()

        if n_categories <= 6:
            chart_type = "pie"
            reasoning = f"Pie chart shows the proportion of each {cat_col} category."
        else:
            chart_type = "treemap"
            reasoning = f"Treemap handles {n_categories} categories better than a pie chart."

        counts = df[cat_col].value_counts()
        return {
            "chart_type": chart_type,
            "chart_category": "business",
            "title": f"Composition of {cat_col}",
            "reasoning": reasoning,
            "config": {
                "column": cat_col,
                "top_n": 10,
            },
            "data_summary": {
                "n_categories": int(n_categories),
                "top_3": {str(k): int(v) for k, v in counts.head(3).items()},
                "total": int(counts.sum()),
            },
        }

    @staticmethod
    def _recommend_geographic(df, columns) -> dict:
        # Look for location-like columns
        location_cols = [c for c in columns if any(k in c.lower() for k in ["country", "city", "region", "state", "location", "lat", "lon"])]
        value_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in location_cols]

        return {
            "chart_type": "choropleth",
            "chart_category": "geographic",
            "title": "Geographic Distribution",
            "reasoning": "Geographic chart visualizes data distribution across regions.",
            "config": {
                "location_column": location_cols[0] if location_cols else columns[0],
                "value_column": value_cols[0] if value_cols else None,
            },
            "data_summary": {
                "n_regions": int(df[location_cols[0]].nunique()) if location_cols else 0,
            },
        }

    @staticmethod
    def recommend_multiple(df: pd.DataFrame, max_charts: int = 5) -> list[dict]:
        """Recommend multiple complementary charts for a dataset."""
        recommendations = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        datetime_cols = [c for c in df.columns if pd.to_datetime(df[c], errors="coerce").notna().sum() > len(df) * 0.8]

        # 1. Trend (if time data)
        if datetime_cols and numeric_cols:
            recommendations.append(VisualizationEngine._recommend_trend(df, datetime_cols, numeric_cols))

        # 2. Comparison
        if categorical_cols and numeric_cols:
            recommendations.append(VisualizationEngine._recommend_comparison(df, categorical_cols, numeric_cols))

        # 3. Distribution
        if numeric_cols:
            recommendations.append(VisualizationEngine._recommend_distribution(df, [numeric_cols[0]]))

        # 4. Relationship
        if len(numeric_cols) >= 2:
            recommendations.append(VisualizationEngine._recommend_relationship(df, numeric_cols[:2]))

        # 5. Composition
        if categorical_cols:
            recommendations.append(VisualizationEngine._recommend_composition(df, categorical_cols, numeric_cols))

        return recommendations[:max_charts]

    # ─── Persistence ─────────────────────────────────────────

    def save_recommendation(
        self,
        org_id: int,
        user_id: int,
        chart_type: str,
        chart_category: str,
        title: str,
        config: dict,
        reasoning: str,
        dataset_id: int | None = None,
        data_summary: dict | None = None,
    ) -> ChartRecommendation:
        rec = ChartRecommendation(
            organization_id=org_id,
            dataset_id=dataset_id,
            chart_type=chart_type,
            chart_category=chart_category,
            title=title,
            config=config,
            reasoning=reasoning,
            data_summary=data_summary,
            created_by=user_id,
        )
        self.db.add(rec)
        self.db.commit()
        return rec

    def list_recommendations(self, org_id: int, dataset_id: int | None = None) -> list[ChartRecommendation]:
        query = select(ChartRecommendation).where(ChartRecommendation.organization_id == org_id)
        if dataset_id:
            query = query.where(ChartRecommendation.dataset_id == dataset_id)
        return self.db.execute(query.order_by(ChartRecommendation.created_at.desc())).scalars().all()
