# Phase 7 — Executive Decision Center (Part 4)
# Enterprise AI Decision Engine

## Purpose

This document defines the architecture, services, prompts, workflows, APIs, model management, and operational strategy for the Enterprise AI Decision Engine in AEDIP Phase 7. The engine behaves as an **AI Decision Partner**, not a chatbot. It answers: *What happened? Why? What may happen next? What should be done? What evidence supports the recommendation? How confident is the prediction?*

---

## 1. Design Principles

1. **Decision-first output.** Every AI response must lead to a decision, action, or insight.
2. **Evidence-based.** Recommendations cite data, charts, or lineage where possible.
3. **Confidence-aware.** Always expose confidence, data freshness, coverage, model, and limitations.
4. **Responsible AI.** Enforce RBAC, audit AI outputs, accept feedback, avoid hallucinated certainty.
5. **Modular engines.** Each module is independent, composable, and testable.
6. **Human-in-the-loop.** Executives approve, reject, or modify AI recommendations.
7. **No redesign of prior phases.** Reuse Phase 6 AI services, Phase 5 ETL, existing auth, existing DB, and existing dashboards.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Executive Decision Center UI                            │
│           (Decision Dashboard · Briefing · Recommendations · Scenarios)        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI Decision Engine API Layer                            │
│  /ai/decision/briefing    /ai/decision/recommendations   /ai/decision/forecast │
│  /ai/decision/scenario    /ai/decision/root-cause        /ai/decision/benchmark│
│  /ai/decision/insights    /ai/decision/alerts              /ai/decision/story    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI Decision Engine Service Layer                        │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Insight      │ │ Recommendation │ │ Forecast     │ │ Risk         │          │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Opportunity  │ │ Trend          │ │ Executive    │ │ Daily        │          │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Weekly/Monthly│ │ KPI Interpreter│ │ Data         │ │ Scenario     │          │
│  │ Report       │ │                │ │ Storytelling │ │ Simulator    │          │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Benchmark    │ │ Root Cause     │ │ Smart Alerts │ │ Decision     │          │
│  │              │ │ Analysis       │ │              │ │ Timeline     │          │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐                           │
│  │ Goal Tracking│ │ Strategy       │ │ AI Feedback  │                           │
│  └──────────────┘ └────────────────┘ └──────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI Gateway & Model Management                         │
│  Reuse Phase 6 AIGateway · Provider routing · Token/cost limits · Caching      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Data & Knowledge Layer                                  │
│  Existing AEDIP DB · Data Warehouse · ETL metadata · KPI definitions · RBAC      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Engine Modules

### 3.1 AI Insight Engine
- **Purpose:** Generate high-level observations from data changes, anomalies, and trends.
- **Inputs:** KPI values, historical time series, anomaly flags, ETL logs, alerts.
- **Output:** Structured insight objects with observation, evidence, trend direction, severity, and supporting metrics.
- **Example:** "Revenue declined 12% in Region A between May and June. Product X accounted for 68% of the drop."

### 3.2 AI Recommendation Engine
- **Purpose:** Suggest specific executive actions with full decision intelligence metadata.
- **Required output fields:**
  - `observation`
  - `reason`
  - `evidence` (data references, chart IDs)
  - `impact` (business effect)
  - `risk`
  - `confidence_score` (0–1)
  - `recommended_action`
  - `estimated_business_value`
  - `priority` (critical, high, medium, low)
  - `responsible_department`
  - `cost_estimate` (optional)
  - `timeframe` (optional)
- **Feedback loop:** users accept, reject, or modify recommendations; results feed model refinement.

### 3.3 AI Forecast Engine
- **Purpose:** Predict future values for KPIs and metrics.
- **Supported targets:** revenue, attendance, enrollment, patients, inventory, sales, donations, budget, crop yield, demand, disease cases, staffing.
- **Algorithms:**
  - Statistical: ARIMA, SARIMA, Exponential Smoothing, Prophet.
  - ML: XGBoost, Random Forest, LightGBM.
  - Deep Learning: optional local/in-house LSTM/Transformer.
  - Ensemble: weighted average of top models.
- **Selection:** admin-configurable per metric; default is auto-select via backtest winner.
- **Output:** point forecast, confidence interval, horizon, model used, backtest MAPE, data coverage.

### 3.4 AI Risk Engine
- **Purpose:** Identify and quantify operational, financial, and strategic risks.
- **Capabilities:** forecast risk, budget overrun, inventory shortage, staffing gap, data quality decline, late reports, ETL failure, security event correlation.
- **Output:** risk score, probability, impact, mitigation recommendation, owner.

