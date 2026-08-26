"""Tests for the Enterprise Dashboard Intelligence Engine.

Tests cover:
  - Dashboard metadata model (CRUD, customization, sharing)
  - KPI Intelligence Engine (detection, formulas, confidence)
  - Chart Recommendation Engine (type selection, data-driven)
  - Dashboard Layout Engine (templates, responsive)
  - Global Filter Engine (detection, application, cascading)
  - Drilldown Engine (navigation, pagination)
  - AI Dashboard Assistant (intent parsing, action execution)
  - Dashboard Export (PDF, Excel, CSV, print)
  - Performance layer (caching, pagination)
  - Access control (permissions, RBAC)
"""

from __future__ import annotations

import pandas as pd
import pytest

from services.chart_recommender import ChartRecommendationEngine
from services.dashboard_assistant import ActionType, AIDashboardAssistant
from services.dashboard_engine import (
    ChartDefinition,
    DashboardEngine,
    DashboardMetadata,
    DrilldownLevel,
    KPIDefinition,
    PermissionLevel,
)
from services.dashboard_export import DashboardExportService
from services.dashboard_layout import DashboardLayoutEngine
from services.dashboard_performance import DashboardPerformanceLayer
from services.drilldown_engine import DrilldownEngine
from services.filter_engine import GlobalFilterEngine
from services.kpi_intelligence import KPIIntelligenceEngine

# â”€â”€ Fixtures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.fixture
def healthcare_df():
    return pd.DataFrame(
        {
            "patient_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "patient_name": [
                "John",
                "Jane",
                "Bob",
                "Alice",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
                "Grace",
                "Henry",
            ],
            "age": [45, 32, 67, 28, 55, 41, 60, 35, 50, 72],
            "diagnosis": [
                "E11.9",
                "J45.909",
                "I10",
                "E11.9",
                "M54.5",
                "I10",
                "E11.9",
                "J45.909",
                "M54.5",
                "I10",
            ],
            "doctor": [
                "Dr. Smith",
                "Dr. Jones",
                "Dr. Smith",
                "Dr. Lee",
                "Dr. Jones",
                "Dr. Smith",
                "Dr. Lee",
                "Dr. Jones",
                "Dr. Smith",
                "Dr. Lee",
            ],
            "ward": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
            "admission_date": pd.to_datetime(
                [
                    "2024-01-15",
                    "2024-02-20",
                    "2024-03-10",
                    "2024-04-05",
                    "2024-05-12",
                    "2024-06-01",
                    "2024-07-15",
                    "2024-08-20",
                    "2024-09-10",
                    "2024-10-05",
                ]
            ),
            "billing_amount": [
                1500.00,
                3200.50,
                8900.00,
                750.00,
                4200.00,
                2100.00,
                5500.00,
                1800.00,
                3200.00,
                7800.00,
            ],
        }
    )


@pytest.fixture
def retail_df():
    return pd.DataFrame(
        {
            "order_id": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "product_name": [
                "Widget A",
                "Widget B",
                "Gadget C",
                "Gadget D",
                "Tool E",
                "Widget A",
                "Gadget C",
                "Tool E",
                "Widget B",
                "Gadget D",
            ],
            "category": [
                "Electronics",
                "Electronics",
                "Tools",
                "Tools",
                "Tools",
                "Electronics",
                "Tools",
                "Tools",
                "Electronics",
                "Tools",
            ],
            "region": [
                "North",
                "South",
                "North",
                "East",
                "West",
                "South",
                "North",
                "West",
                "South",
                "East",
            ],
            "sales": [
                299.90,
                499.90,
                155.00,
                250.00,
                399.90,
                299.90,
                155.00,
                399.90,
                499.90,
                250.00,
            ],
            "profit": [89.90, 149.90, 45.00, 75.00, 119.90, 89.90, 45.00, 119.90, 149.90, 75.00],
            "order_date": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-01-15",
                    "2024-02-01",
                    "2024-02-15",
                    "2024-03-01",
                    "2024-03-15",
                    "2024-04-01",
                    "2024-04-15",
                    "2024-05-01",
                    "2024-05-15",
                ]
            ),
        }
    )


