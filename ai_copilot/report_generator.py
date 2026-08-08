"""Report Generator.

Generates structured narrative reports from the semantic model,
industry intelligence, and automated insights. Reports include:
  - Executive Summary
  - Key Metrics
  - Trend Analysis
  - Industry-Specific Insights
  - Data Quality Assessment
  - Recommendations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class ReportSection:
    """A section of a generated report."""

    title: str
    content: str
    bullets: list[str] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "bullets": self.bullets,
            "tables": self.tables,
        }


@dataclass
class Report:
    """A complete generated report."""

    title: str
    industry: str
    generated_at: str
    sections: list[ReportSection] = field(default_factory=list)
    summary: str = ""

    def to_markdown(self) -> str:
        """Render the report as Markdown."""
        lines = [f"# {self.title}", ""]
        lines.append(f"*Industry: {self.industry.title()} | Generated: {self.generated_at}*")
        lines.append("")

        if self.summary:
            lines.append(f"**Executive Summary:** {self.summary}")
            lines.append("")

        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            if section.content:
                lines.append(section.content)
                lines.append("")
            for bullet in section.bullets:
                lines.append(f"- {bullet}")
            if section.bullets:
                lines.append("")
            for table in section.tables:
                lines.append(f"**{table.get('title', '')}**")
                lines.append("")
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                if headers:
                    lines.append("| " + " | ".join(headers) + " |")
                    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for row in rows:
                        lines.append("| " + " | ".join(str(v) for v in row) + " |")
                    lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "industry": self.industry,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections],
        }


class ReportGenerator:
    """Generates structured reports from data and semantic analysis."""

    @staticmethod
    def generate(
        df: pd.DataFrame,
        mapping_result: object | None = None,
        industry_intelligence: object | None = None,
        insights: list | None = None,
        title: str | None = None,
    ) -> Report:
        """Generate a comprehensive report from the data.

        Args:
            df: The DataFrame to report on.
            mapping_result: SemanticMappingResult (optional).
            industry_intelligence: AnalyticsResult from industry_intelligence (optional).
            insights: List of AutoInsight objects (optional).
            title: Custom report title.

        Returns:
            Report with structured sections.
        """
        industry = getattr(mapping_result, "industry", "unknown") if mapping_result else "unknown"
        dataset_name = getattr(mapping_result, "table_metadata", None)
        dataset_name = getattr(dataset_name, "table_name", "dataset") if dataset_name else "dataset"

        title = title or f"{industry.title()} Data Analysis Report"
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        sections: list[ReportSection] = []

        # 1. Overview
        sections.append(ReportGenerator._overview_section(df, dataset_name, industry))

        # 2. Key Metrics
        sections.append(ReportGenerator._key_metrics_section(df, mapping_result))

        # 3. Industry-Specific Insights
        if industry_intelligence:
            sections.append(ReportGenerator._industry_insights_section(industry_intelligence))

        # 4. Trend Analysis
        sections.append(ReportGenerator._trend_section(df, mapping_result))

        # 5. Automated Insights
        if insights:
            sections.append(ReportGenerator._insights_section(insights))

        # 6. Recommendations
        sections.append(ReportGenerator._recommendations_section(industry_intelligence, insights))

        # Generate executive summary
        summary = ReportGenerator._executive_summary(df, industry, industry_intelligence, insights)

        return Report(
            title=title,
            industry=industry,
            generated_at=generated_at,
            sections=sections,
            summary=summary,
        )

    @staticmethod
    def _overview_section(df: pd.DataFrame, dataset_name: str, industry: str) -> ReportSection:
        row_count = len(df)
        col_count = len(df.columns)
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        text_cols = [c for c in df.columns if df[c].dtype == "object"]
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        return ReportSection(
            title="Dataset Overview",
            content=(
                f"This report analyzes **{dataset_name}**, containing {row_count:,} records "
                f"across {col_count} columns. The dataset has been classified as "
                f"**{industry.title()}** industry."
            ),
            bullets=[
                f"Total records: {row_count:,}",
                f"Total columns: {col_count}",
                f"Numeric columns: {len(numeric_cols)}",
                f"Text columns: {len(text_cols)}",
                f"Date columns: {len(date_cols)}",
            ],
        )

    @staticmethod
    def _key_metrics_section(df: pd.DataFrame, mapping_result: object | None) -> ReportSection:
        bullets = []
        tables = []

        # From semantic model metrics if available
        semantic_model = getattr(mapping_result, "semantic_model", None) if mapping_result else None
        if semantic_model and hasattr(semantic_model, "metrics"):
            metric_rows = []
            for m in semantic_model.metrics[:10]:
                metric_rows.append([m.label, f"{m.value:,.2f}" if m.value else "N/A"])
            if metric_rows:
                tables.append(
                    {
                        "title": "Computed Metrics",
                        "headers": ["Metric", "Value"],
                        "rows": metric_rows,
                    }
                )

        # Basic stats
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for col in numeric_cols[:5]:
            total = float(df[col].sum())
            avg = float(df[col].mean())
            bullets.append(
                f"**{col.replace('_', ' ').title()}**: Total={total:,.2f}, Average={avg:,.2f}"
            )

        return ReportSection(
            title="Key Metrics",
            content="Summary of key metrics computed from the dataset.",
            bullets=bullets,
            tables=tables,
        )

    @staticmethod
    def _industry_insights_section(intelligence: object) -> ReportSection:
        bullets = []
        insights_list = getattr(intelligence, "insights", [])
        for insight in insights_list[:10]:
            line = f"**{insight.title}**: {insight.formatted}"
            if insight.alert and insight.alert != "ok":
                line += f" ⚠️ ({insight.alert})"
            bullets.append(line)

        # Add alerts
        alerts = getattr(intelligence, "alerts", [])
        alert_bullets = [f"⚠️ {a}" for a in alerts] if alerts else []

        return ReportSection(
            title="Industry-Specific Insights",
            content=f"Specialized analytics for the {getattr(intelligence, 'industry', 'unknown').title()} sector.",
            bullets=bullets + alert_bullets,
        )

    @staticmethod
    def _trend_section(df: pd.DataFrame, mapping_result: object | None) -> ReportSection:
        bullets = []

        # Find date column
        date_col = None
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
        if date_col is None and mapping_result:
            col_mapping = {}
            sem_result = getattr(mapping_result, "semantic_result", None)
            if sem_result and hasattr(sem_result, "get_column_mapping"):
                col_mapping = sem_result.get_column_mapping()
            for col, entity in col_mapping.items():
                if entity == "date" and col in df.columns:
                    date_col = col
                    break

        if date_col and date_col in df.columns:
            df_temp = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_temp[date_col]):
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
            df_temp = df_temp.dropna(subset=[date_col])

            if not df_temp.empty:
                date_range = f"{df_temp[date_col].min().date()} to {df_temp[date_col].max().date()}"
                bullets.append(f"Date range: {date_range}")

                numeric_cols = [
                    c
                    for c in df_temp.columns
                    if pd.api.types.is_numeric_dtype(df_temp[c]) and c != date_col
                ]
                for col in numeric_cols[:3]:
                    df_temp["_period"] = df_temp[date_col].dt.to_period("M").astype(str)
                    monthly = df_temp.groupby("_period")[col].sum()
                    if len(monthly) >= 2:
                        first_val = float(monthly.iloc[0])
                        last_val = float(monthly.iloc[-1])
                        if first_val != 0:
                            change = ((last_val - first_val) / abs(first_val)) * 100
                            direction = "increase" if change > 0 else "decrease"
                            bullets.append(
                                f"**{col.replace('_', ' ').title()}** trend: {direction} of {abs(change):.1f}% "
                                f"from {first_val:,.0f} to {last_val:,.0f}"
                            )
        else:
            bullets.append("No date column found — trend analysis not available.")

        return ReportSection(
            title="Trend Analysis",
            content="Time-based analysis of key metrics.",
            bullets=bullets,
        )

    @staticmethod
    def _insights_section(insights: list) -> ReportSection:
        bullets = []
        for insight in insights[:10]:
            icon = (
                "⚠️"
                if insight.severity.value == "warning"
                else (
                    "🔴"
                    if insight.severity.value == "critical"
                    else "✅" if insight.severity.value == "positive" else "ℹ️"
                )
            )
            bullets.append(f"{icon} **{insight.title}**: {insight.description}")

        return ReportSection(
            title="Automated Insights",
            content="Patterns and anomalies automatically detected in the data.",
            bullets=bullets,
        )

    @staticmethod
    def _recommendations_section(
        intelligence: object | None, insights: list | None
    ) -> ReportSection:
        bullets = []

        # From industry intelligence
        if intelligence:
            recs = getattr(intelligence, "recommendations", [])
            for rec in recs[:5]:
                bullets.append(rec)

        # From insights
        if insights:
            for insight in insights:
                if insight.recommendation and insight.severity.value in ("warning", "critical"):
                    bullets.append(insight.recommendation)

        if not bullets:
            bullets.append("Continue regular data monitoring and quality checks.")

        # Deduplicate
        seen = set()
        unique_bullets = []
        for b in bullets:
            if b not in seen:
                seen.add(b)
                unique_bullets.append(b)

        return ReportSection(
            title="Recommendations",
            content="Actionable next steps based on the analysis.",
            bullets=unique_bullets[:10],
        )

    @staticmethod
    def _executive_summary(
        df: pd.DataFrame,
        industry: str,
        intelligence: object | None,
        insights: list | None,
    ) -> str:
        parts = [f"This dataset contains {len(df):,} records classified as {industry.title()}."]

        if intelligence:
            insight_count = len(getattr(intelligence, "insights", []))
            alert_count = len(getattr(intelligence, "alerts", []))
            parts.append(f"Industry intelligence identified {insight_count} insights")
            if alert_count:
                parts.append(f"with {alert_count} alerts requiring attention")

        if insights:
            critical = sum(1 for i in insights if i.severity.value == "critical")
            warnings = sum(1 for i in insights if i.severity.value == "warning")
            if critical or warnings:
                parts.append(
                    f"Automated analysis found {critical} critical and {warnings} warning-level patterns"
                )

        return ". ".join(parts) + "."
