# Unified Visualization Engine — Audit & Implementation Report

## Schema Version: 1.0

## Executive Summary

The project had **five separate chart-selection engines** with overlapping
functionality but inconsistent outputs. This work unifies them into a single
canonical **Visualization Intelligence Engine** (`services/auto/engine.py`)
that serves as the authoritative entry point for all visualization needs.

All 96 tests pass (64 existing + 32 new).

---

## Phase 1: Architecture Audit

### Engines Found

| # | Engine | File | Status | Used By |
|---|--------|------|--------|---------|
| 1 | `IntelligentChartSelectionEngine` | `services/auto/chart_selection_engine.py` | **CANONICAL** | `AutoEngineOrchestrator` → dashboard + presentation |
| 2 | `ChartRecommendationEngine` | `services/chart_recommender.py` | **DEPRECATED** | `services/dashboard_engine_routes.py` |
| 3 | `ChartSelector` | `intelligence/chart_selector.py` | **DEPRECATED** | `intelligence/__init__.py` (exported, no active callers) |
| 4 | `VisualizationEngine` | `studios/visualization_service.py` | **DEPRECATED** | `studios/routes.py` |
| 5 | `DashboardRecommendationEngine` | `services/dashboard_recommender.py` | **LEGACY** | `services/dataset_workflow.py` (parallel to auto orchestrator) |

### Key Issues Identified

- **Two separate `ChartSpecification` classes**: `services/auto/chart_specification.py` (canonical) vs `intelligence/chart_selector.py` (duplicate)
- **Two separate column analyzers**: `services/auto/analysis_engine.py` vs `intelligence/column_analyzer.py`
- **Report engine had its own `ChartDefinition`** — did not consume canonical specs
- **No chart validation/fallback** — broken charts would crash the dashboard
- **Missing chart types**: area, box plot, treemap
- **Deduplication too aggressive** — removed different chart types sharing the same axes

---

## Phases 2-19: Implementation

### New Files Created

1. **`services/auto/engine.py`** — `VisualizationIntelligenceEngine` facade
   - Single canonical entry point for all visualization
   - Wraps the existing auto pipeline + adds validation
   - `generate()` → dashboard + presentation + charts + understanding
   - `generate_chart_specs()` → standalone chart specs for reports
   - `validate_chart()` → single chart validation
   - `explain_chart()` → "Why this chart?" explanation
   - Schema versioning (`VISUALIZATION_SCHEMA_VERSION = "1.0"`)

2. **`services/auto/validators.py`** — `ChartValidator` + `ValidationResult`
   - Validates chart specs against source DataFrame
   - Checks: empty data, missing columns, NaN values, chart-type constraints
   - Pie/donut max 8 categories, bar max 25, scatter min 5 points
   - `validate_and_fallback()` — skips invalid charts, keeps dashboard alive

3. **`tests/test_visualization_engine.py`** — 32 new tests
   - Full pipeline, chart types, validation, edge cases, report integration, orchestrator compat

### Files Modified

1. **`services/auto/chart_selection_engine.py`**
   - Added `_make_area_chart()` — volume/trend emphasis over time
   - Added `_make_box_plot()` — distribution + group comparison with outliers
   - Added `_make_treemap()` — hierarchical part-to-whole for many categories (8-100)
   - Added scoring for new chart types (area: 13, box: 9, treemap: 10)
   - Fixed deduplication: different chart types with same axes are no longer duplicates
   - Added new chart types to diversity priority list

2. **`services/auto/orchestrator.py`**
   - Now delegates to `VisualizationIntelligenceEngine` (thin wrapper)
   - Preserves backward-compatible API (`generate`, `explain_chart`, sub-engines)

3. **`services/auto/__init__.py`**
   - Exports `VisualizationIntelligenceEngine`, `ChartValidator`, `ValidationResult`

4. **`services/report_engine.py`**
   - `ChartDefinition.from_canonical_spec()` — converts canonical `ChartSpecification` to report format
   - `ReportCompositionService.populate_from_dashboard_spec()` — populates report sections from canonical dashboard

5. **Deprecated legacy engines** (deprecation notices added):
   - `services/chart_recommender.py`
   - `intelligence/chart_selector.py`
   - `studios/visualization_service.py`

6. **`tests/test_auto_engine.py`**
   - Updated `test_no_duplicate_axes` to allow different chart types with same axes

---

## Phases 23-24: Security & Frontend

### Security (Org Isolation)
- `organization_id` is set server-side from the authenticated user in `dataset_workflow.py`
- The visualization engine itself does not query the database — org isolation is enforced at the workflow/API layer
- Cache re-attribution bug already fixed (cross-tenant data attribution)

### Frontend Audit
- `DashboardPreview.tsx` already renders auto-generated dashboards with:
  - No manual chart configuration
  - "Why this chart?" explanations with importance/confidence scores
  - Responsive grid layout (`grid-cols-1 lg:grid-cols-2`, `md:grid-cols-3 lg:grid-cols-6`)
  - KPI cards, primary/supporting chart sections, AI insights, recommendations
  - PPTX download button
  - Loading/error states
  - Legacy fallback view

---

## Phases 26-28: Test Results

```
96 passed, 157 warnings in 7.07s
```

- 64 existing auto engine tests — all pass
- 32 new visualization engine tests — all pass
- Coverage: full pipeline, chart types, validation, edge cases, report integration, backward compat

---

## Architecture Map (After)

```
DataFrame + metadata
     │
     ▼
VisualizationIntelligenceEngine (services/auto/engine.py)
     │
     ├── AutomaticAnalysisEngine → DatasetUnderstanding
     │
     ├── IntelligentChartSelectionEngine → list[ChartSpecification]
     │     ├── line, bar, pie, donut, scatter, histogram, heatmap
     │     ├── NEW: area_chart, box_plot, treemap
     │     ├── Scoring (7 components, 0-100)
     │     ├── Deduplication (type-aware)
     │     └── Diversity enforcement
     │
     ├── ChartValidator → validated list[ChartSpecification]
     │     ├── Column existence, NaN, empty data checks
     │     ├── Chart-type constraints (pie max 8, bar max 25, etc.)
     │     └── Fallback: skip invalid, keep dashboard alive
     │
     ├── AutomaticKPIEngine → list[KPISpecification]
     ├── AutomaticInsightEngine → list[InsightSpecification]
     ├── AutomaticFilterEngine → list[FilterSpecification]
     │
     ├── IntelligentDashboardLayoutEngine → DashboardSpecification
     │     └── Responsive: 12/8/4 column grids
     │
     └── PresentationLayoutEngine → PresentationSpecification
           └── SAME ChartSpecification objects as dashboard

ReportCompositionService.populate_from_dashboard_spec()
     └── Converts canonical specs → report ChartDefinitions
```

---

## Remaining Work

- **Phase 25 (safe removal)**: Legacy engines are deprecated but not yet removed. Removal should happen after confirming no runtime callers remain.
- **Phase 29-30**: This report serves as the final audit document.
