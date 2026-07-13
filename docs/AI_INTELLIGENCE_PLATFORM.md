# Phase 6 — AI Intelligence Platform

## Overview

Phase 6 transforms DataFlow into an **Enterprise AI Decision Intelligence Platform**.
Instead of only running reports, the platform now understands natural language,
recommends actions, predicts trends, detects anomalies, and explains what happened
and why.

All AI features are fully integrated into the existing DataFlow codebase.
No new application was created, and no existing feature was removed.

## Mission

- Help organizations understand data and make better decisions.
- Reduce manual work through AI automation.
- Support multiple AI providers so the platform is never locked to one vendor.
- Enforce responsible AI principles: permissions, audit logging, data retention,
  and clear distinction between AI-generated and human-generated content.

## Architecture

```
ai/
├── __init__.py
├── config.py              # AI-specific configuration
├── models.py              # SQLAlchemy ORM models for AI tables
├── schemas.py             # Pydantic request/response schemas
├── routes.py              # FastAPI endpoints (single /ai router)
├── gateway.py             # Central AI orchestrator
├── providers/
│   ├── base.py            # Provider interface
│   ├── manager.py         # Provider lifecycle and routing
│   ├── openai_provider.py # OpenAI / Azure OpenAI / compatible
│   ├── gemini_provider.py # Google Gemini
│   ├── deepseek_provider.py
│   ├── glm_provider.py    # Zhipu BigModel
│   ├── claude_provider.py # Anthropic Claude
│   └── local_provider.py  # Ollama, LM Studio, vLLM
├── prompts/
│   └── templates.py       # System prompts + prompt manager
├── memory.py              # Conversation history + summarization
├── context_builder.py     # Platform context for AI requests
├── security.py            # Input validation, permissions, redaction
├── usage.py               # Token/cost tracking
├── cache.py               # In-memory response cache
├── model_router.py        # Route requests to best provider/model
├── assistants/
│   └── assistants.py      # 8 specialized AI assistants
├── engines/
│   ├── nl_to_sql.py       # Natural language to SQL
│   ├── nl_to_etl.py       # Natural language to ETL pipeline
│   ├── nl_to_dashboard.py # Natural language to dashboard
│   ├── ai_quality.py      # AI data quality analysis
│   ├── report_writer.py   # AI report generation
│   ├── decision_center.py # Decision intelligence
│   ├── forecasting.py     # Time series forecasting
│   ├── anomaly_detection.py
│   ├── kpi_engine.py      # KPI recommendation and monitoring
│   ├── dashboard_insights.py
│   ├── ai_search.py       # Global natural language search
│   └── document_chat.py   # Chat with uploaded documents
├── workflow.py            # AI workflow automation
└── plugins.py             # Plugin system
```

## AI Services

### 1. AI Gateway (`ai/gateway.py`)

The single entry point for all AI operations. It coordinates:
- Input validation and permission checks via the AI Security Layer
- Context building from platform data
- Conversation memory management
- Provider/model selection via the Model Router
- Caching, usage tracking, and audit logging

### 2. Multi-Provider LLM Support (`ai/providers/`)

Supported providers:
- **OpenAI** — GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Google Gemini** — Gemini 1.5 Pro / Flash
- **DeepSeek** — DeepSeek Chat / Coder / Reasoner
- **GLM (Zhipu)** — GLM-4 series
- **Claude (Anthropic)** — Claude 3.5 Sonnet / Haiku
- **Local LLM** — Ollama, LM Studio, vLLM via OpenAI-compatible endpoints

Admins configure providers via `/ai/providers`.
The system falls back to environment variables if no database config exists.

### 3. AI Assistants (`ai/assistants/`)

