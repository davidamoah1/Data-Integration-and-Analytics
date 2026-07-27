# Dataset Intelligence Workflow

## Overview

The Dataset Intelligence Workflow transforms any uploaded dataset into a complete analytical experience through an AI-driven, multi-stage pipeline.

## Workflow Stages

```text
Upload → Validate → Profile → Quality Check → Semantic Analysis
→ Industry Detection → Metadata Generation → Business Knowledge
→ AI Insights → Dashboard Recommendation → Analysis Complete
```

### Stage Details

| Stage | Description | Output |
|-------|-------------|--------|
| **Uploaded** | Records file metadata (rows, columns, memory) | Row/column counts, memory usage |
| **Validated** | Checks for empty datasets, duplicate columns, empty columns | Validation issues list |
| **Profiled** | Comprehensive data profiling via `EnterpriseDataProfiler` | Per-column stats, correlations, sensitive data, PK candidates |
| **Quality Checked** | AI data quality assessment via `QualityIntelligenceEngine` | Quality score (0-100), findings, recommendations |
| **Semantically Analyzed** | Column-to-entity mapping via `SemanticMappingEngine` | Entity mappings, business concepts |
| **Industry Identified** | Industry detection with confidence and evidence | Industry, confidence, alternative candidates |
| **Metadata Generated** | Schema discovery via `MetadataExtractor` | Table metadata, PK/FK detection |
| **Knowledge Extracted** | Business knowledge via `KnowledgeGraphBuilder` and `KPIGenerator` | Knowledge graph, KPIs, business entities |
| **Insights Generated** | AI insights via `InsightGenerator` | Anomalies, trends, correlations, executive summary |
| **Dashboard Ready** | Dashboard recommendations via `DashboardRecommendationEngine` | Recommended charts, measures, dimensions |
| **Analysis Complete** | Final summary | Complete analysis summary |

## Architecture

### Backend Components

- **`services/dataset_workflow.py`** — `DatasetWorkflowOrchestrator` with status progression, retries, caching, progress events
- **`services/enterprise_profiler.py`** — `EnterpriseDataProfiler` consolidating all profiling logic
- **`services/dashboard_recommender.py`** — `DashboardRecommendationEngine` with accept/customize/reject
- **`services/dataset_workflow_routes.py`** — FastAPI endpoints for the workflow

### Reused Components

- `semantic/metadata_extractor.py` — MetadataExtractor
- `semantic/mapping_engine.py` — SemanticMappingEngine
- `semantic/knowledge_graph.py` — KnowledgeGraphBuilder
- `semantic/kpi_generator.py` — KPIGenerator
- `data_quality/quality_engine.py` — QualityIntelligenceEngine
- `ai_copilot/insight_generator.py` — InsightGenerator
- `semantic/dashboard_generator.py` — DashboardGenerator

### Frontend Components

- **`frontend/app/(app)/datasets/workflow/page.tsx`** — Main workflow page
- **`frontend/features/dataset-workflow/WorkflowTimeline.tsx`** — Processing timeline
- **`frontend/features/dataset-workflow/ProfileSummary.tsx`** — Dataset profile view
- **`frontend/features/dataset-workflow/QualityReportView.tsx`** — Quality report with findings
- **`frontend/features/dataset-workflow/IndustryDetectionView.tsx`** — Industry detection with confidence
- **`frontend/features/dataset-workflow/InsightCards.tsx`** — AI insight cards
- **`frontend/features/dataset-workflow/DashboardPreview.tsx`** — Dashboard recommendations

## Error Handling

Each stage:
- Logs execution time
- Supports up to 2 retries (configurable)
- Emits progress events on status change
- Records errors with full context

## Caching

Completed workflows are cached by dataset hash (shape + columns + sample rows). Re-uploading the same dataset returns cached results instantly.

## Performance

- **10K rows**: Completes in < 5 seconds
- **100K rows**: Completes in < 30 seconds
- **1M rows**: Requires background processing (planned)

## Usage

### API

```bash
# Run workflow
curl -X POST http://localhost:8000/dataset-workflow/run \
  -F "file=@dataset.csv"

# Get status
curl http://localhost:8000/dataset-workflow/{id}/status

# Get profile
curl http://localhost:8000/dataset-workflow/{id}/profile

# Get quality report
curl http://localhost:8000/dataset-workflow/{id}/quality

# Get insights
curl http://localhost:8000/dataset-workflow/{id}/insights

# Get dashboard recommendations
curl http://localhost:8000/dataset-workflow/{id}/dashboard
```

### Python

```python
from services.dataset_workflow import DatasetWorkflowOrchestrator
import pandas as pd

df = pd.read_csv("dataset.csv")
orchestrator = DatasetWorkflowOrchestrator()
state = orchestrator.start(df, dataset_name="dataset.csv")

print(f"Industry: {state.context['industry_result']['industry']}")
print(f"Quality: {state.context['quality_report']['score']['overall']}")
print(f"Insights: {state.context['insights']['total_insights']}")
```
