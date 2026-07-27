# Enterprise Dashboard Intelligence Engine

## Overview

The Dashboard Intelligence Engine dynamically generates dashboards from semantic analysis, metadata, industry knowledge, and AI recommendations — replacing hardcoded sector dashboards with a fully metadata-driven pipeline.

## Architecture

```
Dataset → Semantic Layer → KPI Intelligence Engine → Chart Recommendation Engine
    → Dashboard Layout Engine → Global Filter Engine → Interactive Dashboard
    → Drilldown Engine → AI Dashboard Assistant → Export
```

## Components

### 1. Dashboard Metadata Model (`services/dashboard_engine.py`)

The persistable schema for all dashboards:

- **`DashboardMetadata`** — Complete dashboard definition with KPIs, charts, filters, layout, drilldowns, permissions
- **`DashboardEngine`** — CRUD operations, customization, sharing, access control
- **`KPIDefinition`** — KPI with formula, source columns, confidence, thresholds
- **`ChartDefinition`** — Chart with data bindings, confidence, reasoning, drilldown target
- **`FilterDefinition`** — Global filter with type, column, cascading support
- **`DrilldownLevel`** — Hierarchical navigation level
- **`DashboardLayout`** — Section-based responsive layout
- **`DashboardPermissions`** — RBAC with visibility, roles, per-user permissions

### 2. KPI Intelligence Engine (`services/kpi_intelligence.py`)

Auto-detects KPIs from data:

- **Universal KPIs** — Total records, data quality score
- **Industry-specific KPIs** — Pre-defined templates for 13 industries with formulas
- **Data-driven KPIs** — Numeric column detection (sum, average)
- **Registry KPIs** — From `KPIRegistry` with semantic entity mapping
- **Confidence scoring** — Based on semantic mapping availability

### 3. Chart Recommendation Engine (`services/chart_recommender.py`)

Recommends chart types based on data characteristics:

- **Time series** → Line chart
- **Category comparison** → Bar chart (or horizontal bar for high cardinality)
- **Composition** → Donut chart (2-10 categories)
- **Distribution** → Histogram
- **Correlation** → Scatter plot
- **Geographic** → Geo map
- **Cross-tabulation** → Heatmap
- **Ranking** → Leaderboard

Each recommendation includes confidence score and reasoning.

### 4. Dashboard Layout Engine (`services/dashboard_layout.py`)

Generates responsive layouts:

- **Standard** — Filters, KPIs, primary charts, supporting charts, AI insights, detail table
- **Compact** — Fewer charts, focused on key metrics
- **Mobile** — Single-column layout
- **Executive** — KPI-first, minimal charts

### 5. Global Filter Engine (`services/filter_engine.py`)

Cross-chart filtering:

- **Filter types** — Date range, single select, multi select, search, numeric range
- **Auto-detection** — From semantic mappings and data characteristics
- **Cascading filters** — Dependent filter options update based on parent selections
- **Affected chart tracking** — Identifies which charts need refresh on filter change

### 6. Drilldown Engine (`services/drilldown_engine.py`)

Hierarchical navigation:

- **Levels** — Summary → Chart → Grouped Detail → Record Details
- **Breadcrumbs** — Navigation trail
- **Pagination** — Server-side pagination for detail tables
- **Filter context** — Drilldown filters propagate to detail views

### 7. AI Dashboard Assistant (`services/dashboard_assistant.py`)

Natural language to dashboard actions:

- **"Show revenue by region"** → Create chart
- **"Replace this chart with a heatmap"** → Replace chart
- **"Highlight the top 5 products"** → Add ranking filter
- **"Compare this month with last month"** → Create comparison chart
- **"Export this dashboard as PDF"** → Export action
- **"Make this chart bigger"** → Resize widget

Intent detection via regex patterns with confidence scoring.

### 8. Dashboard Export (`services/dashboard_export.py`)

Multi-format export:

- **PDF** — Branded report with KPIs, charts, filters, AI insights, data preview
- **Excel** — Multi-sheet (KPIs, Charts, Filters, AI Insights, Data, Metadata)
- **CSV** — Flat data export with metadata header
- **PNG** — Metadata stub (frontend chart capture required)
- **Print** — Print-friendly HTML with CSS styling