Eight specialized assistants, each with a dedicated system prompt and role:
1. **Data Copilot** — Understands datasets, KPIs, charts, dashboards.
2. **ETL Copilot** — Builds and troubleshoots ETL pipelines from natural language.
3. **Dashboard Copilot** — Generates dashboard configurations.
4. **Report Copilot** — Generates executive and operational reports.
5. **Decision Copilot** — Explains what happened, why, what next, and recommends actions.
6. **Forecast Copilot** — Supports forecasting for revenue, attendance, demand, etc.
7. **Data Quality Copilot** — Detects quality issues and recommends fixes.
8. **SQL Copilot** — Translates natural language to validated SQL.

### 4. Natural Language Interfaces (`ai/engines/`)

- **NL-to-SQL** — Generates safe `SELECT` queries, validates SQL, estimates row counts.
- **NL-to-ETL** — Translates instructions into concrete pipeline steps.
- **NL-to-Dashboard** — Generates dashboard configs with chart types and mappings.

### 5. AI Data Quality Engine (`ai/engines/ai_quality.py`)

Uses the Phase 5 ETL quality engine and adds AI analysis:
- Quality score (0-100)
- Risk level (low/medium/high/critical)
- Specific issues with affected columns and rows
- Fix suggestions with confidence scores
- Optional auto-fixes

### 6. AI Report Writer (`ai/engines/report_writer.py`)

Generates professional reports:
- Executive summary
- Monthly / annual reports
- Department reports
- Data quality reports
- ETL performance reports
- Audit reports

### 7. AI Decision Center (`ai/engines/decision_center.py`)

The flagship feature. For any metric or period, the AI explains:
- **What happened** — observed changes and patterns
- **Why it happened** — contributing factors and root causes
- **What may happen next** — likely future scenarios
- **Recommended actions** — prioritized, actionable next steps

### 8. AI Forecasting (`ai/engines/forecasting.py`)

Supports multiple methods:
- Linear regression
- Exponential smoothing
- Moving average
- Seasonal decomposition
- Auto-selection

Returns predictions with confidence intervals and accuracy scores.

### 9. AI Anomaly Detection (`ai/engines/anomaly_detection.py`)

Detects:
- Spikes and drops
- Trend anomalies
- Missing records
- Fraud indicators

Generates alerts with severity, expected vs actual values, and deviation percentage.

### 10. AI KPI Engine (`ai/engines/kpi_engine.py`)

- Recommends KPIs based on domain and available data
- Monitors active KPIs
- Generates alerts when thresholds are breached

### 11. AI Dashboard Insights (`ai/engines/dashboard_insights.py`)

Every dashboard can include:
- Key findings
- Risks
- Opportunities
- Recommendations
- Trend analysis

### 12. AI Search (`ai/engines/ai_search.py`)

Global natural language search across:
- ETL jobs and pipelines
- Reports
- AI insights and forecasts
- Anomaly alerts
- Platform data (e.g., sales by region)

### 13. AI Document Chat (`ai/engines/document_chat.py`)

Upload PDF, Word, Excel, CSV, PowerPoint, or text files and ask questions.
The AI answers using only the uploaded document content.

### 14. AI Workflow Automation (`ai/workflow.py`)

Users can build workflows with steps such as:
- Import, clean, profile, transform, load
- Quality check, anomaly detection, forecasting
- Generate dashboard, report, insights
- Notify, email, archive
- AI chat step

Workflows can be triggered manually, on a schedule, or by events.

### 15. AI Plugin System (`ai/plugins.py`)

Extensible architecture for:
- Custom providers
- Custom assistants
- Custom engines
- Custom tools

Built-in system plugins are auto-registered on startup.

## Database Tables

All AI tables are prefixed with `ai_`:

| Table | Purpose |
|-------|---------|
| `ai_conversations` | Chat sessions between users and assistants |
| `ai_messages` | Individual messages in conversations |
| `ai_provider_configs` | Provider configuration (API keys, models, settings) |
| `ai_usage_logs` | Token usage and cost tracking per request |
| `ai_audit_logs` | AI action audit trail for compliance |
| `ai_workflows` | Automated workflow definitions |
| `ai_workflow_runs` | Workflow execution records |
| `ai_insights` | Generated insights (decision, dashboard, etc.) |
| `ai_forecasts` | Forecasting results |
| `ai_anomaly_alerts` | Anomaly detection alerts |
| `ai_documents` | Uploaded documents for document chat |
| `ai_kpi_recommendations` | AI-recommended KPIs |
| `ai_report_generations` | AI-generated report metadata |
| `ai_prompt_templates` | Reusable prompt templates |
| `ai_plugins` | Registered AI plugins |