### 3.5 AI Opportunity Engine
- **Purpose:** Surface upside opportunities from data.
- **Capabilities:** demand spikes, underperforming regions with growth potential, cost savings, process improvements, cross-department collaboration.
- **Output:** opportunity score, expected value, confidence, supporting evidence.

### 3.6 AI Trend Engine
- **Purpose:** Detect and explain trends across dimensions (time, region, department, product).
- **Capabilities:** trend direction, rate of change, seasonality, outliers, comparison to prior periods.
- **Output:** structured trend narrative with evidence.

### 3.7 AI Executive Summary Engine
- **Purpose:** Generate concise summaries for executives.
- **Inputs:** any dashboard, report, or dataset.
- **Output:** 3–5 bullet executive summary, key takeaways, decisions required.

### 3.8 AI Daily Briefing Engine
- **Purpose:** Generate the AI Daily Briefing every morning.
- **Sections:** organization summary, critical events, positive trends, negative trends, forecasts, recommendations, upcoming deadlines, pending approvals, security issues, data quality status, ETL status, department highlights.
- **Output:** structured briefing object for UI rendering and TTS/email fallback.

### 3.9 AI Weekly & Monthly Executive Report Engines
- **Purpose:** Generate periodic executive reports automatically.
- **Sections:** performance overview, top wins, top risks, KPI scorecard, forecast updates, AI recommendations, decisions made, pending decisions, department highlights, next period outlook.
- **Output:** report payload suitable for PDF/Word export and interactive dashboard.

### 3.10 AI KPI Interpreter
- **Purpose:** Explain any KPI in plain language.
- **Inputs:** KPI definition, current value, target, historical values.
- **Output:** natural language explanation, context, whether performance is on track, contributing factors.

### 3.11 AI Data Storytelling Engine
- **Purpose:** Convert charts into narrative summaries.
- **Example:** Instead of a sales chart, output "Revenue increased steadily from January to April before declining in May. The decline was mainly associated with Region A. Product X accounted for most of the reduction."
- **Output:** narrative, chart references, key turning points.

### 3.12 AI Scenario Simulator & What-If Analysis
- **Purpose:** Answer what-if questions with visual comparisons.
- **Examples:**
  - "What happens if revenue increases by 15%?"
  - "What happens if attendance falls by 20%?"
  - "What happens if inventory doubles?"
- **Output:** adjusted forecast, impact on related KPIs, comparison chart, risks/opportunities.

### 3.13 AI Benchmark Engine
- **Purpose:** Compare performance across departments, branches, regions, schools, hospitals, churches, projects, business units.
- **Privacy:** internal benchmarking is default. Cross-organization benchmarking requires explicit opt-in and anonymized aggregate data.
- **Output:** ranking, percentile, gap analysis, peer group, improvement recommendations.

### 3.14 AI Root Cause Analysis Engine
- **Purpose:** Automatically explain causes for negative outcomes.
- **Domains:** revenue decrease, attendance decline, inventory shortages, poor KPI performance, delayed reporting, low data quality, failed ETL jobs, budget variance.
- **Output:** root cause hypotheses, evidence, confidence, recommended diagnostic actions.

### 3.15 AI Smart Alerts Engine
- **Purpose:** Generate intelligent, contextual alerts beyond threshold rules.
- **Trigger types:** KPI threshold, forecast risk, budget overrun, low attendance, medicine shortage, inventory risk, late reports, failed ETL, data quality decline, security events.
- **Output:** alert object with severity, explanation, recommended action, owner.

### 3.16 AI Decision Timeline Engine
- **Purpose:** Store and retrieve decision history.
- **Fields:** decision, reason, expected outcome, actual outcome, lessons learned, decision maker, timestamp.
- **Output:** timeline entries for review and learning.

### 3.17 AI Goal Tracking Engine
- **Purpose:** Track user-defined goals automatically.
- **Examples:** increase revenue by 10%, reduce absenteeism, increase church membership, reduce patient waiting time.
- **Output:** goal status, progress, projected achievement date, gap, recommendations.

### 3.18 AI Strategy Assistant
- **Purpose:** Help executives formulate strategic initiatives from data insights.
- **Capabilities:** initiative draft, resource estimation, risk assessment, milestone suggestions, success metrics.

---

## 4. Prompt Architecture

### 4.1 Prompt Engineering Standards
- Use structured system prompts to constrain output.
- Use few-shot examples for complex engines.
- Enforce JSON mode where supported.
- Chain-of-thought for root cause and recommendations.
- All prompts include RBAC context, organization context, and data freshness.

