# AI Gap Analysis — Phase 12.4

## Current State

### Existing AI Infrastructure

| Component | File | Status |
|-----------|------|--------|
| AI Gateway | `ai/gateway.py` | Central orchestrator with provider routing, memory, caching, security, audit |
| Context Builder | `ai/context_builder.py` | Builds platform context per assistant type |
| Prompt Manager | `ai/prompts/templates.py` | 8 system prompts with DB override support |
| Provider Manager | `ai/providers/manager.py` | 6 providers (OpenAI, Gemini, DeepSeek, GLM, Claude, Local) |
| Model Router | `ai/model_router.py` | Task-to-model mapping with cost optimization |
| Security Layer | `ai/security.py` | Input validation, RBAC, SQL injection prevention, data redaction |
| Memory | `ai/memory.py` | Conversation history with summarization |
| Cache | `ai/cache.py` | TTL-based response caching |
| Usage Tracker | `ai/usage.py` | Token/cost tracking |
| Assistants | `ai/assistants/assistants.py` | 8 assistants (data, ETL, dashboard, report, decision, forecast, quality, SQL) |

### Existing AI Engines

| Engine | File | Capabilities |
|--------|------|-------------|
| Decision Center | `ai/engines/decision_center.py` | WHAT/WHY/NEXT/ACTIONS framework, hardcoded to `sales` table |
| Forecasting | `ai/engines/forecasting.py` | Linear, exponential, moving average, seasonal — with confidence intervals |
| Anomaly Detection | `ai/engines/anomaly_detection.py` | Z-score, trend breaks, missing records — with severity levels |
| Report Writer | `ai/engines/report_writer.py` | Executive, monthly, annual, quality, ETL reports — hardcoded to `sales` |
| Dashboard Insights | `ai/engines/dashboard_insights.py` | Key findings, risks, opportunities — hardcoded to `sales` |
| KPI Engine | `ai/engines/kpi_engine.py` | KPI recommendation and monitoring — hardcoded to `sales` |
| NL-to-SQL | `ai/engines/nl_to_sql.py` | Natural language to SQL translation |
| NL-to-ETL | `ai/engines/nl_to_etl.py` | Natural language to ETL pipeline |
| NL-to-Dashboard | `ai/engines/nl_to_dashboard.py` | Natural language to dashboard config |
| AI Quality | `ai/engines/ai_quality.py` | AI-powered data quality analysis |
| AI Search | `ai/engines/ai_search.py` | Global search across platform |
| Document Chat | `ai/engines/document_chat.py` | Chat with uploaded documents |

### Existing Frontend

| Component | File | Status |
|-----------|------|--------|
| AI Chat Page | `frontend/app/(app)/ai/page.tsx` | Basic chat with suggested questions, no streaming, no context |
| AI Service | `frontend/services/ai/aiService.ts` | Chat, conversations, insights, forecast, anomaly — minimal |
| Streamlit Copilot | `dashboard/copilot.py` | Inline chat panel with assistant selection |

---

## Gap Analysis

### 1. Context Engine — MAJOR GAPS

**Current:** `ContextBuilder` builds context per assistant type but:
- Does NOT include current dataset context (DataFrame, columns, profile, semantic mappings)
- Does NOT include dashboard state (active filters, selected KPIs, current view)
- Does NOT include user role/organization context for personalized responses
- Does NOT include KPI definitions from the new KPI Intelligence Engine
- Does NOT include industry knowledge from the semantic layer
- Does NOT include conversation intent history

**Required:** A unified context engine that aggregates:
- Organization + user role + permissions
- Active dataset (schema, profile, quality, semantic mappings)
- Dashboard state (filters, KPIs, charts, layout)
- Industry knowledge (KPIs, business rules, entities)
- Conversation history with intent tracking

### 2. Prompt Orchestration — MODERATE GAPS

**Current:** Single monolithic system prompt per assistant type. No specialized prompt pipelines.

