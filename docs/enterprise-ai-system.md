# Enterprise AI Decision Support System

## Overview

The Enterprise AI Decision Support System transforms the existing AI assistant into a comprehensive analytics platform capable of:

- **Explaining data** — Executive summaries, KPI highlights, trend analysis
- **Detecting issues** — Anomaly detection with explanations and impact assessment
- **Forecasting trends** — Multi-method time series forecasting with confidence intervals
- **Recommending actions** — Industry-specific, data-driven recommendations
- **Generating reports** — Professional reports in Markdown, HTML, PDF, and DOCX
- **Analyzing in natural language** — Intent detection and structured analytical operations
- **Explaining root causes** — Structured root cause analysis with evidence and confidence

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                          │
│  ┌──────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ │
│  │ Chat │ │ Exec   │ │ Root     │ │Forecast │ │ Anomaly  │ │
│  │      │ │Summary │ │ Cause    │ │         │ │          │ │
│  └──────┘ └────────┘ └──────────┘ └─────────┘ └──────────┘ │
│  ┌────────────┐ ┌──────────┐ ┌──────────────────────────┐  │
│  │Recommend   │ │NL        │ │Report Generation         │  │
│  │            │ │Analytics │ │                          │  │
│  └────────────┘ └──────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Enterprise API   │
                    │  Routes           │
                    └─────────┬─────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│  Context Engine  │ │  Prompt         │ │  Data Gatherer  │
│  (unified)       │ │  Orchestrator   │ │  (semantic)     │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌────────▼─────────┐
                    │  AI Gateway      │
                    │  (providers)     │
                    └────────┬─────────┘
                              │
                    ┌────────▼─────────┐
                    │  Database        │
                    │  (insights,      │
                    │   forecasts,     │
                    │   reports)       │
                    └──────────────────┘
```

## Components

### 1. Enterprise Context Engine (`ai/context_engine.py`)

Aggregates all context into a single `EnterpriseAIContext` object:
- **User context** — role, permissions, organization
- **Dataset context** — schema, profile, quality, semantic mappings
- **Dashboard context** — active filters, KPIs, charts
- **Industry context** — KPIs, business rules, entities
- **Conversation context** — recent messages, intent

```python
from ai.context_engine import EnterpriseContextEngine

engine = EnterpriseContextEngine(db)
context = engine.build(
    assistant_type="decision_copilot",
    user_id=1,
    df=dataframe,
    semantic_mappings={"date": "order_date", "revenue": "sales"},
    industry="retail",
)
```

### 2. Prompt Orchestrator (`ai/prompt_orchestrator.py`)

Modular prompt pipelines for specialized AI tasks:
- `EXECUTIVE_SUMMARY` — Structured summary with KPIs, risks, recommendations
- `ROOT_CAUSE_ANALYSIS` — Evidence-based root cause with confidence
- `FORECASTING` — Time series forecast with assumptions and limitations
- `ANOMALY_DETECTION` — Anomaly explanation with impact assessment
- `RISK_ANALYSIS` — Risk identification with severity and evidence
- `NL_ANALYTICS` — Natural language to structured analysis
- `REPORT_GENERATION` — Full report with methodology and appendix
- `KPI_EXPLANATION`, `TREND_ANALYSIS`, `DATA_QUALITY`, etc.

```python
from ai.prompt_orchestrator import PromptOrchestrator, PromptTaskType