### 4.2 Universal System Prompt

```
You are an Enterprise AI Decision Partner for AEDIP.
You analyze organizational data and produce executive-grade insights.
Rules:
1. Answer: What happened? Why? What may happen next? What should be done? What evidence supports it? How confident are you?
2. Always cite data, metrics, and sources when possible.
3. Never present predictions as certainty. Include confidence and limitations.
4. Use simple, executive-appropriate language.
5. Respect RBAC: only use authorized data.
6. Output structured JSON unless asked for prose.
7. Avoid speculation beyond the provided context.
8. Flag missing, stale, or low-coverage data.
```

### 4.3 Engine-Specific Prompts

#### Recommendation Engine
```json
{
  "role": "AI Decision Partner",
  "task": "Generate executive recommendations based on the provided context.",
  "context": {
    "organization": "{org_name}",
    "department": "{department}",
    "date_range": "{date_range}",
    "kpis": "{kpi_snapshot}",
    "alerts": "{active_alerts}",
    "forecasts": "{forecast_snapshot}",
    "data_quality": "{dq_score}",
    "etl_status": "{etl_status}"
  },
  "output_schema": {
    "recommendations": [
      {
        "observation": "string",
        "reason": "string",
        "evidence": ["string"],
        "impact": "string",
        "risk": "string",
        "confidence_score": "float 0-1",
        "recommended_action": "string",
        "estimated_business_value": "string",
        "priority": "critical|high|medium|low",
        "responsible_department": "string"
      }
    ]
  }
}
```

#### Daily Briefing Engine
```json
{
  "role": "AI Decision Partner",
  "task": "Generate the daily executive briefing.",
  "context": {
    "date": "{today}",
    "organization": "{org_name}",
    "health_score": "{health_score}",
    "kpis": "{kpi_values}",
    "alerts": "{alerts}",
    "forecasts": "{forecasts}",
    "recommendations": "{recommendations}",
    "deadlines": "{upcoming_deadlines}",
    "approvals": "{pending_approvals}",
    "security": "{security_status}",
    "data_quality": "{dq_score}",
    "etl_status": "{etl_status}",
    "departments": "{department_highlights}"
  },
  "output_schema": {
    "sections": [
      {
        "type": "summary|critical_events|positive_trends|negative_trends|forecast|recommendations|deadlines|approvals|security|data_quality|etl_status|departments",
        "title": "string",
        "content": "string",
        "items": ["string"],
        "priority": "high|medium|low"
      }
    ]
  }
}
```

#### Root Cause Analysis Engine
```json
{
  "role": "AI Decision Partner",
  "task": "Perform root cause analysis for the issue below.",
  "issue": {
    "metric": "{metric_name}",
    "observed_change": "{change_description}",
    "time_range": "{time_range}",
    "context": "{supporting_data}"
  },
  "output_schema": {
    "hypotheses": [
      {
        "cause": "string",
        "confidence": "float 0-1",
        "evidence": ["string"],
        "supporting_dimensions": ["string"],
        "recommended_diagnostic_action": "string"
      }
    ],
    "data_quality_notes": "string",
    "limitations": ["string"]
  }
}
```

#### Forecast Engine
```json
{
  "role": "AI Forecast Engine",
  "task": "Forecast the target metric over the specified horizon.",
  "context": {
    "target": "{metric_name}",
    "horizon_days": "int",
    "granularity": "day|week|month|quarter",
    "historical_data": "{time_series_csv_or_json}",
    "metadata": "{events, seasonality, known_factors}"
  },
  "output_schema": {
    "model_used": "string",
    "forecast": [
      {"period": "string", "value": "float", "lower_bound": "float", "upper_bound": "float"}
    ],
    "confidence": "float 0-1",
    "mape": "float",
    "data_freshness": "datetime",
    "data_coverage": "float 0-1",
    "known_limitations": ["string"]
  }
}
```

#### Scenario Simulator
```json
{
  "role": "AI Scenario Simulator",
  "task": "Simulate the impact of a hypothetical change on the target metric and related KPIs.",
  "scenario": {
    "variable": "{metric_name}",
    "change_type": "increase|decrease|set_value",
    "change_value": "float or percent",
    "cascade": true
  },
  "output_schema": {
    "baseline": "{current_value}",
    "projected_value": "float",
    "impacted_kpis": [
      {"kpi": "string", "baseline": "float", "projected": "float", "change_percent": "float"}
    ],
    "risks": ["string"],
    "opportunities": ["string"],
    "confidence": "float 0-1"
  }
}
```