**Required:** Modular prompt pipelines for:
- Executive summaries (structured output with sections)
- KPI explanations (metric → formula → drivers → context)
- Trend analysis (period comparison → direction → rate → significance)
- Root cause analysis (observation → hypothesis → evidence → conclusion)
- Forecasting (data summary → method → predictions → interpretation → limitations)
- Risk analysis (risk identification → severity → probability → mitigation)
- Data quality explanations (issue → impact → root cause → fix recommendation)
- Dashboard assistance (intent → action → parameters → execution)
- ETL assistance (description → pipeline steps → validation → execution)

### 3. Executive Summary Engine — MAJOR GAPS

**Current:** `DecisionCenterEngine` generates analysis but:
- Hardcoded to `sales` table (SQLite-specific SQL)
- No integration with KPI Intelligence Engine
- No integration with Dashboard Engine metadata
- No industry-aware summaries
- No period-over-period comparison
- No growth/decline calculation
- No confidence scoring methodology

**Required:** Executive summary engine that:
- Works with any dataset via semantic mappings
- Integrates KPI Intelligence Engine for metric detection
- Calculates period-over-period changes
- Identifies growth and decline drivers
- Flags risks and opportunities
- Provides confidence level with methodology
- Generates industry-specific insights

### 4. Root Cause Analysis — MISSING

**Current:** `DecisionCenterEngine` includes a "WHY" section but relies entirely on LLM reasoning without structured analysis.

**Required:**
- Contribution analysis (which segments drove the change)
- Correlation detection (which factors co-vary with the metric)
- Period comparison (what changed between periods)
- Segment decomposition (break down metric by dimensions)
- Statistical significance testing
- Evidence-backed explanations with data references

### 5. Forecasting — PARTIAL

**Current:** `ForecastingEngine` has 4 methods with confidence intervals but:
- Requires explicit `source_type` and `source_config` (connector-based)
- No integration with semantic layer (auto-detect date/value columns)
- No multi-horizon support (short/medium/long term)
- No assumption documentation
- No model limitation disclosure
- AI interpretation is generic, not industry-aware

**Required:**
- Auto-detect date and value columns from semantic mappings
- Multi-horizon forecasts (7-day, 30-day, 90-day)
- Documented assumptions (trend continuation, seasonality, data quality)
- Model limitations (data requirements, accuracy caveats)
- Industry-aware interpretation

### 6. Anomaly Detection — PARTIAL

**Current:** `AnomalyDetectionEngine` detects spikes, drops, trends, missing records but:
- Requires explicit connector configuration
- No integration with semantic layer
- No "why" explanation for anomalies
- No industry-specific thresholds
- No historical pattern comparison

**Required:**
- Auto-detect metric and date columns from semantic mappings
- Explain WHY each anomaly was flagged (context, comparison, deviation)
- Industry-specific sensitivity (e.g., healthcare readmission vs. retail sales)
- Historical baseline comparison
- Impact assessment (how many records/sales affected)

### 7. Recommendation Engine — MISSING

**Current:** Recommendations are generated ad-hoc by the LLM in decision center responses. No structured recommendation engine.

**Required:**
- Industry-specific recommendation templates
- Action → expected impact → priority → feasibility
- Data-driven triggers (e.g., low inventory → restock recommendation)
- Integration with KPI thresholds for automated alerts
- Recommendation history and tracking

### 8. Natural Language Analytics — PARTIAL

**Current:** NL-to-SQL engine exists but:
- No period comparison support
- No ranking/top-N support
- No trend analysis translation
- No churn/retention analysis
- No spending anomaly detection

**Required:**
- Intent detection (compare, rank, trend, explain, summarize)
- Period-aware query construction
- Multi-dimensional analysis (group by, filter, aggregate)
- Result interpretation (not just data, but explanation)

### 9. Report Generation — PARTIAL

**Current:** `AIReportWriter` generates reports but:
- Hardcoded to `sales` table
- No chart embedding
- No KPI table generation
- No methodology section
- No appendix with detailed data
- Only Markdown output (no PDF, DOCX, HTML)

**Required:**
- Works with any dataset via semantic mappings
- Includes KPI tables from KPI Intelligence Engine
- Embeds chart descriptions/references
- Methodology section (data sources, analysis methods, limitations)
- Appendix with detailed data tables
- Export to PDF, DOCX, HTML

