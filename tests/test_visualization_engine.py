"""Tests for the Visualization Intelligence Engine.

Tests cover:
  - Full pipeline generation (dashboard + presentation)
  - Chart validation and fallback
  - New chart types (area, box plot, treemap)
  - Report integration with canonical specs
  - Schema versioning
  - Edge cases (empty data, single column, all NaN)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from services.auto.chart_specification import (
    ChartSpecification,
    DashboardSpecification,
    PresentationSpecification,
)
from services.auto.engine import VISUALIZATION_SCHEMA_VERSION, VisualizationIntelligenceEngine
from services.auto.validators import ChartValidator

# ── Fixtures ──────────────────────────────────────────


@pytest.fixture
def sales_df() -> pd.DataFrame:
    """Retail sales dataset with time, category, geography, and measures."""
    np.random.seed(42)
    n = 200
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    regions = np.random.choice(["North", "South", "East", "West", "Central"], n)
    products = np.random.choice(
        ["Widget A", "Widget B", "Widget C", "Gadget X", "Gadget Y", "Tool Z"], n
    )
    revenue = np.random.uniform(100, 5000, n).round(2)
    quantity = np.random.randint(1, 50, n)
    return pd.DataFrame(
        {
            "date": dates,
            "region": regions,
            "product": products,
            "revenue": revenue,
            "quantity": quantity,
        }
    )


@pytest.fixture
def many_categories_df() -> pd.DataFrame:
    """Dataset with many categories (suitable for treemap)."""
    np.random.seed(99)
    n = 300
    departments = [f"Dept_{i:02d}" for i in range(15)]
    dept_values = np.random.choice(departments, n)
    budget = np.random.uniform(1000, 50000, n).round(2)
    return pd.DataFrame(
        {
            "department": dept_values,
            "budget": budget,
        }
    )


@pytest.fixture
def minimal_df() -> pd.DataFrame:
    """Minimal single-column dataset."""
    return pd.DataFrame({"values": [1, 2, 3, 4, 5]})


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Empty DataFrame."""
    return pd.DataFrame(columns=["a", "b"])


@pytest.fixture
def engine() -> VisualizationIntelligenceEngine:
    return VisualizationIntelligenceEngine()


# ── Full Pipeline Tests ───────────────────────────────


