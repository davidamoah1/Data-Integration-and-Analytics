# Data-to-Decision Workflow

## Product Proposition

**TURN RAW DATA INTO DECISIONS.**

The primary user journey in DataFlow follows seven clear stages:

```
RAW DATA → UNDERSTAND → QUALITY → ANALYSIS → VISUALIZATION → REPORT → PRESENTATION → DECISION
```

## Workflow Stages

### 1. Upload

**User action:** Drag & drop or select a file (CSV, XLSX, XLS).

**System behavior:**
- Validates file integrity and format (via `etl/file_security.py::FileValidator`)
- Runs governance classification (via `governance/__init__.py::classify_dataset`)
- Uploads to persistent storage (local, S3, R2, or Supabase — based on config)
- Triggers the full workflow pipeline

**Backend:** `POST /dataset-workflow/run` → `DatasetWorkflowOrchestrator.start()`

**Async mode:** When `REDIS_URL` is configured and a worker is running, the pipeline is enqueued as a background job (returns 202 with a `job_id` to poll). Otherwise runs synchronously.

---

### 2. Understand

**Purpose:** Automatically profile and understand the data's structure, types, distributions, and domain context.

**System behavior:**
- **Profiling:** Row/column counts, data types, null percentages, cardinality, distributions, correlations, outliers, sensitive column detection, primary key candidates.
- **Semantic Analysis:** Maps columns to business entities (revenue, date, name, etc.) using voting-based entity recognition (`ai/data_gatherer.py`).
- **Industry Detection:** Identifies the sector (healthcare, education, business, etc.) based on column names and value patterns with confidence scoring and alternative candidates.

**Backend stages:** `profiled` → `semantically_analyzed` → `industry_identified`

**Frontend:** `UnderstandStep.tsx` — displays profile summary, quality score overview, and detected industry with confidence.

---

### 3. Clean

**Purpose:** Transparent data quality assessment and smart cleaning with full undo support.

**System behavior:**
- Runs 15+ automated quality checks (`data_quality/checks.py::QualityCheckEngine`):
  - Missing values, blank fields, duplicates
  - Sentinel/placeholder values (999, -1, "N/A", "UNKNOWN")
  - Out-of-range values, invalid formats
  - Type mismatches, constant columns
  - Mixed-case inconsistencies, invalid dates
- Computes multi-dimensional quality score (`data_quality/quality_engine.py::QualityEngine`):
  - Completeness, Validity, Uniqueness, Consistency, Timeliness
  - Overall weighted score (0-100), traffic light, letter grade
- Detects drift (reference-based or time-based) via `data_quality/drift_detector.py`
- Detects schema changes via `data_quality/schema_monitor.py`
- Proposes transformations via `studios/cleaning_service.py::DataCleaningService`

**Cleaning actions supported:**
| Action | Method |
|--------|--------|
| Fill missing values | Mean, Median, Mode, Custom value |
| Remove duplicates | Exact row matching |
| Normalize categories | Standardize (y→Yes, n→No, etc.) |
| Normalize countries | Standard names (USA→United States) |
| Convert types | String to numeric |
| Parse dates | Auto-detect datetime formats |
| Flag outliers | IQR method |

**Traceability:**
- Every transformation is recorded with: `id`, `timestamp`, `action`, `column`, `description`, `affected_rows`, `applied_by`
- Transformations can be undone individually
- Full history available via `GET /dataset-workflow/{id}/clean/history`
- All cleaning actions are audit-logged

**Frontend:** `CleanStep.tsx` — shows findings by severity, transformation history with undo, "Apply All Suggested" bulk action.

---

### 4. Analyze

**Purpose:** Generate insights from the cleaned data using both AI-assisted and traditional statistical methods.

**System behavior:**
- **Easy Mode:** Users ask questions in plain language; the system translates to appropriate analysis
- **Pro Mode:** Full statistical controls — descriptive stats, frequency analysis, cross-tabulation, correlation matrix, distribution analysis, outlier detection, time-series, trend, comparative analysis
- **Auto-Insights:** AI-generated insights based on data patterns (trends, anomalies, correlations, dominance patterns)
- **Sector-Specific:** Analysis recommendations adapt to detected industry

**Backend stages:** `knowledge_extracted` → `insights_generated`

**Frontend:** `AnalyzeStep.tsx` — Easy/Pro mode toggle, question input with suggested questions (sector-aware), insight cards.

---

### 5. Visualize

**Purpose:** Generate interactive dashboards with appropriate chart types based on data structure.

**System behavior:**
- Recommends chart types based on:
  - Data types (measures vs. dimensions)
  - Cardinality and distributions
  - Temporal fields (time-series charts)
  - Geographic fields (maps)
  - Industry-specific templates