---

## 5. Service Layer

### Package Structure

```
ai_decision/
├── __init__.py
├── engines/
│   ├── insight_engine.py
│   ├── recommendation_engine.py
│   ├── forecast_engine.py
│   ├── risk_engine.py
│   ├── opportunity_engine.py
│   ├── trend_engine.py
│   ├── summary_engine.py
│   ├── briefing_engine.py
│   ├── report_engine.py
│   ├── kpi_interpreter.py
│   ├── storytelling_engine.py
│   ├── scenario_engine.py
│   ├── benchmark_engine.py
│   ├── root_cause_engine.py
│   ├── smart_alert_engine.py
│   ├── decision_timeline.py
│   ├── goal_engine.py
│   └── strategy_engine.py
├── models/
│   ├── local_forecast.py          # StatsModels / Prophet / sklearn wrappers
│   └── embeddings.py              # Optional vector cache
├── prompts/
│   ├── system_prompts.py
│   ├── recommendation_prompts.py
│   ├── briefing_prompts.py
│   ├── root_cause_prompts.py
│   ├── forecast_prompts.py
│   ├── scenario_prompts.py
│   └── storytelling_prompts.py
├── workflows/
│   ├── daily_briefing_workflow.py
│   ├── recommendation_workflow.py
│   ├── alert_generation_workflow.py
│   └── report_generation_workflow.py
├── cache/
│   └── decision_cache.py
├── feedback/
│   └── recommendation_feedback.py
├── schemas/
│   └── decision_schemas.py      # Pydantic models
├── tasks/
│   └── celery_tasks.py
└── api/
    └── decision_routes.py         # FastAPI routes
```

### Key Services

| Service | Responsibility |
|---------|----------------|
| `DecisionCenterService` | Orchestrates engine calls for dashboard payloads. |
| `BriefingService` | Generates, caches, and stores daily briefings. |
| `RecommendationService` | Creates, ranks, and tracks recommendations. |
| `ForecastService` | Runs and caches forecasts; selects models. |
| `RiskService` | Evaluates and ranks enterprise risks. |
| `ScenarioService` | Executes what-if simulations. |
| `BenchmarkService` | Computes internal/cross-org benchmarks. |
| `RootCauseService` | Runs diagnostic analysis. |
| `SmartAlertService` | Generates and deduplicates smart alerts. |
| `DecisionTimelineService` | Records and retrieves decision history. |
| `GoalTrackingService` | Tracks progress against goals. |
| `StorytellingService` | Converts charts/data into narratives. |
| `ModelRegistryService` | Tracks forecast model versions and metrics. |
| `FeedbackService` | Collects and applies user feedback. |

---

## 6. Workflows

### 6.1 Daily Briefing Workflow

1. Scheduler triggers at 06:00 organization timezone.
2. Fetch health score, KPIs, alerts, forecasts, deadlines, approvals, security, DQ, ETL, department highlights.
3. Run `BriefingEngine.generate()`.
4. Cache result in Redis with key `briefing:{org_id}:{date}` TTL 12h.
5. Store in `ai_briefings` table.
6. Send notifications to subscribed executives.
7. Render in UI / email / TTS fallback.

### 6.2 Recommendation Workflow

1. Trigger: scheduled, alert-driven, or user-requested.
2. Gather context (KPIs, alerts, forecasts, recent decisions, goals).
3. Run `RecommendationEngine.generate()`.
4. Filter by RBAC, deduplicate, score by value and confidence.
5. Persist to `ai_recommendations` with `status = pending`.
6. Notify owners and responsible departments.
7. Surface in Decision Center; collect feedback.

### 6.3 Forecast Workflow

1. User or scheduler requests forecast for metric/horizon.
2. Fetch historical data via `DashboardDataService` / warehouse.
3. If auto-select, run backtest across candidate models.
4. Select winning model by MAPE/RMSE.
5. Generate forecast + confidence intervals.
6. Persist to `ai_forecasts`.
7. Cache result; invalidate on new data.

### 6.4 Smart Alert Workflow

1. Scheduled anomaly/forecast/risk scan or real-time event ingestion.
2. Run `SmartAlertEngine.detect()`.
3. Score and deduplicate alerts.
4. Persist to `dc_alerts` with `is_smart_alert = true`.
5. Route notifications via channels.
6. Learn from user dismissals/escalations.

### 6.5 Root Cause Workflow

