# Phase 12.2 — Gap Analysis: Enterprise Dataset Intelligence Workflow

## Audit Date: 2026-07-26

---

## 1. Existing Functionality (Reuse)

### Dataset Upload
- **ETL Routes** (`etl/routes.py`): `POST /etl/import/upload` (multipart), `POST /etl/import/preview`, `POST /etl/import/execute`
- **Semantic Routes** (`semantic/routes.py`): `POST /semantic/analyze` (multipart), `POST /semantic/detect-industry`, `POST /semantic/analyze-with-overrides`
- **Validation Routes** (`validation/routes.py`): `POST /validation/run` (multipart), `GET /validation/status/{id}`, `GET /validation/report/{id}`
- **Dataset Library** (`dataset_library/routes.py`): `GET /datasets/`, `GET /datasets/{id}/preview`, `GET /datasets/{id}/schema`

### Metadata Extraction
- **`semantic/metadata_extractor.py`**: `MetadataExtractor.extract(df)` → `TableMetadata` with column metadata, PK/FK detection, constraints, cardinality, value distribution
- **Status**: ✅ Complete — reuse as-is

### Data Profiling (3 separate implementations)
- **`semantic/data_profiler.py`**: `DataProfiler.profile(df)` → `DatasetProfile` with per-column quality metrics, outliers, patterns, quality score
- **`etl/profiling/__init__.py`**: `DataProfiler.profile(df)` → dict with numeric/datetime/categorical stats, outliers, quality score
- **`validation/profiler.py`**: `ValidationProfiler.profile(df)` → `DataProfileResult` with column stats, completeness, uniqueness
- **Status**: ⚠️ Three overlapping implementations — consolidate into one enterprise profiler

### Data Quality Engine
- **`data_quality/quality_engine.py`**: `QualityIntelligenceEngine` with composite score (0-100), findings, drift detection, schema monitoring, recommendations, traffic light grade
- **`data_quality/checks.py`**: `QualityCheckEngine` detects missing values, duplicates, sentinel values, out-of-range, invalid formats, type mismatches, constant columns, mixed-case
- **Status**: ✅ Robust — extend with business impact assessment and recommended fixes

### Semantic Engine
- **`semantic/semantic_engine.py`**: `SemanticMappingEngine.analyze(df)` → column-to-entity mapping, industry detection with weighted scoring (strong/medium/weak signals), confidence threshold (70%)
- **`semantic/mapping_engine.py`**: `SemanticMappingEngine` orchestrates metadata → profiling → semantic mapping → relationships → industry detection → KPIs → dashboard
- **`semantic/service.py`**: `SemanticIntelligenceService.analyze_dataset(df)` → full pipeline (mapping, knowledge graph, KPIs, dashboard, governance)
- **Status**: ✅ Advanced — reuse industry detection, entity mapping, KPI generation

### Industry Detection
- **`semantic/semantic_engine.py`**: Weighted scoring with strong signals (weight 3.0), moderate (2.0-2.5), weak/universal (no vote). Min confidence 70%. Tie-breaking returns "unknown".
- **`semantic/industry_knowledge.py`**: Industry knowledge bases for healthcare, education, agriculture, retail, banking, government, SME, logistics, manufacturing, telecom
- **`semantic/entity_library.py`**: Entity library with synonyms across industries
- **`semantic/extra_industries.py`**: Additional industry definitions
- **Status**: ✅ Multi-industry support — extend with value-based signals and statistical patterns

### Business Knowledge Extraction
- **`semantic/entity_library.py`**: 100+ business entities with synonyms across industries
- **`semantic/knowledge_graph.py`**: `KnowledgeGraphBuilder` builds entity relationships
- **`semantic/relationship_engine.py`**: Detects relationships between entities
- **`semantic/governance.py`**: `GovernanceEngine` generates business glossary
- **Status**: ✅ Exists — reuse for business metadata generation

### AI Insight Generation
- **`ai_copilot/insight_generator.py`**: `InsightGenerator.generate(df)` → anomalies, trends, correlations, dominance, quality issues, distribution patterns with severity and recommendations
- **`ai/engines/dashboard_insights.py`**: `DashboardInsightsEngine` generates key findings, risks, opportunities, recommendations via AI gateway
- **Status**: ✅ Exists — extend with confidence scores, supporting data, and executive summary

