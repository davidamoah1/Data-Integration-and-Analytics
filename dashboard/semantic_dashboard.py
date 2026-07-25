from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import CHART_LAYOUT
from dashboard.utils import fmt_currency, fmt_number
from semantic.dashboard_registry import DashboardRegistry, WidgetDefinition
from semantic.mapping_engine import SemanticMappingResult


def render_semantic_dashboard(
    df: pd.DataFrame,
    mapping_result: SemanticMappingResult,
    admin_confirmed: bool = False,
) -> None:
    confidence = mapping_result.industry_confidence
    if confidence < 85.0 and not admin_confirmed and mapping_result.industry != "unknown":
        st.warning(
            f"Industry confidence is {confidence:.0f}% (below 85% threshold). "
            f"Detected industry: '{mapping_result.industry}'. "
            f"Admin confirmation required to generate the dashboard."
        )
        return
    template = DashboardRegistry.get(mapping_result.industry)
    if template is None:
        st.warning(
            f"No dashboard template found for industry '{mapping_result.industry}'. "
            f"Confidence: {mapping_result.industry_confidence:.0f}%. "
            f"Please confirm the industry or register a template."
        )
        return
    entity_columns = _entity_columns(mapping_result)
    st.markdown(
        f'<div class="section-header">{html.escape(template.title)}</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Industry detected: {mapping_result.industry.title()} "
        f"({mapping_result.industry_confidence:.0f}% confidence)"
    )

    if mapping_result.industry == "unknown":
        _render_generic_dashboard(df, template)
        return

    # Show value-based signals if any were detected
    value_signals = getattr(mapping_result.semantic_result, "value_signals", [])
    if value_signals:
        with st.expander("Data Understanding Signals", expanded=False):
            for sig in value_signals:
                st.caption(
                    f"• **{sig.column_name}** → {sig.signal_type.replace("_", " ").title()} "
                    f"({sig.industry}): {sig.evidence}"
                )

    cards = [widget for widget in template.widgets if widget.widget_type == "kpi_card"]
    charts = [widget for widget in template.widgets if widget.widget_type != "kpi_card"]
    _render_cards(df, cards, entity_columns)
    _render_charts(df, charts, entity_columns)
    if template.ai_insights:
        st.markdown(
            '<div class="section-header">Suggested AI Insights</div><hr class="section-divider">',
            unsafe_allow_html=True,
        )
        for insight in template.ai_insights:
            st.caption(f"• {insight}")


def _entity_columns(mapping_result: SemanticMappingResult) -> dict[str, list[str]]:
    columns: dict[str, list[str]] = {}
    for mapping in mapping_result.semantic_result.mappings:
        columns.setdefault(mapping.entity_key, []).append(mapping.column_name)
    return columns