1. User selects metric/issue or automated trigger.
2. Fetch related dimensions (region, product, department, time).
3. Run `RootCauseEngine.analyze()`.
4. Return ranked hypotheses with evidence.
5. Store result in `ai_root_cause_analyses`.
6. Surface in Decision Center and link to recommendations.

---

## 7. API Specification

Base path: `/api/v1/ai/decision`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/briefing` | Get today's AI Daily Briefing. |
| GET | `/briefing/history` | Get briefing history. |
| POST | `/briefing/generate` | Force regenerate today's briefing. |
| GET | `/recommendations` | List AI recommendations. |
| POST | `/recommendations` | Generate new recommendations. |
| GET | `/recommendations/{id}` | Get recommendation details. |
| POST | `/recommendations/{id}/feedback` | Accept/reject/modify recommendation. |
| GET | `/insights` | Get AI-generated insights. |
| POST | `/insights` | Generate insights for a context. |
| GET | `/forecasts` | List forecasts. |
| POST | `/forecasts` | Generate a forecast. |
| GET | `/forecasts/{id}` | Get forecast details. |
| GET | `/forecasts/models` | List available forecast models. |
| POST | `/scenarios` | Run what-if scenario. |
| GET | `/scenarios/{id}` | Get scenario result. |
| POST | `/benchmarks` | Run benchmark comparison. |
| GET | `/benchmarks` | List benchmark reports. |
| POST | `/root-cause` | Run root cause analysis. |
| GET | `/root-cause/{id}` | Get root cause result. |
| GET | `/alerts` | List smart alerts. |
| POST | `/alerts/generate` | Trigger smart alert scan. |
| GET | `/timeline` | Get decision timeline. |
| POST | `/timeline` | Record a decision. |
| GET | `/goals` | List goals. |
| POST | `/goals` | Create goal. |
| GET | `/goals/{id}/progress` | Get goal progress. |
| POST | `/story` | Generate narrative from chart/data. |
| GET | `/reports/weekly` | Generate weekly executive report. |
| GET | `/reports/monthly` | Generate monthly executive report. |
| POST | `/reports` | Generate custom executive report. |
| POST | `/feedback` | Submit general AI feedback. |

### Example Request/Response

#### POST /ai/decision/recommendations

Request:
```json
{
  "organization_id": 1,
  "department_id": null,
  "context": "monthly_review",
  "max_results": 5
}
```

Response:
```json
{
  "recommendations": [
    {
      "id": "rec_123",
      "observation": "Revenue in Region A fell 12% in June.",
      "reason": "Product X sales declined due to supplier delays.",
      "evidence": ["sales_region_a_june.csv", "product_x_inventory_alert"],
      "impact": "Estimated $24k monthly revenue loss.",
      "risk": "If unaddressed, Q3 revenue target may be missed by 8%.",
      "confidence_score": 0.87,
      "recommended_action": "Expedite supplier delivery and launch promotion for Product X.",
      "estimated_business_value": "$18k–$28k recovery per month",
      "priority": "high",
      "responsible_department": "Sales",
      "status": "pending"
    }
  ],
  "generated_at": "2026-07-13T06:00:00Z"
}
```

---

## 8. Model Management

### 8.1 Model Registry

Table `ai_decision_models`:
- `id`, `name`, `engine_type`, `algorithm`, `version`, `description`
- `supported_targets` (JSON)
- `default_hyperparameters` (JSON)
- `is_active`, `is_default`, `requires_gpu`, `local_only`
- `created_at`, `updated_at`, `created_by`

### 8.2 Forecast Model Selection

- **Auto-select:** backtest on recent history; pick model with lowest MAPE/RMSE.
- **Manual:** admin selects per metric.
- **Comparison:** return forecasts from multiple models side-by-side.

### 8.3 Model Performance Tracking

Table `ai_model_runs`:
- `id`, `model_id`, `target`, `horizon`, `backtest_period`
- `mape`, `rmse`, `mae`, `coverage`
- `training_time_ms`, `inference_time_ms`
- `data_points_used`, `generated_at`

### 8.4 Local vs External Models

- **Statistical/ML forecasts:** run locally via `statsmodels`, `prophet`, `scikit-learn`, `xgboost`.
- **LLM-based reasoning:** routed through Phase 6 `AIGateway` with provider fallback.
- **Optional deep learning:** containerized local service with GPU support for LSTM/Transformer experiments.

### 8.5 Caching Strategy

- Redis cache for forecasts, briefings, recommendations, benchmarks.
- TTLs: briefing 12h, forecast until next data refresh, recommendations 1h, insights 30m.
- Cache keys include organization, parameters, and data version hash.

---

## 9. Background Jobs

### Celery Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `generate_daily_briefing` | 06:00 org timezone | Generate and cache daily briefing. |
| `generate_recommendations` | Every 4 hours | Refresh recommendation pool. |
| `run_forecast_backtests` | Daily 02:00 | Evaluate and select forecast models. |
| `generate_smart_alerts` | Every 30 minutes | Detect and create smart alerts. |
| `run_department_benchmarks` | Weekly Monday 05:00 | Update benchmark rankings. |
| `generate_weekly_report` | Monday 07:00 | Weekly executive report. |
| `generate_monthly_report` | 1st of month 07:00 | Monthly executive report. |
| `check_goal_progress` | Daily 08:00 | Update goal tracking statuses. |
| `archive_decision_timeline` | Daily 01:00 | Archive old timeline entries. |
| `prune_ai_cache` | Daily 03:00 | Expire stale cache entries. |

### APScheduler Jobs

- Same tasks wrapped for lightweight deployments without Celery.
- Configuration toggled via env var `USE_CELERY=true|false`.

### Idempotency

- Use deterministic cache keys and `ON DUPLICATE KEY UPDATE` semantics.
- Store task run IDs; skip if already processed for the same window.

---

## 10. Database Additions

New tables extend Phase 7 Part 2 schema. All tables include `organization_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, and `is_deleted`.