### Dashboard Generation
- **`semantic/dashboard_generator.py`**: `DashboardGenerator.generate(df, mapping_result)` → `DashboardConfig` with KPI cards, charts, filters, recommendations. Confidence threshold 85%.
- **`semantic/dashboard_registry.py`**: Industry-specific dashboard templates
- **`semantic/kpi_registry.py`**: Industry-specific KPI definitions
- **Status**: ✅ Exists — extend into recommendation engine with accept/customize/reject

### AI Workflow Engine
- **`ai/workflow.py`**: `WorkflowEngine` with step handlers for import, clean, profile, quality_check, transform, load, generate_dashboard, generate_report, generate_insights, forecast, anomaly_check, decision_analysis, notify, email, archive
- **Status**: ✅ Exists — adapt for dataset intelligence workflow with status progression

### Next.js Frontend
- **`frontend/`**: App Router with login, dashboard, datasets, analytics, AI copilot, reports, scheduler, notifications, admin, settings pages
- **`frontend/features/datasets/DatasetUpload.tsx`**: Drag-and-drop upload with 3-stage pipeline (upload → validate → semantic analyze)
- **`frontend/services/`**: API client with auth, dataset, dashboard, AI services
- **Status**: ✅ Foundation exists — extend with workflow timeline, quality report, semantic report, insight cards

---

## 2. Missing Functionality (Build)

### Unified Dataset Workflow Orchestrator
- **Gap**: No single orchestrator that chains: upload → validate → profile → quality → semantic → industry → metadata → insights → dashboard
- **Need**: `DatasetWorkflowOrchestrator` class with status progression, progress events, error handling, retries, execution time logging
- **Location**: New `services/dataset_workflow.py`

### Enterprise Dataset Profiler (Enhanced)
- **Gap**: Three separate profilers with overlapping functionality. Missing: file encoding detection, memory usage, correlations, sensitive information detection, candidate primary key scoring
- **Need**: Consolidate into `EnterpriseDataProfiler` with all features
- **Location**: Enhance `semantic/data_profiler.py` or new `services/enterprise_profiler.py`

### AI Quality Engine Extensions
- **Gap**: Quality engine lacks: business impact assessment, estimated fix effort, recommended fix actions per finding, invalid date/numeric detection
- **Need**: Extend `QualityIntelligenceResult` with per-finding business impact and fix recommendations
- **Location**: Extend `data_quality/quality_engine.py` and `data_quality/checks.py`

### Advanced Industry Detection
- **Gap**: Current detection uses column names and some value signals. Missing: data distribution analysis, statistical pattern matching, relationship-based signals, alternative candidate ranking
- **Need**: Enhance with value distributions, statistical patterns, alternative candidates with evidence
- **Location**: Extend `semantic/semantic_engine.py`

### Dashboard Recommendation Engine
- **Gap**: `DashboardGenerator` generates dashboards but doesn't present recommendations as accept/customize/reject
- **Need**: `DashboardRecommendationEngine` that recommends dashboards based on industry, measures, dimensions, time/geo fields with explanations
- **Location**: New `services/dashboard_recommender.py`

### Workflow API Endpoints
- **Gap**: No unified API for: start workflow, get workflow status, get profile, get quality report, get semantic analysis, get insights, get dashboard recommendations, retry failed stage
- **Need**: New FastAPI router `services/dataset_workflow_routes.py`
- **Location**: New routes integrated into `api/main.py`

### Next.js Workflow UI
- **Gap**: Current upload component is basic. Missing: processing timeline, quality report view, semantic report view, industry detection view, AI insight cards, dashboard preview, error recovery
- **Need**: Full workflow page with stage-by-stage progress
- **Location**: `frontend/app/(app)/datasets/workflow/` and `frontend/features/dataset-workflow/`

### Background Processing
- **Gap**: Current processing is synchronous. Large datasets (100K+ rows) will block.
- **Need**: Background task execution with status polling
- **Location**: Use FastAPI `BackgroundTasks` or existing scheduler