### 10. Frontend AI Experience — MODERATE GAPS

**Current:** Basic chat with suggested questions. Missing:
- No streaming responses
- No conversation history persistence
- No insight cards (structured AI output rendering)
- No report preview
- No context selection (dataset, dashboard, filters)
- No assistant type selection
- No error recovery suggestions

**Required:**
- Streaming responses (SSE or WebSocket)
- Conversation history with search
- Structured insight cards (findings, risks, recommendations)
- Report preview with export buttons
- Context selector (dataset, dashboard, time range)
- Assistant type selector
- Loading states with skeleton UI
- Error handling with retry suggestions

### 11. Security & Governance — MODERATE GAPS

**Current:** `AISecurityLayer` has input validation, RBAC, SQL injection prevention, data redaction. Missing:
- No per-dataset access control (AI can access any table)
- No confidence level disclosure in responses
- No assumption vs. analysis distinction
- No AI interaction logging for compliance

**Required:**
- Per-dataset RBAC (AI respects dataset-level permissions)
- Confidence level in every response
- Clear distinction between data-backed analysis and assumptions
- Full audit trail of AI interactions (input, output, context, model)

### 12. Performance — MODERATE GAPS

**Current:** Response caching exists. Missing:
- No context retrieval optimization (gathers all data every time)
- No prompt token optimization (context truncated at 3000 chars)
- No response latency monitoring
- No AI failure rate tracking

**Required:**
- Lazy context loading (only gather relevant data for the query)
- Token budget management (prioritize critical context)
- Response latency monitoring with alerts
- AI failure rate tracking with retry logic

---

## Duplicate Code

| Issue | Location | Fix |
|-------|----------|-----|
| Sales-hardcoded SQL | `decision_center.py`, `report_writer.py`, `dashboard_insights.py`, `kpi_engine.py` | Replace with semantic-aware data gathering |
| Sales summary query | Repeated in 4+ engines | Extract to shared `DataGatherer` utility |
| JSON parsing pattern | Repeated in all engines | Extract to shared `ResponseParser` utility |
| Gateway instantiation | Each engine creates its own `AIGateway(db)` | Use dependency injection |

## Improvement Opportunities

1. **Unified Context Engine** — Single source of truth for AI context, replacing per-assistant context builders
2. **Prompt Pipeline Architecture** — Modular, composable prompt components instead of monolithic prompts
3. **Semantic-Aware Data Gathering** — Use semantic mappings to dynamically query any dataset
4. **Structured Response Parsing** — Consistent JSON schema for all AI responses
5. **Recommendation Templates** — Industry-specific recommendation patterns with impact estimation
6. **Multi-Format Report Export** — PDF, DOCX, HTML with chart embedding
7. **Streaming Frontend** — Real-time AI response rendering
8. **AI Usage Analytics** — Dashboard for AI usage, cost, latency, and failure rates

---

## Implementation Priority

| Priority | Step | Description |
|----------|------|-------------|
| P0 | Step 2 | AI Context Engine — foundation for all other steps |
| P0 | Step 3 | Prompt Orchestration — structured prompt pipelines |
| P0 | Step 4 | Executive Summary Engine — flagship feature |
| P1 | Step 5 | Root Cause Analysis — structured analysis framework |
| P1 | Step 6 | Forecasting enhancement — semantic-aware, multi-horizon |
| P1 | Step 7 | Anomaly Detection enhancement — explainable anomalies |
| P1 | Step 8 | Recommendation Engine — actionable, industry-specific |
| P2 | Step 9 | NL Analytics — intent detection, period comparison |
| P2 | Step 10 | Report Generation — multi-format, chart embedding |
| P2 | Step 11 | Frontend AI Experience — streaming, insight cards |
| P2 | Step 12 | Security & Governance — per-dataset RBAC, audit trail |
| P3 | Step 13 | Performance — lazy context, token optimization |
| P3 | Step 14 | Testing |
| P3 | Step 15 | Documentation |