### 10.1 Core Tables

```sql
CREATE TABLE ai_recommendations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  engine_type VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  observation TEXT NOT NULL,
  reason TEXT NOT NULL,
  evidence JSON,
  impact TEXT,
  risk TEXT,
  confidence_score DECIMAL(4,3),
  recommended_action TEXT,
  estimated_business_value VARCHAR(255),
  priority VARCHAR(16),
  responsible_department_id BIGINT,
  responsible_user_id BIGINT,
  status VARCHAR(32) DEFAULT 'pending',
  source_alert_id BIGINT,
  source_kpi_id BIGINT,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  accepted_at DATETIME,
  rejected_at DATETIME,
  modified_at DATETIME,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (responsible_department_id) REFERENCES departments(id),
  FOREIGN KEY (responsible_user_id) REFERENCES users(id),
  INDEX idx_org_status (organization_id, status),
  INDEX idx_priority (priority),
  INDEX idx_generated (generated_at)
) ENGINE=InnoDB;

CREATE TABLE ai_recommendation_feedback (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  recommendation_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  feedback_type VARCHAR(32) NOT NULL, -- accept, reject, modify, later
  comment TEXT,
  actual_outcome TEXT,
  value_realized DECIMAL(18,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recommendation_id) REFERENCES ai_recommendations(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_rec (recommendation_id)
) ENGINE=InnoDB;

CREATE TABLE ai_forecasts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  target VARCHAR(128) NOT NULL,
  horizon_days INT NOT NULL,
  granularity VARCHAR(16),
  model_used VARCHAR(128),
  algorithm VARCHAR(64),
  forecast_data JSON NOT NULL,
  confidence DECIMAL(4,3),
  mape DECIMAL(6,3),
  data_freshness DATETIME,
  data_coverage DECIMAL(4,3),
  known_limitations JSON,
  scenario_id BIGINT,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_org_target (organization_id, target),
  INDEX idx_generated (generated_at)
) ENGINE=InnoDB;

CREATE TABLE ai_briefings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  briefing_type VARCHAR(32) NOT NULL, -- daily, weekly, monthly
  briefing_date DATE NOT NULL,
  title VARCHAR(255),
  sections JSON NOT NULL,
  raw_prompt TEXT,
  generated_by_model VARCHAR(128),
  tokens_used INT,
  is_published BOOLEAN DEFAULT FALSE,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  UNIQUE KEY uniq_org_date_type (organization_id, briefing_date, briefing_type),
  INDEX idx_generated (generated_at)
) ENGINE=InnoDB;

CREATE TABLE ai_root_cause_analyses (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  issue_type VARCHAR(64),
  metric VARCHAR(128),
  observed_change TEXT,
  time_range_start DATETIME,
  time_range_end DATETIME,
  hypotheses JSON NOT NULL,
  data_quality_notes TEXT,
  limitations JSON,
  recommendations JSON,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_org_metric (organization_id, metric)
) ENGINE=InnoDB;

CREATE TABLE ai_scenarios (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  title VARCHAR(255),
  variable VARCHAR(128),
  change_type VARCHAR(32),
  change_value DECIMAL(18,4),
  projected_value DECIMAL(18,4),
  impacted_kpis JSON,
  risks JSON,
  opportunities JSON,
  confidence DECIMAL(4,3),
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_org (organization_id)
) ENGINE=InnoDB;

CREATE TABLE ai_benchmarks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  title VARCHAR(255),
  target_type VARCHAR(64), -- department, branch, region, school, hospital, etc.
  metric VARCHAR(128),
  peer_group JSON,
  is_cross_organization BOOLEAN DEFAULT FALSE,
  anonymized BOOLEAN DEFAULT FALSE,
  results JSON NOT NULL,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_org_type (organization_id, target_type)
) ENGINE=InnoDB;

CREATE TABLE ai_decision_timeline (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT,
  expected_outcome TEXT,
  actual_outcome TEXT,
  lessons_learned TEXT,
  decision_maker_id BIGINT,
  related_recommendation_id BIGINT,
  decision_date DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (decision_maker_id) REFERENCES users(id),
  FOREIGN KEY (related_recommendation_id) REFERENCES ai_recommendations(id),
  INDEX idx_org_date (organization_id, decision_date)
) ENGINE=InnoDB;

CREATE TABLE ai_goals (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  department_id BIGINT,
  title VARCHAR(255) NOT NULL,
  target_metric VARCHAR(128),
  target_value DECIMAL(18,4),
  unit VARCHAR(64),
  direction VARCHAR(16), -- increase, decrease, maintain
  start_date DATE,
  deadline DATE,
  current_progress DECIMAL(6,3),
  projected_achievement_date DATE,
  status VARCHAR(32) DEFAULT 'active',
  created_by BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (department_id) REFERENCES departments(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_org_status (organization_id, status)
) ENGINE=InnoDB;

CREATE TABLE ai_model_runs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  model_id BIGINT NOT NULL,
  target VARCHAR(128),
  horizon_days INT,
  backtest_period VARCHAR(64),
  mape DECIMAL(6,3),
  rmse DECIMAL(18,4),
  mae DECIMAL(18,4),
  coverage DECIMAL(4,3),
  training_time_ms INT,
  inference_time_ms INT,
  data_points_used INT,
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (model_id) REFERENCES ai_decision_models(id),
  INDEX idx_model (model_id)
) ENGINE=InnoDB;

CREATE TABLE ai_feedback (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  user_id BIGINT,
  engine_type VARCHAR(64),
  reference_id BIGINT,
  reference_table VARCHAR(64),
  rating INT,
  comment TEXT,
  tags JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_ref (reference_table, reference_id)
) ENGINE=InnoDB;
```