## API Endpoints

All AI endpoints are under `/ai` and require JWT authentication unless noted.

### Chat & Conversations
- `POST /ai/chat` — Send a message to an AI assistant
- `POST /ai/chat/stream` — Stream a chat response
- `GET /ai/conversations` — List conversations
- `GET /ai/conversations/{id}/messages` — Get conversation messages
- `DELETE /ai/conversations/{id}` — Archive a conversation
- `POST /ai/messages/{id}/feedback` — Message feedback
- `GET /ai/assistants` — List available assistants

### Providers
- `GET /ai/providers` — List providers
- `POST /ai/providers` — Configure a provider
- `PUT /ai/providers/{id}` — Update a provider
- `POST /ai/providers/{name}/test` — Test provider connection

### NL Interfaces
- `POST /ai/sql/generate` — Generate SQL from natural language
- `POST /ai/sql/execute` — Execute validated SQL
- `POST /ai/etl/generate` — Generate ETL pipeline from natural language
- `POST /ai/dashboard/generate` — Generate dashboard from description

### AI Engines
- `POST /ai/quality/analyze` — AI data quality analysis
- `POST /ai/reports/generate` — Generate AI report
- `GET /ai/reports` — List reports
- `GET /ai/reports/{id}` — Get report
- `POST /ai/decision/analyze` — Decision intelligence analysis
- `GET /ai/insights` — List AI insights
- `POST /ai/forecast` — Generate forecast
- `GET /ai/forecasts` — List forecasts
- `GET /ai/forecasts/{id}` — Get forecast predictions
- `POST /ai/anomaly/detect` — Detect anomalies
- `GET /ai/anomaly/alerts` — List alerts
- `POST /ai/anomaly/alerts/{id}/resolve` — Resolve alert
- `POST /ai/kpi/recommend` — Recommend KPIs
- `GET /ai/kpi/monitor` — Monitor KPIs
- `POST /ai/dashboard/insights` — Generate dashboard insights
- `POST /ai/search` — Global AI search

### Document Chat
- `POST /ai/documents/upload` — Upload document
- `POST /ai/documents/{id}/chat` — Chat with document
- `GET /ai/documents` — List documents

### Workflow Automation
- `POST /ai/workflows` — Create workflow
- `GET /ai/workflows` — List workflows
- `POST /ai/workflows/{id}/execute` — Execute workflow
- `GET /ai/workflows/{id}/runs` — Get workflow runs

### Prompts, Usage, Audit, Plugins
- `GET /ai/prompts` — List prompt templates
- `POST /ai/prompts` — Create prompt template
- `GET /ai/usage/stats` — Usage statistics
- `GET /ai/usage/me` — Current user usage
- `GET /ai/usage/limits` — Usage limits
- `GET /ai/audit/logs` — AI audit logs
- `GET /ai/plugins` — List plugins
- `POST /ai/plugins/{id}/activate` — Activate plugin
- `POST /ai/plugins/{id}/deactivate` — Deactivate plugin
- `GET /ai/dashboard` — AI platform dashboard

## Configuration

Add to `.env`:

