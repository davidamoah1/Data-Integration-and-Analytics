# Dashboard Engine Gap Analysis — Phase 12.3

## 1. Current State

### 1.1 Streamlit Dashboards

| Component | File | Status |
|-----------|------|--------|
| **Sector Dashboards** | `dashboard/sector_dashboards.py` (1441 lines) | ❌ Hardcoded — separate `render_*_dashboard()` per industry |
| **Semantic Dashboard** | `dashboard/semantic_dashboard.py` (317 lines) | ⚠️ Semi-dynamic — uses DashboardRegistry widgets but rendering is Streamlit-specific |
| **Chart Components** | `dashboard/charts.py` (328 lines) | ❌ Hardcoded to SME columns (`sales`, `profit`, `region`, `category`) |
| **Validation Dashboard** | `dashboard/validation_dashboard.py` | Standalone, not integrated |
| **Dashboard App** | `dashboard/app.py` | Routes between hardcoded sector dashboards |

### 1.2 Semantic Layer (Reusable)

| Component | File | Status |
|-----------|------|--------|
| **DashboardRegistry** | `semantic/dashboard_registry.py` (487 lines) | ✅ Good — widget definitions for 13 industries, but static templates |
| **DashboardGenerator** | `semantic/dashboard_generator.py` (308 lines) | ⚠️ Partial — generates config from semantic mappings, but chart selection is hardcoded per industry |
| **KPIGenerator** | `semantic/kpi_generator.py` (333 lines) | ⚠️ Partial — computes KPIs from semantic mappings, but KPI definitions are static per industry |
| **KPIRegistry** | `semantic/kpi_registry.py` (144 lines) | ✅ Good — per-industry KPI definitions, but no formula/confidence/source columns |
| **ReportRegistry** | `semantic/report_registry.py` (104 lines) | ✅ Good — per-industry report types |
| **IndustryKnowledge** | `semantic/industry_knowledge.py` (946 lines) | ✅ Good — entities, KPIs, rules, alerts, charts per industry |

### 1.3 AI KPI Engine

| Component | File | Status |
|-----------|------|--------|
| **KPIEngine** | `ai/engines/kpi_engine.py` (218 lines) | ⚠️ Hardcoded to `sales` table — SQL queries assume specific schema |

### 1.4 Next.js Frontend

| Component | File | Status |
|-----------|------|--------|
| **Analytics Page** | `frontend/app/(app)/analytics/page.tsx` | ⚠️ Basic — lists dashboards and KPIs, no dynamic rendering |
| **Dashboard Page** | `frontend/app/(app)/dashboard/page.tsx` | ⚠️ Basic — KPI cards and recent datasets |
| **Dataset Workflow** | `frontend/app/(app)/datasets/workflow/page.tsx` | ✅ Good — Phase 12.2 workflow with timeline, profile, quality, insights, dashboard preview |
| **DashboardPreview** | `frontend/features/dataset-workflow/DashboardPreview.tsx` | ⚠️ Shows recommendations only, no interactive dashboard |

### 1.5 Export

| Component | File | Status |
|-----------|------|--------|
| **ReportExportService** | `services/report_export_service.py` (171 lines) | ✅ CSV, Excel, PDF — for AI reports only |
| **ValidationReportGenerator** | `validation/report_generator.py` (273 lines) | ✅ CSV, Excel, PDF — for validation reports only |
| **Dashboard Export** | — | ❌ Missing — no dashboard export functionality |

### 1.6 Missing Capabilities

| Capability | Status |
|-----------|--------|
| **Dynamic chart recommendation** | ❌ Chart types are hardcoded per industry in `dashboard_generator.py` |
| **Dashboard layout engine** | ❌ No layout system — Streamlit columns are hardcoded |
| **Global filter engine** | ❌ No cross-chart filter system |
| **Drilldown engine** | ❌ No drilldown or breadcrumb navigation |
| **AI dashboard assistant** | ❌ No natural language → dashboard action translation |
| **Dashboard customization** | ❌ No widget add/remove/resize/reorder |
| **Dashboard persistence** | ❌ Dashboard configs are not persisted (in-memory only) |
| **Dashboard metadata model** | ❌ No formal dashboard schema with versioning |
| **Access control for dashboards** | ❌ No per-dashboard RBAC |
| **Performance optimization** | ❌ No lazy loading, caching, or incremental rendering for dashboards |