### 10.2 Extension to Existing Alert Table

Add columns to `dc_alerts`:
```sql
ALTER TABLE dc_alerts
  ADD COLUMN is_smart_alert BOOLEAN DEFAULT FALSE,
  ADD COLUMN ai_confidence DECIMAL(4,3),
  ADD COLUMN ai_explanation TEXT,
  ADD COLUMN ai_recommendation_id BIGINT,
  ADD FOREIGN KEY (ai_recommendation_id) REFERENCES ai_recommendations(id);
```

---

## 11. Testing Strategy

### Unit Tests
- Mock LLM gateway responses.
- Test each engine with synthetic data.
- Validate Pydantic schema outputs.
- Test prompt rendering and token limits.

### Integration Tests
- End-to-end recommendation generation workflow.
- Forecast backtest and model selection.
- Daily briefing generation and caching.
- Scenario simulation correctness.
- Benchmark engine with test datasets.

### API Tests
- All `/ai/decision/*` endpoints return valid schemas.
- RBAC enforcement for cross-department and cross-org data.
- Rate limiting and input validation.
- Error handling for missing/stale data.

### Model Tests
- Backtest each forecast model on historical data.
- Assert MAPE/RMSE within acceptable thresholds.
- Assert confidence intervals contain actuals at expected rate.
- Test model fallback when a model fails.

### Responsible AI Tests
- Confirm no unauthorized data leakage.
- Verify feedback is stored and linked.
- Verify confidence and limitations are always present.
- Test adversarial prompts for policy violations.

### Load Tests
- Simulate 100 concurrent executives requesting briefings.
- Simulate 1000 forecast generations per hour.
- Monitor Redis cache hit rate and DB connection pool.

---

## 12. Security Design

### RBAC
- Every engine call must receive the user's organization, department, and permission scope.
- Data retrieval is filtered by `organization_id` and role-based department access.
- Cross-organization benchmarks require explicit `benchmark.cross_org` permission and opt-in.