- Identifies available measures, dimensions, time fields, and geo fields
- Generates dashboard configuration for the Dashboard Engine

**Backend stage:** `dashboard_ready`

**Persistence:** Dashboard can be saved via `POST /semantic/persist-analysis` → creates dashboard, KPIs, and report records.

**Frontend:** `VisualizeStep.tsx` — chart recommendations, measure/dimension lists, save dashboard action.

---

### 6. Report

**Purpose:** Generate a professional, structured analysis report.

**System behavior:**
- Configurable report sections:
  - Executive Summary
  - Data Quality Assessment
  - Methodology
  - Visualizations
  - Recommendations
  - Limitations
- Report includes real analysis data (not templates)
- Persisted via `services/report_engine.py`
- Supports export to PDF

**Frontend:** `ReportStep.tsx` — report configuration (title, org, author, section toggles), preview, generate action.

---

### 7. Present

**Purpose:** One-click generation of a professional PPTX presentation.

**System behavior:**
- Generates presentation slides:
  - Title Slide
  - Executive Summary
  - Dataset Overview
  - Data Quality
  - Key Metrics
  - Main Trends
  - Key Findings
  - Recommendations
  - Conclusion
- Uses `python-pptx` for generation
- Available for download as .pptx file

**Frontend:** `PresentStep.tsx` — one-click generate, download, workflow complete celebration.

---

## Architecture

### Frontend Components

```
frontend/features/data-workflow/
├── index.ts              — Barrel exports
├── WorkflowStepper.tsx   — 7-step visual progress indicator
├── UploadStep.tsx        — File upload with drag & drop
├── UnderstandStep.tsx    — Profile, quality, industry display
├── CleanStep.tsx         — Findings, fixes, undo, history
├── AnalyzeStep.tsx       — Easy/Pro modes, insights
├── VisualizeStep.tsx     — Dashboard recommendations
├── ReportStep.tsx        — Report configuration & generation
└── PresentStep.tsx       — Presentation generation & download
```

### Main Page

```
frontend/app/(app)/data-to-decision/page.tsx
```

Orchestrates all step components with shared state management (React useState + useCallback). Connects to:
- `workflowService` for backend communication
- `datasetService` for persistence operations
- Audit-logged API calls

### Backend Pipeline

```
services/dataset_workflow.py          — Orchestrator (stage machine)
services/dataset_workflow_routes.py   — API endpoints (14 routes)
services/dataset_workflow_models.py   — Database persistence model
data_quality/checks.py                — 15+ quality checks
data_quality/quality_engine.py        — Composite scoring
data_quality/drift_detector.py        — Drift detection
data_quality/schema_monitor.py        — Schema monitoring
studios/cleaning_service.py           — Transformation engine
ai/data_gatherer.py                   — Semantic entity recognition
```

### Navigation

The "Data to Decision" page is accessible from the sidebar navigation for roles:
- Organization Owner
- Organization Admin
- Data Analyst
- Business Analyst
- Executive
- Researcher

---

## Design Principles

1. **Transparency:** Every automated action is visible and explained
2. **Traceability:** Every transformation is logged with user, timestamp, and rollback capability
3. **Reproducibility:** Methodology and parameters are recorded
4. **Progressive disclosure:** Simple by default, advanced on demand (Easy/Pro modes)
5. **Real data only:** No fake charts, no hardcoded statistics, no placeholder results
6. **Sector awareness:** Analysis adapts to detected industry
7. **Non-destructive:** Original data is preserved; cleaning creates a new version

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/dataset-workflow/run` | Start workflow |
| GET | `/dataset-workflow/{id}/status` | Get status |
| GET | `/dataset-workflow/{id}/profile` | Get profile |
| GET | `/dataset-workflow/{id}/quality` | Get quality report |
| GET | `/dataset-workflow/{id}/semantic` | Get semantic analysis |
| GET | `/dataset-workflow/{id}/industry` | Get industry detection |
| GET | `/dataset-workflow/{id}/metadata` | Get metadata |
| GET | `/dataset-workflow/{id}/insights` | Get insights |
| GET | `/dataset-workflow/{id}/dashboard` | Get dashboard recommendation |
| GET | `/dataset-workflow/{id}/summary` | Get analysis summary |
| POST | `/dataset-workflow/{id}/retry/{stage}` | Retry failed stage |
| POST | `/dataset-workflow/{id}/confirm-industry` | Confirm/override industry |
| POST | `/dataset-workflow/{id}/clean/apply` | Apply transformation |
| GET | `/dataset-workflow/{id}/clean/history` | Get transformation history |