orch = PromptOrchestrator()
messages = orch.build_messages(
    PromptTaskType.EXECUTIVE_SUMMARY,
    "What happened this month?",
    context,
)
```

### 3. Data Gatherer (`ai/data_gatherer.py`)

Semantic-aware data extraction from any DataFrame:
- `gather_for_summary()` — Overall stats, dimensions, trends, contributors
- `gather_for_root_cause()` — Period comparison, contributions, correlations
- `gather_for_trend()` — Time series with monthly aggregation
- `gather_for_forecast()` — Time series with date/value arrays
- `gather_for_anomaly()` — Time series with statistics
- `gather_for_report()` — Comprehensive data for report generation

No hardcoded SQL queries — works with any dataset via semantic mappings.

### 4. Executive Summary Engine (`ai/engines/executive_summary.py`)

Generates structured executive summaries with:
- KPI highlights with direction indicators
- Main drivers
- Risks with severity and evidence
- Opportunities
- Forecast direction and assumptions
- Recommended actions with priority and feasibility
- Confidence scoring with methodology

### 5. Root Cause Analysis Engine (`ai/engines/root_cause.py`)

Performs structured root cause analysis:
- Observation and magnitude
- Multiple root causes with evidence and contribution
- Ruled-out factors
- Conclusion with overall confidence
- Recommended actions

### 6. Enterprise Forecast Engine (`ai/engines/enterprise_forecast.py`)

Multi-method time series forecasting:
- **Methods**: linear, exponential, moving_average, seasonal, auto
- **Horizons**: short (7d), medium (30d), long (90d)
- **Confidence intervals** with configurable level
- **Assumptions** documentation
- **Model limitations** disclosure
- **AI interpretation** of forecast results

### 7. Enterprise Anomaly Engine (`ai/engines/enterprise_anomaly.py`)

Semantic-aware anomaly detection:
- **Statistical anomalies** (z-score based)
- **Trend breaks** (rolling mean deviation)
- **Missing records** (gap detection)
- **Value outliers** (non-time-series)
- **Industry-specific sensitivity**
- **"Why" explanations** for each anomaly
- **Impact assessment** (high/medium/low)

### 8. Recommendation Engine (`ai/engines/recommendation_engine.py`)

Industry-specific recommendations:
- **7 industry templates**: retail, healthcare, education, government, finance, manufacturing, logistics
- **Data-driven trigger detection** from analysis data
- **Template matching** to industry-specific actions
- **AI-enhanced recommendations** merged with templates
- **Priority sorting** (high → medium → low)
- **Expected impact** and **feasibility** assessment

### 9. NL Analytics Engine (`ai/engines/nl_analytics.py`)

Natural language to structured analysis:
- **Intent detection**: compare, rank, trend, explain, summarize, filter, highlight, breakdown
- **Query interpretation** in plain language
- **Structured analysis** based on intent
- **AI explanation** of results
- **Visualization recommendations** per intent type

### 10. Enterprise Report Engine (`ai/engines/enterprise_report.py`)

Professional report generation:
- **Report types**: executive, monthly, annual, quality, performance
- **Sections**: Executive Summary, KPI Highlights, Main Drivers, Data Overview, Trend Analysis, Top Contributors, Risks, Opportunities, Recommendations
- **Methodology** section with data sources and methods
- **Appendix** with detailed statistics
- **Export formats**: Markdown, HTML, PDF, DOCX

## API Endpoints

All enterprise AI endpoints are under `/api/ai/enterprise/`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/enterprise/executive-summary` | Generate executive summary |
| POST | `/ai/enterprise/root-cause` | Analyze root cause |
| POST | `/ai/enterprise/forecast` | Generate forecast |
| POST | `/ai/enterprise/anomaly` | Detect anomalies |
| POST | `/ai/enterprise/recommendations` | Get recommendations |
| POST | `/ai/enterprise/nl-analytics` | Natural language analytics |
| POST | `/ai/enterprise/report` | Generate report |
| GET | `/ai/enterprise/task-types` | List available task types |

## Security & Governance

Enhanced security features in `ai/security.py`:
- **Per-dataset RBAC** — `check_dataset_access()` enforces dataset-level permissions
- **Confidence disclosure** — `validate_confidence_disclosure()` ensures all responses include confidence
- **Evidence basis** — `distinguish_analysis_vs_assumptions()` marks data-backed vs assumed content
- **Full audit trail** — `create_audit_record()` logs all AI interactions
- **Enterprise validation** — `validate_enterprise_request()` combines all checks in one call

## Performance Optimization

Performance features in `ai/performance.py`:
- **PerformanceMonitor** — Tracks latency, failure rates, and generates alerts
- **TokenBudgetManager** — Allocates token budget by priority across context sections
- **LazyContextLoader** — Only loads relevant context sections per task type
- **`@track_performance`** decorator for automatic performance tracking

## Frontend

The Next.js AI page (`frontend/app/(app)/ai/page.tsx`) provides 8 tabs:
1. **Chat** — Interactive AI copilot
2. **Exec Summary** — One-click executive summary generation
3. **Root Cause** — Ask "why" questions with structured analysis
4. **Forecast** — Metric forecasting with horizon selection
5. **Anomalies** — Anomaly detection with explanations
6. **Recommend** — Industry-specific recommendations
7. **NL Analytics** — Natural language questions to structured analysis
8. **Report** — Report generation with format selection and download

## Testing

Run the test suite:

```bash
python -m pytest tests/test_enterprise_ai.py -v
```

69 tests covering all components:
- Context Engine (7 tests)
- Prompt Orchestrator (4 tests)
- Data Gatherer (7 tests)
- Executive Summary Engine (2 tests)
- Root Cause Analysis Engine (3 tests)
- Enterprise Forecast Engine (6 tests)
- Enterprise Anomaly Engine (4 tests)
- Recommendation Engine (5 tests)
- NL Analytics Engine (5 tests)
- Enterprise Report Engine (4 tests)
- Security Layer (13 tests)
- Performance (7 tests)

## File Structure

```
ai/
├── context_engine.py          # Enterprise Context Engine
├── prompt_orchestrator.py     # Modular Prompt Pipelines
├── data_gatherer.py           # Semantic-aware Data Extraction
├── enterprise_routes.py       # Enterprise API Routes
├── performance.py             # Performance Optimization
├── security.py                # Enhanced Security & Governance
└── engines/
    ├── executive_summary.py   # Executive Summary Engine
    ├── root_cause.py          # Root Cause Analysis Engine
    ├── enterprise_forecast.py # Enterprise Forecast Engine
    ├── enterprise_anomaly.py  # Enterprise Anomaly Engine
    ├── recommendation_engine.py # Recommendation Engine
    ├── nl_analytics.py        # Natural Language Analytics Engine
    └── enterprise_report.py   # Enterprise Report Engine

frontend/
├── app/(app)/ai/page.tsx      # Enhanced AI Copilot (8 tabs)
├── services/ai/aiService.ts   # Enterprise AI Service
└── types/index.ts             # Enterprise AI Types

tests/
└── test_enterprise_ai.py      # 69 tests

docs/
├── ai-gap-analysis.md         # Gap Analysis Document
└── enterprise-ai-system.md    # This documentation
```