### Input Validation
- Pydantic schemas for all API requests.
- Strict allowlists for `target`, `metric`, `engine_type`, and `algorithm`.
- Max input lengths and sanitized string fields.
- Prompt injection guardrails: no user input directly embedded into system prompts without escaping.

### Output Controls
- Strip or redact sensitive fields before returning to UI.
- Audit all AI outputs in `ai_feedback` and engine tables.
- Log prompts, model used, tokens, and response metadata.

### Rate Limiting
- Per-user and per-organization limits.
- Expensive endpoints (`/forecasts`, `/scenarios`, `/root-cause`) have stricter limits.
- Token budgets per organization configurable by admin.

### Data Protection
- No PII in prompts unless necessary and approved.
- Optional local-only mode for sensitive organizations.
- Encryption at rest and in transit.

---

## 13. Monitoring

### Metrics
- AI request latency (p50, p95, p99).
- Engine success/failure rate.
- LLM token usage and cost per organization.
- Cache hit rate.
- Forecast accuracy (MAPE) over time.
- Recommendation acceptance/rejection rate.
- Smart alert precision/recall (via feedback).

### Logging
- Structured logs with correlation IDs.
- Audit log for AI decisions, recommendations, and feedback.
- Prompt and response metadata logged for debugging.

### Alerts
- Alert on AI engine failure rate > 1%.
- Alert on forecast accuracy degradation > threshold.
- Alert on LLM cost overrun.
- Alert on cache failure or Redis disconnect.

### Dashboards
- Grafana dashboard: AI Engine Health.
- Grafana dashboard: Forecast Accuracy.
- Grafana dashboard: Recommendation Effectiveness.

---

## 14. Deployment Strategy

### Service Deployment
- AI Decision Engine is deployed alongside existing FastAPI backend.
- Optional forecast worker service with heavier dependencies (`prophet`, `xgboost`, `scikit-learn`) can run as a separate container.
- LLM calls route through existing Phase 6 `AIGateway`.

### Environment Variables
```env
AI_DECISION_ENABLED=true
AI_DAILY_BRIEFING_TIME=06:00
AI_FORECAST_AUTO_SELECT=true
AI_FORECAST_DEFAULT_MODEL=auto
AI_RECOMMENDATION_MAX_RESULTS=10
AI_CACHE_TTL_BRIEFING=43200
AI_CACHE_TTL_FORECAST=3600
AI_CACHE_TTL_RECOMMENDATION=3600
AI_RATE_LIMIT_PER_MINUTE=30
AI_CROSS_ORG_BENCHMARKS=false
```

### Scaling
- Horizontal scaling of FastAPI workers behind load balancer.
- Celery workers scaled independently for background jobs.
- Redis cluster for caching and Celery broker.
- GPU nodes isolated in optional forecast model service.

### Rollout
1. Feature-flagged deployment.
2. Pilot with one organization.
3. Monitor metrics and feedback for 2 weeks.
4. Gradual rollout to all organizations.
5. Full production after accuracy and stability targets met.

---

## 15. Integration with Existing AEDIP

- **No redesign** of authentication, ETL, database core, RBAC, or dashboards.
- **Reuses** Phase 6 `AIGateway`, model providers, and AI conversation tables.
- **Extends** Phase 7 Part 2 database tables.
- **Feeds** Phase 7 Part 3 UI components with structured payloads.
- **Consumes** existing `DashboardDataService`, `SalesRepository`, `KpiService`, and ETL metadata.
- **Adds** new `/ai/decision/*` routes under existing FastAPI app.

---

## 16. Output Summary

1. **Complete AI Architecture** — high-level design and engine interactions.
2. **Prompt Architecture** — system prompt, engine prompts, JSON schemas.
3. **Service Layer** — package structure and service responsibilities.
4. **Workflow** — briefing, recommendation, forecast, alert, root cause workflows.
5. **API Specification** — endpoint list and example request/response.
6. **Model Management** — registry, selection, performance tracking, caching.
7. **Background Jobs** — Celery/APScheduler task schedule.
8. **Database Additions** — new table DDL and alert table extensions.
9. **Testing Strategy** — unit, integration, API, model, responsible AI, load tests.
10. **Security Design** — RBAC, validation, rate limiting, audit, data protection.
11. **Monitoring** — metrics, logging, dashboards, operational alerts.
12. **Deployment Strategy** — rollout, scaling, environment variables.

All specifications are production-ready and enterprise-grade. Ready for **Part 5 — implementation** when confirmed.
