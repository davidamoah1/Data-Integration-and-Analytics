"""Decision intelligence and recommendation generation.

Generates data-driven narrative recommendations by combining metric changes,
outliers, forecasts, and domain heuristics.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.anomaly import detect_spikes
from ml.readiness import assess_ml_readiness


def generate_recommendation(
    df: pd.DataFrame,
    metric_column: str,
    segment_column: str | None = None,
    forecast_values: list[float] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a narrative recommendation based on a dataset.

    Example output:
        "Sales decreased by 14% in the Northern Region. Inventory shortages
        coincided with the decline. Consider replenishing Product X before the
        next sales cycle."
    """
    context = context or {}
    recommendations = []
    facts = []

    if metric_column not in df.columns:
        return {
            "recommendation": "",
            "facts": [],
            "reasoning": "Metric column not found",
            "confidence": 0.0,
        }

    series = df[metric_column].dropna()
    if len(series) < 2:
        return {
            "recommendation": "",
            "facts": [],
            "reasoning": "Insufficient data",
            "confidence": 0.0,
        }

    recent = series.iloc[-1]
    previous = series.iloc[-2]
    pct_change = ((recent - previous) / previous * 100) if previous != 0 else 0.0
    direction = "increased" if pct_change > 0 else "decreased"

    facts.append(
        f"{metric_column.replace('_', ' ').title()} {direction} by {abs(pct_change):.1f}%."
    )

    if segment_column and segment_column in df.columns:
        grouped = df.groupby(segment_column)[metric_column].sum().sort_values(ascending=False)
        if not grouped.empty:
            top_segment = grouped.index[0]
            bottom_segment = grouped.index[-1]
            facts.append(f"Top contributor: {top_segment}; lowest contributor: {bottom_segment}.")

    # Correlation with other numeric columns
    numeric = df.select_dtypes(include=[np.number])
    if metric_column in numeric.columns and len(numeric.columns) > 1:
        corr = numeric.corr()[metric_column].drop(metric_column).dropna()
        strongest = corr.abs().idxmax() if not corr.empty else None
        if strongest and abs(corr[strongest]) > 0.5:
            direction_corr = "positively" if corr[strongest] > 0 else "negatively"
            facts.append(
                f"{strongest} is {direction_corr} correlated ({corr[strongest]:.2f}) with {metric_column}."
            )

    # Outliers
    spike = detect_spikes(df, metric_column, threshold=2.5)
    if spike.get("status") == "completed" and spike.get("anomaly_count", 0) > 0:
        facts.append(f"Detected {spike['anomaly_count']} anomalous values.")

    # Build recommendation
    if pct_change < -5:
        recommendations.append(
            f"Investigate the drivers behind the {abs(pct_change):.1f}% {metric_column} decline."
        )
        if segment_column:
            recommendations.append(
                "Review performance in the weakest segment and reallocate resources if needed."
            )
    elif pct_change > 5:
        recommendations.append(f"Capitalize on the {metric_column} growth momentum.")
        if segment_column:
            recommendations.append("Reinforce what's working in the top-performing segment.")
    else:
        recommendations.append(
            f"{metric_column.replace('_', ' ').title()} is stable; monitor for trend shifts."
        )

    if forecast_values and len(forecast_values) > 0:
        avg_forecast = float(np.mean(forecast_values))
        if avg_forecast > recent * 1.05:
            recommendations.append(
                "Forecast indicates continued growth; plan inventory and staffing accordingly."
            )
        elif avg_forecast < recent * 0.95:
            recommendations.append(
                "Forecast indicates a slowdown; consider cost controls or demand-generation initiatives."
            )

    readiness = assess_ml_readiness(df)
    if not readiness["ready"]:
        recommendations.append("Improve data quality before building predictive models.")

    confidence = min(0.95, 0.5 + min(abs(pct_change) / 100, 0.3) + (0.1 if forecast_values else 0))

    return {
        "recommendation": " ".join(recommendations),
        "facts": facts,
        "reasoning": "Based on recent change, segment breakdown, correlation analysis, and forecast outlook.",
        "confidence": round(confidence, 2),
        "metric_change_pct": round(pct_change, 2),
    }


def generate_what_if_scenarios(
    df: pd.DataFrame,
    metric_column: str,
    driver_column: str | None = None,
    scenarios: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate what-if scenario projections.

    Scenarios are dictionaries like {"name": "Increase marketing 10%", "impact_pct": 10}.
    If a driver_column is provided and it correlates with metric_column, the engine
    estimates a more informed outcome.
    """
    if scenarios is None:
        scenarios = [
            {"name": "Increase marketing spend 10%", "impact_pct": 10},
            {"name": "Reduce prices 5%", "impact_pct": -5},
            {"name": "Hire additional staff", "impact_pct": 8},
            {"name": "Increase inventory", "impact_pct": 6},
        ]

    series = df[metric_column].dropna()
    if series.empty:
        return []

    baseline = float(series.mean())
    latest = float(series.iloc[-1])

    # Optional informed multiplier from correlation
    multiplier = 1.0
    if driver_column and driver_column in df.columns:
        numeric = df.select_dtypes(include=[np.number])
        if driver_column in numeric.columns and metric_column in numeric.columns:
            corr = numeric[metric_column].corr(numeric[driver_column])
            if pd.notna(corr) and abs(corr) > 0.3:
                multiplier = max(0.5, min(abs(corr) * 2, 2.0))

    results = []
    for scenario in scenarios:
        impact_pct = scenario.get("impact_pct", 0) * multiplier
        projected = latest * (1 + impact_pct / 100)
        delta = projected - baseline
        results.append(
            {
                "name": scenario.get("name", "Unnamed scenario"),
                "baseline": round(baseline, 2),
                "latest": round(latest, 2),
                "projected": round(projected, 2),
                "delta": round(delta, 2),
                "assumption": f"Assumes a {impact_pct:.1f}% direct impact on {metric_column}.",
            }
        )
    return results