### 9. Performance Layer (`services/dashboard_performance.py`)

Optimizations:

- **KPI caching** — TTL-based cache keyed by dataset hash
- **Aggregation caching** — Grouped aggregation results cached
- **Server-side pagination** — For detail tables and large datasets
- **Lazy KPI loading** — Only compute requested KPIs
- **Cache management** — Clear by dataset or all

### 10. Access Control

Integrated in `DashboardEngine`:

- **Visibility** — Private, org, public
- **Per-user permissions** — View, edit, share, export, admin
- **Role-based access** — Allowed roles list
- **Owner privileges** — Full access for dashboard owner

## API Endpoints

All endpoints are prefixed with `/dashboard-engine`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate dashboard from dataset |
| GET | `/{id}` | Get dashboard metadata |
| GET | `` | List dashboards (filter by dataset_id or org_id) |
| PUT | `/{id}` | Update dashboard |
| DELETE | `/{id}` | Delete dashboard |
| POST | `/{id}/widget` | Add widget |
| DELETE | `/{id}/widget/{wid}` | Remove widget |
| PUT | `/{id}/widget/{wid}/resize` | Resize widget |
| PUT | `/{id}/reorder` | Reorder widgets |
| POST | `/{id}/share` | Share dashboard |
| POST | `/{id}/save-custom` | Save custom layout |
| POST | `/{id}/reset` | Reset to recommended |
| GET | `/{id}/kpi-values` | Get computed KPI values |
| POST | `/{id}/filters` | Apply filters |
| POST | `/{id}/drilldown` | Get drilldown data |
| POST | `/{id}/assistant` | Parse NL query |
| POST | `/{id}/export` | Export dashboard |
| GET | `/{id}/permissions` | Check permissions |

## Usage Examples

### Generate a Dashboard

```python
from services.dashboard_engine_routes import register_dataset
import pandas as pd

# Register dataset
df = pd.read_csv("healthcare_data.csv")
register_dataset("ds-001", df)

# Call API
POST /dashboard-engine/generate
{
    "dataset_id": "ds-001",
    "org_id": "org-1",
    "industry": "healthcare",
    "semantic_mappings": {
        "patient_id": "patient",
        "billing_amount": "billing",
        "ward": "ward"
    },
    "title": "Hospital Performance Dashboard",
    "created_by": "user-1"
}
```

### Use the AI Assistant

```python
POST /dashboard-engine/{id}/assistant
{
    "query": "Show billing by ward"
}

# Response
{
    "success": true,
    "data": {
        "action": {
            "action_type": "create_chart",
            "parameters": {
                "metric": "billing",
                "dimension": "ward",
                "chart_type": "bar_chart"
            },
            "confidence": 0.85
        },
        "suggestions": [
            "Show billing by diagnosis",
            "Highlight the top 5 wards",
            "Compare this month with last month"
        ]
    }
}
```

### Export a Dashboard

```python
POST /dashboard-engine/{id}/export
{
    "fmt": "pdf",
    "include_data": true
}
# Returns PDF file download
```

## Testing

```bash
python -m pytest tests/test_dashboard_engine.py -v
```

73 tests covering all engines, CRUD, customization, sharing, exports, and performance.

## Files

| File | Purpose |
|------|---------|
| `services/dashboard_engine.py` | Metadata model + CRUD engine |
| `services/kpi_intelligence.py` | KPI detection and generation |
| `services/chart_recommender.py` | Chart type recommendation |
| `services/dashboard_layout.py` | Layout generation |
| `services/filter_engine.py` | Global filter management |
| `services/drilldown_engine.py` | Drilldown navigation |
| `services/dashboard_assistant.py` | NL to dashboard actions |
| `services/dashboard_export.py` | Multi-format export |
| `services/dashboard_performance.py` | Caching and pagination |
| `services/dashboard_engine_routes.py` | FastAPI routes |
| `tests/test_dashboard_engine.py` | Test suite |
| `docs/dashboard-engine-gap-analysis.md` | Gap analysis |