class TestFullPipeline:
    """Test the complete visualization pipeline."""

    def test_generate_returns_all_keys(self, engine, sales_df):
        result = engine.generate(sales_df, dataset_name="sales", industry="retail")
        assert "understanding" in result
        assert "charts" in result
        assert "dashboard" in result
        assert "presentation" in result
        assert "schema_version" in result

    def test_schema_version(self, engine, sales_df):
        result = engine.generate(sales_df)
        assert result["schema_version"] == VISUALIZATION_SCHEMA_VERSION

    def test_dashboard_is_dashboard_spec(self, engine, sales_df):
        result = engine.generate(sales_df)
        assert isinstance(result["dashboard"], DashboardSpecification)

    def test_presentation_is_presentation_spec(self, engine, sales_df):
        result = engine.generate(sales_df)
        assert isinstance(result["presentation"], PresentationSpecification)

    def test_charts_are_chart_specifications(self, engine, sales_df):
        result = engine.generate(sales_df)
        for chart in result["charts"]:
            assert isinstance(chart, ChartSpecification)

    def test_dashboard_and_presentation_share_charts(self, engine, sales_df):
        result = engine.generate(sales_df)
        dashboard = result["dashboard"]
        presentation = result["presentation"]
        # Presentation should reference chart IDs from the dashboard
        dashboard_ids = {c.id for c in dashboard.charts}
        presentation_ids = set(presentation.included_chart_ids)
        assert presentation_ids.issubset(dashboard_ids)

    def test_generate_dashboard_only(self, engine, sales_df):
        dashboard = engine.generate_dashboard_only(sales_df, industry="retail")
        assert isinstance(dashboard, DashboardSpecification)
        assert len(dashboard.charts) > 0

    def test_generate_presentation_only(self, engine, sales_df):
        presentation = engine.generate_presentation_only(sales_df, industry="retail")
        assert isinstance(presentation, PresentationSpecification)

    def test_generate_chart_specs(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        assert len(charts) > 0
        for chart in charts:
            assert isinstance(chart, ChartSpecification)
            assert chart.data  # All charts should have data
            assert chart.title
            assert chart.reason  # All charts should have explanations


# ── Chart Type Tests ──────────────────────────────────


class TestChartTypes:
    """Test that the engine produces diverse chart types."""

    def test_produces_multiple_chart_types(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        chart_types = {c.chart_type for c in charts}
        # Should produce at least 3 different chart types
        assert len(chart_types) >= 3

    def test_produces_line_chart_for_time_data(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        chart_types = {c.chart_type for c in charts}
        assert "line_chart" in chart_types

    def test_produces_bar_chart_for_categorical(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        chart_types = {c.chart_type for c in charts}
        assert "bar_chart" in chart_types or "horizontal_bar" in chart_types

    def test_produces_area_chart_for_time_data(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        chart_types = {c.chart_type for c in charts}
        assert "area_chart" in chart_types

    def test_produces_box_plot(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        chart_types = {c.chart_type for c in charts}
        assert "box_plot" in chart_types

    def test_produces_treemap_for_many_categories(self, engine, many_categories_df):
        charts = engine.generate_chart_specs(many_categories_df, industry="government")
        chart_types = {c.chart_type for c in charts}
        assert "treemap" in chart_types


# ── Validation Tests ──────────────────────────────────


class TestChartValidation:
    """Test chart validation and fallback."""

    def test_validator_rejects_empty_data(self):
        validator = ChartValidator()
        chart = ChartSpecification(
            chart_type="bar_chart",
            title="Test",
            x_axis="x",
            y_axis="y",
            source_columns=["x", "y"],
            data=[],
        )
        df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
        result = validator.validate(chart, df)
        assert not result.valid
        assert "no data" in result.reason.lower()

    def test_validator_rejects_missing_column(self):
        validator = ChartValidator()
        chart = ChartSpecification(
            chart_type="bar_chart",
            title="Test",
            x_axis="x",
            y_axis="y",
            source_columns=["x", "nonexistent"],
            data=[{"x": "a", "y": 1}],
        )
        df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
        result = validator.validate(chart, df)
        assert not result.valid
        assert "nonexistent" in result.reason

    def test_validator_rejects_pie_too_many_categories(self):
        validator = ChartValidator()
        data = [{"x": f"cat_{i}", "y": i} for i in range(15)]
        chart = ChartSpecification(
            chart_type="pie_chart",
            title="Test Pie",
            source_columns=["x", "y"],
            data=data,
        )
        df = pd.DataFrame({"x": [d["x"] for d in data], "y": [d["y"] for d in data]})
        result = validator.validate(chart, df)
        assert not result.valid
        assert "15" in result.reason

    def test_validator_rejects_nan_values(self):
        validator = ChartValidator()
        chart = ChartSpecification(
            chart_type="bar_chart",
            title="Test",
            source_columns=["x", "y"],
            data=[{"x": "a", "y": float("nan")}],
        )
        df = pd.DataFrame({"x": ["a"], "y": [1.0]})
        result = validator.validate(chart, df)
        assert not result.valid
        assert "nan" in result.reason.lower()

    def test_validator_accepts_valid_chart(self):
        validator = ChartValidator()
        chart = ChartSpecification(
            chart_type="bar_chart",
            title="Test",
            x_axis="x",
            y_axis="y",
            source_columns=["x", "y"],
            data=[{"x": "a", "y": 10}, {"x": "b", "y": 20}],
        )
        df = pd.DataFrame({"x": ["a", "b"], "y": [10, 20]})
        result = validator.validate(chart, df)
        assert result.valid

    def test_validate_and_fallback_skips_invalid(self, engine, sales_df):
        """All charts returned by generate() should be valid."""
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        validator = ChartValidator()
        valid = validator.validate_and_fallback(charts, sales_df)
        assert len(valid) == len(charts)  # All should pass validation

    def test_explain_chart_returns_string(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        for chart in charts:
            explanation = engine.explain_chart(chart)
            assert isinstance(explanation, str)
            assert len(explanation) > 10


# ── Edge Case Tests ───────────────────────────────────


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_minimal_dataset(self, engine, minimal_df):
        charts = engine.generate_chart_specs(minimal_df)
        # Should produce at least one chart (histogram for single numeric column)
        # If no charts, the engine should still not crash
        assert isinstance(charts, list)

    def test_empty_dataset(self, engine, empty_df):
        charts = engine.generate_chart_specs(empty_df)
        # Should return empty list, not crash
        assert isinstance(charts, list)

    def test_all_nan_column(self, engine):
        df = pd.DataFrame(
            {
                "category": ["a", "b", "c"],
                "value": [float("nan"), float("nan"), float("nan")],
            }
        )
        # Should not crash
        charts = engine.generate_chart_specs(df)
        assert isinstance(charts, list)

    def test_single_row_dataset(self, engine):
        df = pd.DataFrame({"category": ["a"], "value": [100]})
        charts = engine.generate_chart_specs(df)
        assert isinstance(charts, list)

    def test_high_missing_percentage(self, engine):
        df = pd.DataFrame(
            {
                "category": ["a", "b", "c", None, None, None, None, None],
                "value": [1, 2, 3, 4, 5, 6, 7, 8],
            }
        )
        charts = engine.generate_chart_specs(df)
        assert isinstance(charts, list)

    def test_validate_chart_method(self, engine, sales_df):
        charts = engine.generate_chart_specs(sales_df, industry="retail")
        for chart in charts:
            is_valid, reason = engine.validate_chart(chart, sales_df)
            assert is_valid, f"Chart {chart.title} should be valid: {reason}"


# ── Report Integration Tests ──────────────────────────


class TestReportIntegration:
    """Test that the report engine can consume canonical chart specs."""

    def test_chart_definition_from_canonical_spec(self):
        from services.report_engine import ChartDefinition, ChartType

        spec = ChartSpecification(
            chart_type="line_chart",
            title="Revenue Over Time",
            x_axis="date",
            y_axis="revenue",
            source_columns=["date", "revenue"],
            data=[{"x": "2024-01", "y": 1000}],
            aggregation="sum",
            reason="Line chart shows trend over time",
            source_analysis="time_series",
            importance_score=85.0,
        )
        cd = ChartDefinition.from_canonical_spec(spec)
        assert cd.title == "Revenue Over Time"
        assert cd.chart_type == ChartType.LINE
        assert cd.x_axis == "date"
        assert cd.y_axis == "revenue"
        assert cd.config["original_chart_type"] == "line_chart"
        assert cd.config["chart_id"] == spec.id

    def test_populate_report_from_dashboard(self, engine, sales_df):
        from services.report_engine import (
            ReportCompositionService,
            ReportSectionType,
            ReportTemplate,
        )

        # Generate dashboard
        result = engine.generate(sales_df, dataset_name="sales", industry="retail")
        dashboard = result["dashboard"]

        # Create a report
        report = ReportCompositionService.create_report(
            title="Sales Report",
            template=ReportTemplate.EXECUTIVE,
            org_name="Test Org",
            industry="retail",
        )

        # Populate from dashboard spec
        populated = ReportCompositionService.populate_from_dashboard_spec(
            report.report_id, dashboard
        )
        assert populated is not None

        # Check charts were populated
        chart_section = next(
            s for s in populated.sections if s.section_type == ReportSectionType.CHART
        )
        assert len(chart_section.charts) > 0
        assert chart_section.charts[0].title  # Should have a title

        # Check KPIs were populated
        kpi_section = next(
            s for s in populated.sections if s.section_type == ReportSectionType.KEY_METRICS
        )
        assert len(kpi_section.kpis) > 0


# ── Orchestrator Backward Compatibility ───────────────


class TestOrchestratorCompat:
    """Test that AutoEngineOrchestrator still works as a thin wrapper."""

    def test_orchestrator_generate(self, sales_df):
        from services.auto.orchestrator import AutoEngineOrchestrator

        orch = AutoEngineOrchestrator()
        result = orch.generate(sales_df, dataset_name="sales", industry="retail")
        assert "dashboard" in result
        assert "presentation" in result
        assert "understanding" in result

    def test_orchestrator_explain_chart(self, sales_df):
        from services.auto.orchestrator import AutoEngineOrchestrator

        orch = AutoEngineOrchestrator()
        result = orch.generate(sales_df, industry="retail")
        chart = result["charts"][0]
        explanation = orch.explain_chart(chart)
        assert isinstance(explanation, str)
        assert len(explanation) > 10