## 2. Reusable Components

| Component | Reuse For |
|-----------|-----------|
| `DashboardRegistry` widget definitions | Chart recommendation input |
| `KPIRegistry` definitions | KPI intelligence engine seed |
| `IndustryKnowledge` KPIs and rules | KPI formula and threshold source |
| `SemanticMappingEngine` | Entity-to-column mapping for dynamic KPI/chart selection |
| `DashboardGenerator` | Base for dynamic dashboard config generation |
| `ReportExportService` | Extend for dashboard exports |
| `DashboardRecommendationEngine` (Phase 12.2) | Chart recommendation input |

## 3. Components to Replace

| Component | Replace With |
|-----------|-------------|
| `dashboard/sector_dashboards.py` | Dynamic DashboardRenderEngine |
| `dashboard/charts.py` hardcoded chart functions | Dynamic ChartRenderEngine |
| `dashboard_generator.py._generate_charts()` | ChartRecommendationEngine |
| `kpi_generator.py` static KPI computation | KPIIntelligenceEngine with formulas and confidence |
| `ai/engines/kpi_engine.py` hardcoded SQL | Semantic-aware KPI computation |

## 4. Components to Create

| Component | Purpose |
|-----------|---------|
| `services/dashboard_engine.py` | DashboardMetadata model + DashboardEngine |
| `services/kpi_intelligence.py` | KPIIntelligenceEngine — auto-detect KPIs with formulas and confidence |
| `services/chart_recommender.py` | ChartRecommendationEngine — recommend chart types from data characteristics |
| `services/dashboard_layout.py` | DashboardLayoutEngine — auto-generate responsive layouts |
| `services/filter_engine.py` | GlobalFilterEngine — reusable cross-chart filters |
| `services/drilldown_engine.py` | DrilldownEngine — KPI → Chart → Table → Record navigation |
| `services/dashboard_assistant.py` | AIDashboardAssistant — natural language to dashboard actions |
| `services/dashboard_export.py` | DashboardExportService — PDF, Excel, CSV, PNG exports |
| `services/dashboard_routes.py` | FastAPI endpoints for dashboard CRUD, customization, export |
| `frontend/features/dashboard-engine/*` | Dynamic dashboard rendering components |

## 5. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Breaking existing Streamlit dashboards | Keep `sector_dashboards.py` as fallback, build new engine in parallel |
| Performance with large datasets | Add caching, lazy loading, server-side aggregation |
| Frontend complexity | Build incrementally — layout engine first, then customization |
| RBAC integration complexity | Reuse existing permission system from `authentication/services.py` |

## 6. Implementation Order

1. **STEP 2**: Dashboard metadata model — foundation for everything
2. **STEP 3**: KPI Intelligence Engine — auto-detect KPIs with formulas
3. **STEP 4**: Chart Recommendation Engine — data-driven chart selection
4. **STEP 5**: Dashboard Layout Engine — auto-generate layouts
5. **STEP 6**: Global Filter Engine — cross-chart filtering
6. **STEP 7**: Drilldown Engine — navigation hierarchy
7. **STEP 8**: AI Dashboard Assistant — NL to dashboard actions
8. **STEP 9**: Dashboard Customization — widget CRUD, save/share
9. **STEP 10**: Exports — PDF, Excel, CSV, PNG
10. **STEP 11**: Performance — caching, lazy loading, pagination
11. **STEP 12**: Access Control — RBAC integration
12. **STEP 13**: Testing
13. **STEP 14**: Documentation