@pytest.fixture
def healthcare_mappings():
    return {
        "patient_id": "patient",
        "patient_name": "patient",
        "diagnosis": "diagnosis",
        "doctor": "doctor",
        "ward": "ward",
        "admission_date": "date",
        "billing_amount": "billing",
    }


@pytest.fixture
def retail_mappings():
    return {
        "order_id": "order",
        "product_name": "product",
        "category": "category",
        "region": "region",
        "sales": "revenue",
        "profit": "revenue",
        "order_date": "date",
    }


@pytest.fixture
def engine():
    return DashboardEngine()


@pytest.fixture
def kpi_engine():
    return KPIIntelligenceEngine()


@pytest.fixture
def chart_engine():
    return ChartRecommendationEngine()


@pytest.fixture
def layout_engine():
    return DashboardLayoutEngine()


@pytest.fixture
def filter_engine():
    return GlobalFilterEngine()


@pytest.fixture
def drilldown_engine():
    return DrilldownEngine()


@pytest.fixture
def assistant():
    return AIDashboardAssistant()


@pytest.fixture
def export_service():
    return DashboardExportService()


@pytest.fixture
def perf():
    return DashboardPerformanceLayer()


# â”€â”€ Dashboard Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDashboardEngine:
    """Tests for DashboardEngine CRUD and customization."""

    def test_create_and_get(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="test-1",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test Dashboard",
        )
        engine.create(dashboard)
        assert engine.get("test-1") is not None
        assert engine.get("test-1").title == "Test Dashboard"

    def test_delete(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="test-2", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        engine.create(dashboard)
        assert engine.delete("test-2") is True
        assert engine.get("test-2") is None

    def test_list_by_dataset(self, engine):
        for i in range(3):
            engine.create(
                DashboardMetadata(
                    dashboard_id=f"ds-test-{i}",
                    dataset_id="ds-list",
                    org_id="org-1",
                    title=f"Dashboard {i}",
                )
            )
        dashboards = engine.list_by_dataset("ds-list")
        assert len(dashboards) == 3

    def test_add_widget(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="widget-test", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        engine.create(dashboard)
        widget = {
            "chart_type": "bar_chart",
            "title": "Revenue by Region",
            "section": "primary_charts",
            "x_axis": "region",
            "y_axis": "sales",
            "width": 6,
            "height": 300,
        }
        result = engine.add_widget("widget-test", widget)
        assert result is not None
        assert len(result.charts) == 1

    def test_remove_widget(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="remove-test",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test",
            charts=[
                ChartDefinition(
                    id="chart-1",
                    chart_type="bar_chart",
                    title="Test Chart",
                    section="primary_charts",
                )
            ],
        )
        engine.create(dashboard)
        result = engine.remove_widget("remove-test", "chart-1")
        assert result is not None
        assert len(result.charts) == 0

    def test_resize_widget(self, engine):
        chart = ChartDefinition(
            id="chart-1",
            chart_type="bar_chart",
            title="Test",
            section="primary_charts",
            width=6,
            height=300,
        )
        dashboard = DashboardMetadata(
            dashboard_id="resize-test",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test",
            charts=[chart],
        )
        engine.create(dashboard)
        result = engine.resize_widget("resize-test", "chart-1", 12, 400)
        assert result.charts[0].width == 12
        assert result.charts[0].height == 400

    def test_reorder_widgets(self, engine):
        charts = [
            ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary", order=0),
            ChartDefinition(id="c2", chart_type="line", title="C2", section="primary", order=1),
            ChartDefinition(id="c3", chart_type="pie", title="C3", section="primary", order=2),
        ]
        dashboard = DashboardMetadata(
            dashboard_id="reorder-test",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test",
            charts=charts,
        )
        engine.create(dashboard)
        result = engine.reorder_widgets("reorder-test", "primary", ["c3", "c1", "c2"])
        assert result.layout.sections["primary"] == ["c3", "c1", "c2"]

    def test_share_dashboard(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="share-test", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        engine.create(dashboard)
        result = engine.share("share-test", ["user1", "user2"], PermissionLevel.VIEW.value)
        assert "user1" in result.permissions.allowed_users
        assert "user2" in result.permissions.allowed_users

    def test_save_custom_layout(self, engine):
        parent = DashboardMetadata(
            dashboard_id="parent-1",
            dataset_id="ds-1",
            org_id="org-1",
            title="Parent",
            charts=[
                ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary", width=6)
            ],
        )
        engine.create(parent)
        custom = engine.save_custom_layout(
            "parent-1", "user1", "My Custom", chart_updates=[{"id": "c1", "width": 12}]
        )
        assert custom.is_custom is True
        assert custom.parent_dashboard_id == "parent-1"
        assert custom.charts[0].width == 12

    def test_reset_to_recommended(self, engine):
        parent = DashboardMetadata(
            dashboard_id="parent-2",
            dataset_id="ds-1",
            org_id="org-1",
            title="Parent",
            charts=[
                ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary", width=6)
            ],
        )
        engine.create(parent)
        custom = engine.save_custom_layout(
            "parent-2", "user1", "Custom", chart_updates=[{"id": "c1", "width": 12}]
        )
        assert custom.charts[0].width == 12
        reset = engine.reset_to_recommended(custom.dashboard_id)
        assert reset.charts[0].width == 6

    def test_can_access_owner(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="access-test", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        dashboard.permissions.owner_id = "owner1"
        engine.create(dashboard)
        assert engine.can_access("access-test", "owner1", []) is True

    def test_can_access_shared(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="access-test2", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        engine.create(dashboard)
        engine.share("access-test2", ["user1"])
        assert engine.can_access("access-test2", "user1", []) is True

    def test_can_access_denied(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="access-denied", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        engine.create(dashboard)
        assert engine.can_access("access-denied", "stranger", []) is False

    def test_can_edit(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="edit-test", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        dashboard.permissions.owner_id = "owner1"
        engine.create(dashboard)
        assert engine.can_edit("edit-test", "owner1") is True
        assert engine.can_edit("edit-test", "user2") is False

    def test_can_export(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="export-test", dataset_id="ds-1", org_id="org-1", title="Test"
        )
        dashboard.permissions.owner_id = "owner1"
        engine.create(dashboard)
        assert engine.can_export("export-test", "owner1") is True

    def test_serialization(self, engine):
        dashboard = DashboardMetadata(
            dashboard_id="ser-test",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test",
            kpis=[
                KPIDefinition(key="k1", label="K1", entity="e", metric="sum", category="financial")
            ],
            charts=[ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary")],
        )
        engine.create(dashboard)
        data = dashboard.to_dict()
        restored = DashboardMetadata.from_dict(data)
        assert restored.title == "Test"
        assert len(restored.kpis) == 1
        assert len(restored.charts) == 1


# â”€â”€ KPI Intelligence Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestKPIIntelligenceEngine:
    """Tests for KPI detection and generation."""

    def test_detect_universal_kpis(self, kpi_engine, healthcare_df):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare")
        keys = [k.key for k in kpis]
        assert "total_records" in keys
        assert "data_quality" in keys

    def test_detect_healthcare_kpis(self, kpi_engine, healthcare_df, healthcare_mappings):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare", healthcare_mappings)
        keys = [k.key for k in kpis]
        assert "total_admissions" in keys or "total_billing" in keys

    def test_kpis_have_formulas(self, kpi_engine, healthcare_df, healthcare_mappings):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare", healthcare_mappings)
        for kpi in kpis:
            if kpi.key != "total_records" and kpi.key != "data_quality":
                assert kpi.formula != ""

    def test_kpis_have_confidence(self, kpi_engine, healthcare_df, healthcare_mappings):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare", healthcare_mappings)
        for kpi in kpis:
            assert 0 <= kpi.confidence <= 1.0

    def test_kpis_have_source_columns(self, kpi_engine, healthcare_df, healthcare_mappings):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare", healthcare_mappings)
        # At least some KPIs should have source columns
        with_sources = [k for k in kpis if len(k.source_columns) > 0]
        assert len(with_sources) > 0

    def test_data_driven_kpis(self, kpi_engine, healthcare_df):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare")
        # Should detect numeric columns as potential KPIs
        data_driven = [k for k in kpis if k.key.startswith("sum_") or k.key.startswith("avg_")]
        assert len(data_driven) > 0

    def test_retail_kpis(self, kpi_engine, retail_df, retail_mappings):
        kpis = kpi_engine.detect_kpis(retail_df, "retail", retail_mappings)
        keys = [k.key for k in kpis]
        assert "total_revenue" in keys
        assert "total_orders" in keys

    def test_no_duplicate_kpis(self, kpi_engine, healthcare_df, healthcare_mappings):
        kpis = kpi_engine.detect_kpis(healthcare_df, "healthcare", healthcare_mappings)
        keys = [k.key for k in kpis]
        assert len(keys) == len(set(keys))


# â”€â”€ Chart Recommendation Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestChartRecommendationEngine:
    """Tests for chart recommendation."""

    def test_recommend_charts_returns_list(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(healthcare_df, "healthcare", healthcare_mappings)
        assert isinstance(charts, list)
        assert len(charts) > 0

    def test_charts_have_confidence(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(healthcare_df, "healthcare", healthcare_mappings)
        for chart in charts:
            assert 0 <= chart.confidence <= 1.0

    def test_charts_have_reasoning(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(healthcare_df, "healthcare", healthcare_mappings)
        for chart in charts:
            assert chart.reasoning != ""

    def test_time_series_chart(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(healthcare_df, "healthcare", healthcare_mappings)
        line_charts = [c for c in charts if c.chart_type == "line_chart"]
        assert len(line_charts) > 0

    def test_bar_chart_for_categories(self, chart_engine, retail_df, retail_mappings):
        charts = chart_engine.recommend_charts(retail_df, "retail", retail_mappings)
        bar_charts = [c for c in charts if c.chart_type in ("bar_chart", "horizontal_bar")]
        assert len(bar_charts) > 0

    def test_max_charts_limit(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(
            healthcare_df, "healthcare", healthcare_mappings, max_charts=5
        )
        assert len(charts) <= 5

    def test_replacement_recommendation(self, chart_engine):
        result = chart_engine.recommend_replacement(
            "bar_chart", ["horizontal_bar", "pie_chart", "line_chart"]
        )
        assert result is not None
        assert result in ("horizontal_bar", "pie_chart")

    def test_charts_have_ids(self, chart_engine, healthcare_df, healthcare_mappings):
        charts = chart_engine.recommend_charts(healthcare_df, "healthcare", healthcare_mappings)
        for chart in charts:
            assert chart.id != ""


# â”€â”€ Layout Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDashboardLayoutEngine:
    """Tests for layout generation."""

    def test_standard_layout(self, layout_engine):
        kpis = [
            KPIDefinition(key=f"k{i}", label=f"K{i}", entity="e", metric="sum", category="op")
            for i in range(1)
        ]
        charts = [
            ChartDefinition(id=f"c{i}", chart_type="bar", title=f"C{i}", section="primary_charts")
            for i in range(1)
        ]
        layout = layout_engine.generate_layout(kpis, charts)
        assert layout.grid_columns == 12
        assert "filter_bar" in layout.sections
        assert "kpi_row" in layout.sections

    def test_compact_layout(self, layout_engine):
        kpis = [
            KPIDefinition(key=f"k{i}", label=f"K{i}", entity="e", metric="sum", category="op")
            for i in range(8)
        ]
        charts = [
            ChartDefinition(id=f"c{i}", chart_type="bar", title=f"C{i}", section="primary_charts")
            for i in range(10)
        ]
        layout = layout_engine.generate_compact_layout(kpis, charts)
        assert len(layout.sections["kpi_row"]) <= 4

    def test_mobile_layout(self, layout_engine):
        kpis = [KPIDefinition(key="k1", label="K1", entity="e", metric="sum", category="op")]
        charts = [ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary_charts")]
        layout = layout_engine.generate_mobile_layout(kpis, charts)
        assert layout.responsive is True

    def test_executive_layout(self, layout_engine):
        kpis = [
            KPIDefinition(key=f"k{i}", label=f"K{i}", entity="e", metric="sum", category="op")
            for i in range(8)
        ]
        charts = [
            ChartDefinition(id=f"c{i}", chart_type="bar", title=f"C{i}", section="primary_charts")
            for i in range(10)
        ]
        layout = layout_engine.generate_executive_layout(kpis, charts)
        assert layout.show_filters is False

    def test_layout_templates_list(self, layout_engine):
        templates = layout_engine.get_layout_templates()
        assert len(templates) == 4
        keys = [t["key"] for t in templates]
        assert "standard" in keys
        assert "compact" in keys

    def test_apply_template(self, layout_engine):
        kpis = [KPIDefinition(key="k1", label="K1", entity="e", metric="sum", category="op")]
        charts = [ChartDefinition(id="c1", chart_type="bar", title="C1", section="primary_charts")]
        layout = layout_engine.apply_template("compact", kpis, charts)
        assert layout is not None


# â”€â”€ Filter Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestGlobalFilterEngine:
    """Tests for filter detection and application."""

    def test_detect_filters(self, filter_engine, healthcare_df, healthcare_mappings):
        filters = filter_engine.detect_filters(healthcare_df, healthcare_mappings)
        assert len(filters) > 0

    def test_detect_date_filter(self, filter_engine, healthcare_df, healthcare_mappings):
        filters = filter_engine.detect_filters(healthcare_df, healthcare_mappings)
        date_filters = [f for f in filters if f.filter_type == "date_range"]
        assert len(date_filters) > 0

    def test_detect_categorical_filter(self, filter_engine, healthcare_df, healthcare_mappings):
        filters = filter_engine.detect_filters(healthcare_df, healthcare_mappings)
        cat_filters = [f for f in filters if f.filter_type in ("single_select", "multi_select")]
        assert len(cat_filters) > 0

    def test_apply_single_select(self, filter_engine, healthcare_df, healthcare_mappings):
        filters = filter_engine.detect_filters(healthcare_df, healthcare_mappings)
        ward_filter = next((f for f in filters if f.column == "ward"), None)
        assert ward_filter is not None
        filtered = filter_engine.apply_filters(healthcare_df, {ward_filter.id: "A"}, filters)
        assert (filtered["ward"] == "A").all()

    def test_apply_no_filters(self, filter_engine, healthcare_df):
        filters = filter_engine.detect_filters(healthcare_df)
        filtered = filter_engine.apply_filters(healthcare_df, {}, filters)
        assert len(filtered) == len(healthcare_df)

    def test_get_affected_charts(self, filter_engine, healthcare_df, healthcare_mappings):
        filters = filter_engine.detect_filters(healthcare_df, healthcare_mappings)
        from services.dashboard_engine import ChartDefinition

        charts = [
            ChartDefinition(
                id="c1",
                chart_type="bar",
                title="C1",
                section="primary",
                source_columns=["ward", "billing_amount"],
            )
        ]
        if filters:
            affected = filter_engine.get_affected_charts(filters[0].id, filters, charts)
            # Should be affected if filter column is in chart source columns
            assert isinstance(affected, list)


# â”€â”€ Drilldown Engine Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDrilldownEngine:
    """Tests for drilldown navigation."""

    def test_generate_drilldowns(self, drilldown_engine, healthcare_df, healthcare_mappings):
        from services.dashboard_engine import ChartDefinition, KPIDefinition

        kpis = [KPIDefinition(key="k1", label="K1", entity="e", metric="sum", category="op")]
        charts = [
            ChartDefinition(
                id="c1",
                chart_type="line",
                title="Billing Over Time",
                section="primary_charts",
                x_axis="admission_date",
                y_axis="billing_amount",
            )
        ]
        levels = drilldown_engine.generate_drilldowns(
            healthcare_df, kpis, charts, healthcare_mappings
        )
        assert len(levels) >= 2

    def test_drill_down(self, drilldown_engine):
        levels = [
            DrilldownLevel(level=0, label="Summary"),
            DrilldownLevel(level=1, label="Chart"),
            DrilldownLevel(level=2, label="Detail"),
        ]
        path = drilldown_engine.create_path(levels)
        path = drilldown_engine.drill_down(path, 2)
        assert path.current_level == 2
        assert len(path.breadcrumbs) == 3

    def test_drill_up(self, drilldown_engine):
        levels = [
            DrilldownLevel(level=0, label="Summary"),
            DrilldownLevel(level=1, label="Chart"),
            DrilldownLevel(level=2, label="Detail"),
        ]
        path = drilldown_engine.create_path(levels)
        path = drilldown_engine.drill_down(path, 2)
        path = drilldown_engine.drill_up(path)
        assert path.current_level == 1

    def test_get_detail_data_pagination(self, drilldown_engine, healthcare_df):
        levels = [
            DrilldownLevel(level=0, label="Summary", table_columns=list(healthcare_df.columns))
        ]
        path = drilldown_engine.create_path(levels)
        result = drilldown_engine.get_detail_data(healthcare_df, path, page=1, page_size=5)
        assert result["total"] == 10
        assert len(result["data"]) == 5
        assert result["pages"] == 2


# â”€â”€ AI Dashboard Assistant Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestAIDashboardAssistant:
    """Tests for NL to dashboard action parsing."""

    def test_parse_show_by(self, assistant):
        action = assistant.parse_query("Show revenue by region")
        assert action.action_type == ActionType.CREATE_CHART.value
        assert action.parameters.get("metric") == "revenue"
        assert action.parameters.get("dimension") == "region"

    def test_parse_replace_chart(self, assistant):
        action = assistant.parse_query("Replace this chart with a heatmap")
        assert action.action_type == ActionType.REPLACE_CHART.value
        assert action.parameters.get("new_type") == "heatmap"

    def test_parse_highlight_top(self, assistant):
        action = assistant.parse_query("Highlight the top 5 products")
        assert action.action_type == ActionType.HIGHLIGHT_TOP.value
        assert action.parameters.get("n") == 5
        assert action.parameters.get("entity") == "products"

    def test_parse_compare_periods(self, assistant):
        action = assistant.parse_query("Compare this month with last month")
        assert action.action_type == ActionType.COMPARE_PERIODS.value

    def test_parse_filter(self, assistant):
        action = assistant.parse_query("Filter by region")
        assert action.action_type == ActionType.ADD_FILTER.value

    def test_parse_remove_chart(self, assistant):
        action = assistant.parse_query("Remove this chart")
        assert action.action_type == ActionType.REMOVE_CHART.value

    def test_parse_resize(self, assistant):
        action = assistant.parse_query("Make this chart bigger")
        assert action.action_type == ActionType.RESIZE_CHART.value
        assert action.parameters.get("width") == 12

    def test_parse_export(self, assistant):
        action = assistant.parse_query("Export this dashboard as PDF")
        assert action.action_type == ActionType.EXPORT.value
        assert action.parameters.get("format") == "pdf"

    def test_parse_unknown(self, assistant):
        action = assistant.parse_query("What is the meaning of life?")
        assert action.action_type == ActionType.UNKNOWN.value

    def test_execute_create_chart(self, assistant):
        action = assistant.parse_query("Show billing by ward")
        result = assistant.execute_action(
            action, {"charts": []}, ["billing_amount", "ward", "patient_id"]
        )
        assert result["success"] is True
        assert "create_chart" in result["updates"]

    def test_get_suggestions(self, assistant):
        suggestions = assistant.get_suggestions({"charts": []}, ["sales", "profit", "region"])
        assert len(suggestions) > 0


# â”€â”€ Export Service Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDashboardExportService:
    """Tests for dashboard export."""

    @pytest.fixture
    def sample_dashboard(self):
        return DashboardMetadata(
            dashboard_id="export-test-1",
            dataset_id="ds-1",
            org_id="org-1",
            title="Test Dashboard",
            subtitle="Test subtitle",
            industry="healthcare",
            kpis=[
                KPIDefinition(
                    key="k1",
                    label="Total Billing",
                    entity="billing",
                    metric="sum",
                    category="financial",
                )
            ],
            charts=[
                ChartDefinition(
                    id="c1",
                    chart_type="bar_chart",
                    title="Billing by Ward",
                    section="primary_charts",
                    x_axis="ward",
                    y_axis="billing_amount",
                )
            ],
            ai_insights=["Billing is increasing"],
        )

    def test_export_csv(self, export_service, sample_dashboard, healthcare_df):
        content, filename, content_type = export_service.export(
            sample_dashboard, healthcare_df, fmt="csv"
        )
        assert "csv" in filename
        assert "text/csv" in content_type
        assert len(content) > 0

    def test_export_excel(self, export_service, sample_dashboard, healthcare_df):
        content, filename, content_type = export_service.export(
            sample_dashboard, healthcare_df, fmt="excel"
        )
        assert "xlsx" in filename
        assert len(content) > 0

    def test_export_pdf(self, export_service, sample_dashboard, healthcare_df):
        content, filename, content_type = export_service.export(
            sample_dashboard, healthcare_df, fmt="pdf", kpi_values={"k1": 15000.0}
        )
        assert "pdf" in filename
        assert "application/pdf" in content_type
        assert len(content) > 0

    def test_export_print(self, export_service, sample_dashboard, healthcare_df):
        content, filename, content_type = export_service.export(
            sample_dashboard, healthcare_df, fmt="print"
        )
        assert "html" in filename
        assert "text/html" in content_type
        assert b"<html" in content

    def test_export_unsupported(self, export_service, sample_dashboard):
        with pytest.raises(ValueError):
            export_service.export(sample_dashboard, fmt="docx")


# â”€â”€ Performance Layer Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class TestDashboardPerformanceLayer:
    """Tests for caching and pagination."""

    def test_compute_kpi_caching(self, perf, healthcare_df):
        dataset_hash = perf.compute_dataset_hash(healthcare_df)
        val1 = perf.compute_kpi("test_kpi", healthcare_df, ["billing_amount"], "sum", dataset_hash)
        val2 = perf.compute_kpi("test_kpi", healthcare_df, ["billing_amount"], "sum", dataset_hash)
        assert val1 == val2  # Same value from cache

    def test_aggregation_caching(self, perf, healthcare_df):
        dataset_hash = perf.compute_dataset_hash(healthcare_df)
        result1 = perf.compute_aggregation(
            healthcare_df, "ward", "billing_amount", "sum", dataset_hash
        )
        result2 = perf.compute_aggregation(
            healthcare_df, "ward", "billing_amount", "sum", dataset_hash
        )
        assert len(result1) == len(result2)

    def test_pagination(self, perf, healthcare_df):
        result = perf.paginate(healthcare_df, page=1, page_size=3)
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["total_pages"] == 4
        assert len(result["data"]) == 3
        assert result["pagination"]["has_next"] is True

    def test_pagination_last_page(self, perf, healthcare_df):
        result = perf.paginate(healthcare_df, page=4, page_size=3)
        assert len(result["data"]) == 1  # 10 - 9 = 1
        assert result["pagination"]["has_next"] is False

    def test_cache_stats(self, perf, healthcare_df):
        dataset_hash = perf.compute_dataset_hash(healthcare_df)
        perf.compute_kpi("test", healthcare_df, ["billing_amount"], "sum", dataset_hash)
        stats = perf.get_cache_stats()
        assert stats["kpi_cache_size"] >= 1

    def test_clear_cache(self, perf, healthcare_df):
        dataset_hash = perf.compute_dataset_hash(healthcare_df)
        perf.compute_kpi("test", healthcare_df, ["billing_amount"], "sum", dataset_hash)
        cleared = perf.clear_cache(dataset_hash)
        assert cleared >= 1

    def test_dataset_hash_consistency(self, perf, healthcare_df):
        hash1 = perf.compute_dataset_hash(healthcare_df)
        hash2 = perf.compute_dataset_hash(healthcare_df)
        assert hash1 == hash2

    def test_dataset_hash_different(self, perf, healthcare_df, retail_df):
        hash1 = perf.compute_dataset_hash(healthcare_df)
        hash2 = perf.compute_dataset_hash(retail_df)
        assert hash1 != hash2

    def test_lazy_load_kpis(self, perf, healthcare_df):
        dataset_hash = perf.compute_dataset_hash(healthcare_df)
        kpi_defs = [
            {"key": "k1", "source_columns": ["billing_amount"], "aggregation": "sum"},
            {"key": "k2", "source_columns": ["age"], "aggregation": "avg"},
        ]
        results = perf.lazy_load_kpis(["k1"], healthcare_df, kpi_defs, dataset_hash)
        assert "k1" in results
        assert "k2" not in results  # Only loaded k1