def _render_generic_dashboard(df: pd.DataFrame, template: DashboardTemplate) -> None:
    """Render a generic analytics dashboard for unknown industries."""
    from dashboard.utils import fmt_number

    # Dataset overview cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", fmt_number(len(df)))
    with col2:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        st.metric("Numeric Columns", str(len(numeric_cols)))
    with col3:
        text_cols = [c for c in df.columns if df[c].dtype == "object"]
        st.metric("Text Columns", str(len(text_cols)))
    with col4:
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        st.metric("Date Columns", str(len(date_cols)))

    # Statistics summary
    st.markdown(
        '<div class="section-header">Statistical Summary</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)
    else:
        st.info("No numeric columns found for statistical summary.")

    # Missing values
    st.markdown(
        '<div class="section-header">Missing Values</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({"Missing Count": missing, "Missing %": missing_pct})
    missing_df = missing_df[missing_df["Missing Count"] > 0].sort_values("Missing Count", ascending=False)
    if missing_df.empty:
        st.success("No missing values detected in the dataset.")
    else:
        st.dataframe(missing_df, use_container_width=True)

    # Trends (if a date column exists)
    date_col = None
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            date_col = c
            break
    if date_col and numeric_cols:
        st.markdown(
            '<div class="section-header">Trends Over Time</div><hr class="section-divider">',
            unsafe_allow_html=True,
        )
        try:
            trend_df = df.copy()
            trend_df[date_col] = pd.to_datetime(trend_df[date_col], errors="coerce")
            trend_df = trend_df.dropna(subset=[date_col])
            if not trend_df.empty:
                first_numeric = numeric_cols[0]
                trend_data = (
                    trend_df.groupby(trend_df[date_col].dt.to_period("M").astype(str))[first_numeric]
                    .sum()
                    .reset_index()
                )
                fig = px.line(trend_data, x=date_col, y=first_numeric, title=f"{first_numeric} Trend", template="none")
                fig.update_layout(**CHART_LAYOUT, height=300)
                st.plotly_chart(fig, use_container_width=True)
        except (KeyError, TypeError, ValueError):
            pass

    # Correlations
    if len(numeric_cols) >= 2:
        st.markdown(
            '<div class="section-header">Correlation Matrix</div><hr class="section-divider">',
            unsafe_allow_html=True,
        )
        try:
            corr = df[numeric_cols].corr().round(2)
            fig = px.imshow(corr, title="Numeric Correlations", template="none", color_continuous_scale="RdBu_r")
            fig.update_layout(**CHART_LAYOUT, height=400)
            st.plotly_chart(fig, use_container_width=True)
        except (KeyError, TypeError, ValueError):
            pass

    # AI insights
    if template.ai_insights:
        st.markdown(
            '<div class="section-header">Suggested AI Insights</div><hr class="section-divider">',
            unsafe_allow_html=True,
        )
        for insight in template.ai_insights:
            st.caption(f"• {insight}")


def _render_cards(
    df: pd.DataFrame, widgets: list[WidgetDefinition], entity_columns: dict[str, list[str]]
) -> None:
    for start in range(0, len(widgets), 4):
        row = widgets[start : start + 4]
        for container, widget in zip(st.columns(4), row, strict=False):
            with container:
                value = _widget_value(df, widget, entity_columns)
                display = _format_value(value, widget.metric) if value is not None else "N/A"
                st.markdown(
                    f'<div class="kpi-card kpi-card-{html.escape(widget.category)}">'
                    f'<div class="kpi-value">{display}</div>'
                    f'<div class="kpi-label">{html.escape(widget.title)}</div></div>',
                    unsafe_allow_html=True,
                )


def _render_charts(
    df: pd.DataFrame, widgets: list[WidgetDefinition], entity_columns: dict[str, list[str]]
) -> None:
    available = [widget for widget in widgets if _is_available(widget, entity_columns)]
    if not available:
        return
    st.markdown(
        '<div class="section-header">Semantic Analysis</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    for start in range(0, len(available), 2):
        row = available[start : start + 2]
        for container, widget in zip(st.columns(2), row, strict=False):
            with container:
                _render_chart(df, widget, entity_columns)


def _render_chart(
    df: pd.DataFrame, widget: WidgetDefinition, entity_columns: dict[str, list[str]]
) -> None:
    value_col = _first_column(widget.entity, entity_columns)
    group_col = _first_column(widget.group_by, entity_columns)
    if not value_col:
        return
    chart_data = df.copy()
    try:
        if widget.widget_type == "line_chart":
            date_col = group_col or _first_column(widget.time_entity, entity_columns)
            if not date_col:
                return
            chart_data[date_col] = pd.to_datetime(chart_data[date_col], errors="coerce")
            chart_data = chart_data.dropna(subset=[date_col])
            if chart_data.empty:
                return
            y_col = value_col if pd.api.types.is_numeric_dtype(chart_data[value_col]) else None
            if y_col:
                chart_data = (
                    chart_data.groupby(chart_data[date_col].dt.to_period("M").astype(str))[y_col]
                    .sum()
                    .reset_index()
                )
            else:
                chart_data = (
                    chart_data.groupby(chart_data[date_col].dt.to_period("M").astype(str))
                    .size()
                    .reset_index(name="count")
                )
                y_col = "count"
            fig = px.line(chart_data, x=date_col, y=y_col, title=widget.title, template="none")
        elif widget.widget_type in {"bar_chart", "leaderboard", "gauge", "heat_map"}:
            if not group_col:
                return
            if pd.api.types.is_numeric_dtype(chart_data[value_col]) and value_col != group_col:
                chart_data = chart_data.groupby(group_col)[value_col].sum().reset_index()
                y_col = value_col
            else:
                chart_data = chart_data.groupby(group_col).size().reset_index(name="count")
                y_col = "count"
            chart_data = chart_data.sort_values(y_col, ascending=False).head(15)
            if widget.widget_type == "heat_map":
                fig = px.density_heatmap(
                    chart_data, x=group_col, y=y_col, title=widget.title, template="none"
                )
            else:
                fig = px.bar(chart_data, x=group_col, y=y_col, title=widget.title, template="none")
        elif widget.widget_type == "pie_chart":
            if not group_col:
                return
            chart_data = chart_data.groupby(group_col).size().reset_index(name="count")
            fig = px.pie(
                chart_data, names=group_col, values="count", title=widget.title, template="none"
            )
        else:
            return
    except (KeyError, TypeError, ValueError):
        return
    fig.update_layout(**CHART_LAYOUT, height=300)
    st.plotly_chart(fig, use_container_width=True)


def _widget_value(
    df: pd.DataFrame, widget: WidgetDefinition, entity_columns: dict[str, list[str]]
) -> float | int | None:
    value_col = _first_column(widget.entity, entity_columns)
    if not value_col or value_col not in df.columns:
        return None
    if widget.metric == "sum" and pd.api.types.is_numeric_dtype(df[value_col]):
        return float(df[value_col].sum())
    return int(df[value_col].nunique())


def _is_available(widget: WidgetDefinition, entity_columns: dict[str, list[str]]) -> bool:
    return all(_first_column(entity, entity_columns) for entity in widget.required_entities)


def _first_column(entity: str | None, entity_columns: dict[str, list[str]]) -> str | None:
    if not entity:
        return None
    columns = entity_columns.get(entity, [])
    return columns[0] if columns else None


def _format_value(value: float | int, metric: str) -> str:
    if metric == "sum":
        return fmt_currency(value)
    return fmt_number(value)