### Caching
- **Gap**: Analysis results not cached — re-running same dataset repeats all work
- **Need**: Cache profiles, quality reports, semantic analysis by dataset hash
- **Location**: Use existing `performance/cache.py` `CacheManager`

---

## 3. Components to Reuse (No Changes)

| Component | File | Purpose |
|-----------|------|---------|
| MetadataExtractor | `semantic/metadata_extractor.py` | Schema discovery, PK/FK detection |
| EntityLibrary | `semantic/entity_library.py` | Business entity synonyms |
| IndustryKnowledge | `semantic/industry_knowledge.py` | Industry knowledge bases |
| KnowledgeGraphBuilder | `semantic/knowledge_graph.py` | Entity relationship graph |
| GovernanceEngine | `semantic/governance.py` | Business glossary |
| KPIRegistry | `semantic/kpi_registry.py` | Industry KPI definitions |
| DashboardRegistry | `semantic/dashboard_registry.py` | Industry dashboard templates |
| ReportRegistry | `semantic/report_registry.py` | Industry report types |
| InsightGenerator | `ai_copilot/insight_generator.py` | Automated insight detection |
| API Client | `frontend/services/api/client.ts` | Frontend API layer |
| Auth Store | `frontend/stores/authStore.ts` | Frontend auth state |

---

## 4. Components to Improve

| Component | File | Improvement |
|-----------|------|-------------|
| DataProfiler | `semantic/data_profiler.py` | Add encoding, memory, correlations, sensitive data detection |
| QualityCheckEngine | `data_quality/checks.py` | Add invalid date/numeric detection, business impact per finding |
| SemanticMappingEngine | `semantic/semantic_engine.py` | Add value distribution signals, statistical patterns, alternative candidates |
| DashboardGenerator | `semantic/dashboard_generator.py` | Convert to recommendation engine with accept/customize/reject |
| DatasetUpload | `frontend/features/datasets/DatasetUpload.tsx` | Replace with full workflow UI |

---

## 5. Components to Create

| Component | Location | Purpose |
|-----------|----------|---------|
| DatasetWorkflowOrchestrator | `services/dataset_workflow.py` | Unified workflow with status progression |
| EnterpriseDataProfiler | `services/enterprise_profiler.py` | Consolidated profiler with all features |
| DashboardRecommendationEngine | `services/dashboard_recommender.py` | Dashboard recommendations with explanations |
| DatasetWorkflowRoutes | `services/dataset_workflow_routes.py` | FastAPI endpoints for workflow |
| WorkflowPage | `frontend/app/(app)/datasets/workflow/` | Next.js workflow UI |
| WorkflowTimeline | `frontend/features/dataset-workflow/` | Processing timeline component |
| QualityReportView | `frontend/features/dataset-workflow/` | Quality report display |
| InsightCards | `frontend/features/dataset-workflow/` | AI insight cards |
| DashboardPreview | `frontend/features/dataset-workflow/` | Dashboard preview |

---

## 6. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing Streamlit dashboard | All new code in separate modules; existing routes unchanged |
| Performance with large datasets | Background processing + caching from day 1 |
| Duplicate profiling logic | Consolidate into enterprise profiler, deprecate old ones gradually |
| Frontend npm install issues | Trimmed dependencies; can add back later |
| Industry detection false positives | Confidence thresholds + user confirmation flow preserved |

---

## 7. Implementation Order

1. **STEP 2**: DatasetWorkflowOrchestrator (backend)
2. **STEP 3**: EnterpriseDataProfiler (backend)
3. **STEP 4**: Quality engine extensions (backend)
4. **STEP 5**: Advanced industry detection (backend)
5. **STEP 6**: Business knowledge extraction (backend — mostly reuse)
6. **STEP 7**: AI insight engine extensions (backend)
7. **STEP 8**: Dashboard recommendation engine (backend)
8. **STEP 10**: FastAPI workflow routes (backend)
9. **STEP 9**: Next.js workflow UI (frontend)
10. **STEP 11**: Performance — background processing, caching
11. **STEP 12**: Tests
12. **STEP 13**: Documentation
