"""Data Analyst Copilot — the main entry point.

Combines the query engine, root cause analyzer, insight generator,
and report generator into a single conversational interface.

Usage:
    from ai_copilot import DataAnalystCopilot

    copilot = DataAnalystCopilot(df, mapping_result)
    answer = copilot.ask("Why did sales drop?")
    # → "Sales dropped 15%. Main reasons: 1. Product A declined..."

    insights = copilot.auto_insights()
    report = copilot.generate_report()
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ai_copilot.insight_generator import AutoInsight, InsightGenerator
from ai_copilot.query_engine import ParsedQuery, QueryEngine, QueryIntent
from ai_copilot.report_generator import Report, ReportGenerator
from ai_copilot.root_cause import RootCauseAnalyzer, RootCauseResult


@dataclass
class CopilotResponse:
    """A response from the Data Analyst Copilot."""

    question: str
    intent: str
    answer: str
    data: dict = field(default_factory=dict)
    follow_ups: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "intent": self.intent,
            "answer": self.answer,
            "data": self.data,
            "follow_ups": self.follow_ups,
        }


class DataAnalystCopilot:
    """AI Data Analyst Copilot — answers natural language questions about data.

    Works locally using statistical analysis. No LLM required.
    Can optionally enhance answers with LLM calls via the ai/gateway.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        mapping_result: object | None = None,
        industry_intelligence: object | None = None,
    ):
        self.df = df
        self.mapping_result = mapping_result
        self.industry_intelligence = industry_intelligence
        self._col_mapping: dict[str, str] = {}

        if mapping_result:
            sem_result = getattr(mapping_result, "semantic_result", None)
            if sem_result and hasattr(sem_result, "get_column_mapping"):
                self._col_mapping = sem_result.get_column_mapping()

    def ask(self, question: str) -> CopilotResponse:
        """Answer a natural language question about the data.

        Args:
            question: User's natural language question.

        Returns:
            CopilotResponse with the answer, structured data, and follow-up suggestions.
        """
        parsed = QueryEngine.parse(question, self._col_mapping)

        if parsed.intent == QueryIntent.WHY_CHANGE:
            return self._answer_why_change(parsed)
        elif parsed.intent == QueryIntent.TOP_N:
            return self._answer_top_n(parsed)
        elif parsed.intent == QueryIntent.SUMMARY:
            return self._answer_summary(parsed)
        elif parsed.intent == QueryIntent.TREND:
            return self._answer_trend(parsed)
        elif parsed.intent == QueryIntent.COMPARISON:
            return self._answer_comparison(parsed)
        elif parsed.intent == QueryIntent.BREAKDOWN:
            return self._answer_breakdown(parsed)
        elif parsed.intent == QueryIntent.ANOMALY:
            return self._answer_anomaly(parsed)
        elif parsed.intent == QueryIntent.CORRELATION:
            return self._answer_correlation(parsed)
        elif parsed.intent == QueryIntent.DESCRIBE:
            return self._answer_describe(parsed)
        else:
            return self._answer_unknown(parsed)

    def auto_insights(self, max_insights: int = 15) -> list[AutoInsight]:
        """Generate automated insights from the data."""
        return InsightGenerator.generate(self.df, self._col_mapping, max_insights)

    def generate_report(self, title: str | None = None) -> Report:
        """Generate a comprehensive report."""
        insights = self.auto_insights()
        return ReportGenerator.generate(
            self.df,
            mapping_result=self.mapping_result,
            industry_intelligence=self.industry_intelligence,
            insights=insights,
            title=title,
        )

    # ── Intent Handlers ────────────────────────────────────

    def _answer_why_change(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer 'Why did X change?' questions with root cause analysis."""
        metric_col = self._resolve_metric_column(parsed.metric)
        date_col = self._resolve_date_column()
        dimension_cols = self._resolve_dimension_columns()

        if not metric_col or not date_col:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="I need a numeric metric column and a date column to analyze changes. "
                       "Please ensure your data has both.",
                follow_ups=["What metrics are available?", "Give me a summary"],
            )

        result = RootCauseAnalyzer.analyze(
            self.df, metric_col, date_col, dimension_cols,
            metric_label=parsed.metric.replace("_", " ").title() if parsed.metric else metric_col,
            direction=parsed.direction,
        )

        if result is None:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="I couldn't perform root cause analysis — insufficient data or no detectable change.",
                follow_ups=["Give me a summary", "Any anomalies?"],
            )

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=result.summary,
            data=result.to_dict(),
            follow_ups=[
                f"Break down {result.metric_label} by category",
                "What's the trend?",
                "Any anomalies?",
            ],
        )

    def _answer_top_n(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer 'Top N items' questions."""
        metric_col = self._resolve_metric_column(parsed.metric)
        dimension_col = self._resolve_dimension_column(parsed.dimension)

        if not dimension_col:
            # Use first categorical column
            for c in self.df.columns:
                if self.df[c].dtype == "object" and self.df[c].nunique() < 50:
                    dimension_col = c
                    break

        if not metric_col:
            # Use first numeric column
            for c in self.df.columns:
                if pd.api.types.is_numeric_dtype(self.df[c]):
                    metric_col = c
                    break

        if not dimension_col or not metric_col:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="I need at least one category column and one numeric column to rank items.",
                follow_ups=["Give me a summary"],
            )

        grouped = self.df.groupby(dimension_col)[metric_col].sum().sort_values(ascending=False).head(parsed.top_n)

        lines = [f"**Top {parsed.top_n} {dimension_col.replace('_', ' ').title()} by {metric_col.replace('_', ' ').title()}:**\n"]
        for i, (name, value) in enumerate(grouped.items(), 1):
            lines.append(f"{i}. **{name}**: {value:,.2f}")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={
                "dimension": dimension_col,
                "metric": metric_col,
                "items": [{str(k): float(v)} for k, v in grouped.items()],
            },
            follow_ups=[
                f"Why did {metric_col} change?",
                f"Break down {metric_col} by {dimension_col}",
                "Any anomalies?",
            ],
        )

    def _answer_summary(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer 'Give me a summary' questions."""
        df = self.df
        industry = getattr(self.mapping_result, "industry", "unknown") if self.mapping_result else "unknown"

        lines = [f"**Dataset Summary**\n"]
        lines.append(f"- **Records**: {len(df):,}")
        lines.append(f"- **Columns**: {len(df.columns)}")
        lines.append(f"- **Industry**: {industry.title()}")

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            lines.append(f"\n**Key Statistics:**")
            for col in numeric_cols[:5]:
                total = float(df[col].sum())
                avg = float(df[col].mean())
                lines.append(f"- **{col.replace('_', ' ').title()}**: Total={total:,.2f}, Avg={avg:,.2f}")

        # Add industry intelligence insights if available
        if self.industry_intelligence:
            insights = getattr(self.industry_intelligence, "insights", [])
            if insights:
                lines.append(f"\n**Industry Insights:**")
                for insight in insights[:5]:
                    lines.append(f"- **{insight.title}**: {insight.formatted}")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={
                "row_count": len(df),
                "col_count": len(df.columns),
                "industry": industry,
            },
            follow_ups=[
                "Why did revenue change?",
                "Top 5 products by sales",
                "Any anomalies?",
            ],
        )

    def _answer_trend(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer trend-related questions."""
        metric_col = self._resolve_metric_column(parsed.metric)
        date_col = self._resolve_date_column()

        if not date_col:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="No date column found — trend analysis requires a time-based column.",
                follow_ups=["Give me a summary"],
            )

        if not metric_col:
            for c in self.df.columns:
                if pd.api.types.is_numeric_dtype(self.df[c]) and c != date_col:
                    metric_col = c
                    break

        if not metric_col:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="No numeric column found for trend analysis.",
                follow_ups=["Give me a summary"],
            )

        df_temp = self.df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_temp[date_col]):
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
        df_temp = df_temp.dropna(subset=[date_col])

        if df_temp.empty:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="No valid date records found for trend analysis.",
                follow_ups=["Give me a summary"],
            )

        df_temp["_period"] = df_temp[date_col].dt.to_period("M").astype(str)
        monthly = df_temp.groupby("_period")[metric_col].sum()

        lines = [f"**{metric_col.replace('_', ' ').title()} Trend (Monthly):**\n"]
        for period, value in monthly.items():
            lines.append(f"- **{period}**: {value:,.2f}")

        if len(monthly) >= 2:
            first = float(monthly.iloc[0])
            last = float(monthly.iloc[-1])
            if first != 0:
                change = ((last - first) / abs(first)) * 100
                direction = "increase" if change > 0 else "decrease"
                lines.append(f"\nOverall: {direction} of {abs(change):.1f}% from {first:,.0f} to {last:,.0f}")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={
                "metric": metric_col,
                "periods": list(monthly.index.astype(str)),
                "values": [float(v) for v in monthly.values],
            },
            follow_ups=[
                f"Why did {metric_col} change?",
                f"Top 5 by {metric_col}",
                "Any anomalies?",
            ],
        )

    def _answer_comparison(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer comparison questions."""
        metric_col = self._resolve_metric_column(parsed.metric)
        dimension_col = self._resolve_dimension_column(parsed.dimension)

        if not dimension_col:
            for c in self.df.columns:
                if self.df[c].dtype == "object" and self.df[c].nunique() < 20:
                    dimension_col = c
                    break

        if not metric_col:
            for c in self.df.columns:
                if pd.api.types.is_numeric_dtype(self.df[c]):
                    metric_col = c
                    break

        if not dimension_col or not metric_col:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="I need a category column and a numeric column to make comparisons.",
                follow_ups=["Give me a summary"],
            )

        grouped = self.df.groupby(dimension_col)[metric_col].agg(["sum", "mean", "count"])
        grouped = grouped.sort_values("sum", ascending=False)

        lines = [f"**Comparison: {metric_col.replace('_', ' ').title()} by {dimension_col.replace('_', ' ').title()}**\n"]
        lines.append(f"| {dimension_col.title()} | Total | Average | Count |")
        lines.append(f"| --- | --- | --- | --- |")
        for name, row in grouped.iterrows():
            lines.append(f"| {name} | {row['sum']:,.2f} | {row['mean']:,.2f} | {int(row['count'])} |")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={
                "dimension": dimension_col,
                "metric": metric_col,
                "comparison": {str(k): {"sum": float(v["sum"]), "mean": float(v["mean"]), "count": int(v["count"])}
                              for k, v in grouped.to_dict("index").items()},
            },
            follow_ups=[
                f"Why did {metric_col} change?",
                f"Top 5 by {metric_col}",
                "Any anomalies?",
            ],
        )

    def _answer_breakdown(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer breakdown questions."""
        return self._answer_comparison(parsed)

    def _answer_anomaly(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer anomaly detection questions."""
        insights = InsightGenerator.generate(self.df, self._col_mapping, max_insights=10)
        anomaly_insights = [i for i in insights if i.type.value == "anomaly" or i.type.value == "quality"]

        if not anomaly_insights:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="No significant anomalies detected. The data looks clean and within expected ranges.",
                follow_ups=["Give me a summary", "What's the trend?"],
            )

        lines = ["**Detected Anomalies:**\n"]
        for i, insight in enumerate(anomaly_insights, 1):
            icon = "🔴" if insight.severity.value == "critical" else "⚠️"
            lines.append(f"{i}. {icon} **{insight.title}**: {insight.description}")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={"anomalies": [i.to_dict() for i in anomaly_insights]},
            follow_ups=["Give me a summary", "Generate a report"],
        )

    def _answer_correlation(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer correlation questions."""
        numeric_cols = [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]

        if len(numeric_cols) < 2:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="Need at least 2 numeric columns to compute correlations.",
                follow_ups=["Give me a summary"],
            )

        corr = self.df[numeric_cols].corr()
        pairs = []
        seen = set()

        for i, c1 in enumerate(numeric_cols):
            for j, c2 in enumerate(numeric_cols):
                if i >= j:
                    continue
                pair = tuple(sorted([c1, c2]))
                if pair in seen:
                    continue
                seen.add(pair)
                val = corr.loc[c1, c2]
                if not pd.isna(val) and abs(val) >= 0.3:
                    pairs.append((c1, c2, float(val)))

        pairs.sort(key=lambda x: abs(x[2]), reverse=True)

        if not pairs:
            return CopilotResponse(
                question=parsed.raw_text,
                intent=parsed.intent.value,
                answer="No significant correlations (|r| ≥ 0.3) found between numeric columns.",
                follow_ups=["Give me a summary", "Any anomalies?"],
            )

        lines = ["**Correlations Found:**\n"]
        for c1, c2, val in pairs[:10]:
            direction = "positive" if val > 0 else "negative"
            strength = "strong" if abs(val) >= 0.7 else "moderate" if abs(val) >= 0.5 else "weak"
            lines.append(f"- **{c1} ↔ {c2}**: r={val:.2f} ({strength} {direction})")

        answer = "\n".join(lines)

        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=answer,
            data={"correlations": [{"col1": c1, "col2": c2, "correlation": val} for c1, c2, val in pairs[:10]]},
            follow_ups=["Give me a summary", "Any anomalies?"],
        )

    def _answer_describe(self, parsed: ParsedQuery) -> CopilotResponse:
        """Answer describe questions."""
        return self._answer_summary(parsed)

    def _answer_unknown(self, parsed: ParsedQuery) -> CopilotResponse:
        """Handle unrecognized queries."""
        return CopilotResponse(
            question=parsed.raw_text,
            intent=parsed.intent.value,
            answer=(
                "I can help you understand your data. Try asking:\n"
                "- **'Why did sales drop?'** — Root cause analysis\n"
                "- **'Top 5 products by revenue'** — Rankings\n"
                "- **'Give me a summary'** — Dataset overview\n"
                "- **'What's the trend in billing?'** — Time analysis\n"
                "- **'Compare regions'** — Dimension comparison\n"
                "- **'Any anomalies?'** — Outlier detection\n"
                "- **'Correlation between sales and profit'** — Relationships"
            ),
            follow_ups=[
                "Give me a summary",
                "Why did revenue change?",
                "Any anomalies?",
            ],
        )

    # ── Column Resolution Helpers ──────────────────────────

    def _resolve_metric_column(self, metric: str | None) -> str | None:
        """Resolve a metric entity key to an actual DataFrame column."""
        if not metric:
            # Try to find revenue/sales/amount column
            for entity_key in ("revenue", "sales", "billing", "amount", "donation", "production"):
                col = self._find_col_by_entity(entity_key)
                if col:
                    return col
            return None

        return self._find_col_by_entity(metric)

    def _resolve_date_column(self) -> str | None:
        """Find the date column."""
        # Check col_mapping first
        for col, entity in self._col_mapping.items():
            if entity == "date" and col in self.df.columns:
                return col
        # Check by dtype
        for c in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[c]):
                return c
        # Check by name
        lower_map = {c.lower(): c for c in self.df.columns}
        for name in ("date", "order_date", "visit_date", "transaction_date", "created_at", "record_date"):
            if name in lower_map:
                return lower_map[name]
        return None

    def _resolve_dimension_columns(self) -> list[str]:
        """Find all dimension columns (categorical, non-date, non-metric)."""
        dims = []
        for col, entity in self._col_mapping.items():
            if entity not in ("date", "revenue", "sales", "billing", "amount", "profit", "donation", "production"):
                if col in self.df.columns and self.df[col].dtype == "object":
                    dims.append(col)
        # Fallback: add all categorical columns
        if not dims:
            for c in self.df.columns:
                if self.df[c].dtype == "object" and self.df[c].nunique() < 50:
                    dims.append(c)
        return list(set(dims))

    def _resolve_dimension_column(self, dimension: str | None) -> str | None:
        """Resolve a dimension entity key to a DataFrame column."""
        if not dimension:
            return None
        return self._find_col_by_entity(dimension)

    def _find_col_by_entity(self, entity_key: str) -> str | None:
        """Find a DataFrame column by entity key, preferring numeric columns for metrics."""
        # Check col_mapping
        candidates = [col for col, entity in self._col_mapping.items() if entity == entity_key and col in self.df.columns]
        if candidates:
            # Prefer numeric columns
            for col in candidates:
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    return col
            return candidates[0]
        # Fallback: search by name
        lower_map = {c.lower(): c for c in self.df.columns}
        if entity_key in lower_map:
            return lower_map[entity_key]
        for col_lower, col in lower_map.items():
            if entity_key in col_lower:
                return col
        return None