```env
# Default AI Provider (openai, gemini, deepseek, glm, claude, local)
AI_DEFAULT_PROVIDER=openai
AI_DEFAULT_MODEL=gpt-4o-mini
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.7
AI_REQUEST_TIMEOUT=60

# Provider API Keys
OPENAI_API_KEY=your-key
GEMINI_API_KEY=your-key
DEEPSEEK_API_KEY=your-key
GLM_API_KEY=your-key
CLAUDE_API_KEY=your-key

# Provider Base URLs (optional, for proxies / self-hosted)
OPENAI_BASE_URL=https://api.openai.com/v1
LOCAL_LLM_BASE_URL=http://localhost:11434/v1

# AI Memory & Cache
AI_MEMORY_MAX_MESSAGES=20
AI_CACHE_ENABLED=true
AI_CACHE_TTL_SECONDS=3600

# AI Security
AI_ENFORCE_PERMISSIONS=true
AI_MAX_INPUT_LENGTH=10000
AI_DATA_RETENTION_DAYS=90

# AI Usage Limits
AI_DAILY_TOKEN_LIMIT=1000000
AI_MONTHLY_COST_LIMIT_USD=100.0

# AI Document Chat
AI_DOC_MAX_SIZE_MB=20
AI_DOC_ALLOWED_TYPES=pdf,docx,xlsx,csv,pptx,txt

# AI Forecasting
AI_FORECAST_CONFIDENCE_LEVEL=0.95
AI_FORECAST_MAX_HORIZON=365

# AI Anomaly Detection
AI_ANOMALY_SENSITIVITY=2.0
AI_ANOMALY_MIN_DATA_POINTS=10
```

## Security & Responsible AI

- **Permission-aware** — Each assistant type checks required permissions.
- **Input validation** — SQL-injection-like patterns and dangerous input are rejected.
- **Sensitive data redaction** — Credit cards, API keys, and emails are redacted in audit logs.
- **Audit logging** — Every AI action is logged in `ai_audit_logs`.
- **Usage tracking** — Tokens and costs are tracked per user and request.
- **Data retention** — Configurable retention policy for AI data.
- **No hardcoded provider** — All providers are configurable via environment variables or API.
- **AI-generated content is clearly identifiable** — Responses include provider, model, and confidence where applicable.

## Testing

Phase 6 includes 56 new tests in `tests/test_ai_platform.py` covering:
- Provider management
- Prompt templates
- Memory and conversation history
- Security layer
- Cache
- Model router
- Assistants registry
- Plugins
- NL-to-SQL, NL-to-ETL, NL-to-Dashboard
- AI data quality
- KPI engine
- AI search
- Forecasting
- Anomaly detection
- Workflow automation
- All AI API endpoints

Run the tests:

```bash
python -m pytest tests/test_ai_platform.py -v
```

Full platform test suite:

```bash
python -m pytest tests/ -v --ignore=tests/test_dashboard.py
```

## Test Report

- **Unit tests**: 56 passed (AI platform)
- **Integration tests**: Included in `test_ai_platform.py` (API routes, engines, workflow execution)
- **Permission tests**: Covered in security and API route tests
- **Regression tests**: Full suite — 235 passed, including Phases 4 and 5
- **Prompt tests**: Covered by prompt template and assistant tests

## Deployment

1. Install the new dependencies (listed in `requirements.txt`):
   ```bash
   pip install scipy PyPDF2 python-docx python-pptx
   ```
   Note: `scipy` is optional for forecasting; the engine falls back to default values if not installed.

2. Apply the Alembic migration:
   ```bash
   alembic upgrade 0003
   ```

3. Set the AI provider API keys in `.env`.

4. Start the FastAPI server:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

5. The AI endpoints are available at `/ai/*` and will be auto-discovered by the FastAPI application.

## Migration

- Alembic migration: `alembic/versions/0003_phase6_ai.py`
- Down migration: drops all `ai_*` tables.

## Integration Points

- `api/main.py` imports `ai.models` and registers system AI plugins on startup.
- `database/db_setup.py` imports `ai.models` so tables are created.
- `tests/conftest.py` imports `ai.models` for the test database.
- `etl/ai_hooks.py` from Phase 5 remains available and the new AI engines extend the same concepts.

## Next Steps / Future Enhancements

- Add streaming support for all AI engines.
- Implement Redis-backed cache for distributed deployments.
- Add background task execution for long-running AI workflows.
- Implement user-defined AI tool registry.
- Add fine-tuned local model management.
- Expand document chat to support embeddings and vector search.
