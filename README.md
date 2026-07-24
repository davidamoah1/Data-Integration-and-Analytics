# DataFlow — Enterprise Data Intelligence Platform (AEDIP) v1.0.0

A production-ready ETL, analytics, and AI platform that ingests any tabular
dataset, automatically maps business semantics, and generates governed KPIs and
dashboards. It ships with a FastAPI REST layer, Streamlit dashboard, AI Copilot,
job scheduling, audit logging, and multi-tenant IAM (SQLite for dev, MySQL for
production).

---

## Project Structure

```
etl_project/
├── config.py                     # Central configuration with .env support
├── pyproject.toml                # Linting (ruff) + formatting (black) config
├── requirements.txt              # Pinned Python dependencies
├── Dockerfile                    # Container deployment
├── docker-compose.yml            # Multi-service (API + Dashboard + MySQL)
├── .env.example                  # Template for environment variables
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline (lint, test, Docker)
├── alembic/                      # Database migrations
├── dataset/                      # Sample datasets
├── data/                         # Raw + processed data
├── etl/                          # ETL engine (extract, transform, load, routes)
├── pipeline/                     # ETL orchestrator
├── scheduler/                    # APScheduler-based scheduling
├── database/                     # ORM models, repositories, migrations
├── services/                     # ETL service, dashboard data service
├── api/                          # FastAPI REST API (main, auth, schemas)
├── dashboard/                    # Streamlit dashboard (app, auth, charts, styles, copilot)
├── ai/                           # AI Intelligence Platform (gateway, assistants, plugins, routes)
├── analytics/                    # Analytics domain (dashboards, widgets, KPIs, alerts)
├── enterprise/                   # Enterprise platform (industry packs, routes, models)
├── authentication/               # IAM (users, roles, permissions, JWT, sessions)
├── organizations/                # Organization management
├── audit/                        # Audit logging
├── shared/                       # Shared utilities (security, database, middleware, response)
├── monitoring/                   # Health checks
├── tests/                        # Comprehensive test suite (430+ tests)
├── logs/                         # Application logs
└── docs/                         # Documentation (audit report, architecture)
```

---

## Quick Start

### 1. Clone and install
```bash
git clone https://github.com/davidamoah1/Data-Integration-and-Analytics.git
cd Data-Integration-and-Analytics
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# For local dev, set DB_TYPE=sqlite in .env
```

### 3. Run the ETL pipeline
```bash
python pipeline/run_pipeline.py
```

### 4. Start the API backend
```bash
# Set environment variables for local dev
# On Windows PowerShell:
$env:DB_TYPE="sqlite"; $env:SQLITE_DB_PATH="etl_app.db"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
API docs: http://localhost:8000/docs

### 5. Start the dashboard
```bash
# In a new terminal with same env vars:
$env:DB_TYPE="sqlite"; $env:SQLITE_DB_PATH="etl_app.db"
streamlit run dashboard/app.py --server.port 8501
```
Dashboard: http://localhost:8501

Default credentials: `admin` / `admin123`, `viewer` / `viewer123`

### 6. Run the scheduler (optional)
```bash
python scheduler/scheduler.py
```

### 7. Docker deployment
```bash
docker compose up -d
```
Services:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- MySQL: localhost:3306

---

## Running Tests
```bash
# Set test environment
$env:DB_TYPE="sqlite"; $env:SQLITE_DB_PATH="test_etl.db"; $env:JWT_SECRET_KEY="test-secret-min-32-chars-long"; $env:CORS_ORIGINS="http://localhost:8501"
pytest tests/ -v
```

## Linting & Formatting
```bash
ruff check .
black --check .
black .
```

---

## Features

### ETL Pipeline
- CSV/Excel extraction with encoding detection
- Data cleaning, transformation, validation
- Batch database loading with duplicate detection
- Scheduled execution with retry logic
- Pipeline run history and metadata tracking

### Dashboard
- Session-based authentication with RBAC (admin/viewer)
- Live database queries or file upload mode
- Interactive filters (region, category, date range)
- KPI cards, 7 chart types, heatmap, data table
- CSV export of filtered data
- AI Copilot with natural language queries
- Industry pack templates (Retail, Finance, Education, Healthcare)
- Onboarding wizard and quick-start checklist
- Responsive dark theme with accessibility support

### REST API
- FastAPI with Pydantic schemas and OpenAPI docs
- JWT-based authentication (access + refresh tokens)
- API key backward compatibility
- Sales CRUD, KPIs, filter options, pipeline management
- Enterprise IAM: users, roles, permissions, organizations
- AI endpoints: chat, assistants, quality scoring, anomaly detection, forecasting
- Analytics endpoints: dashboards, widgets, KPIs, alerts
- Rate limiting, security headers, request logging, GZip
- Health, readiness, and metrics endpoints

### AI Intelligence Platform
- Multi-provider support (OpenAI, Gemini, DeepSeek, GLM, Claude, local LLM)
- AI Copilot with context-aware data analysis
- AI assistants with custom system prompts
- Data quality scoring and recommendations
- Anomaly detection with configurable sensitivity
- Time-series forecasting with confidence intervals
- Document chat (PDF, DOCX, XLSX, PPTX)
- Permission-aware AI access control
- Usage limits (daily tokens, monthly cost)

### Security
- Argon2 password hashing
- JWT with configurable expiry
- Password policy enforcement
- Account lockout after failed attempts
- RBAC with fine-grained permissions
- XSS sanitization in dashboard
- Security headers (CSP, X-Frame-Options, etc.)
- Rate limiting per client IP
- Audit logging for all critical actions
- File upload size limits and type validation

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | (required) | `sqlite` or `mysql` |
| `SQLITE_DB_PATH` | `database/etl_database.db` | SQLite database path |
| `MYSQL_HOST` | (empty) | MySQL server host |
| `MYSQL_PORT` | `3306` | MySQL server port |
| `MYSQL_DATABASE` | (empty) | MySQL database name |
| `MYSQL_USER` | (empty) | MySQL username |
| `MYSQL_PASSWORD` | (empty) | MySQL password |
| `JWT_SECRET_KEY` | (required in prod) | JWT signing secret |
| `JWT_ACCESS_EXPIRE_MINUTES` | `30` | Access token expiry |
| `JWT_REFRESH_EXPIRE_DAYS` | `7` | Refresh token expiry |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `RATE_LIMIT_RPM` | `120` | Rate limit per IP per minute |
| `API_KEY` | (change in prod) | Legacy API key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `text` | `text` or `json` |
| `AI_DEFAULT_PROVIDER` | `openai` | Default AI provider |
| `AI_DEFAULT_MODEL` | `gpt-4o-mini` | Default AI model |
| `OPENAI_API_KEY` | (empty) | OpenAI API key |
| `AUTH_ADMIN_PASSWORD` | `admin123` | Dashboard admin password |
| `AUTH_VIEWER_PASSWORD` | `viewer123` | Dashboard viewer password |

See `.env.example` for the complete list.

---

## Architecture

### ETL Pipeline
1. **Extract**: Reads raw CSV/Excel data from configured path
2. **Transform**: Cleans duplicates, fixes data types, standardizes dates, validates quality
3. **Load**: Batch-inserts into database (skips duplicates by order_id)
4. **Schedule**: APScheduler runs daily with retry logic and metadata tracking

### Dashboard
- **Auth**: Session-based login with role-based access
- **Data**: Live database or file upload with auto-column detection
- **Caching**: Streamlit cache for DB queries (5-10 min TTL)
- **Charts**: Plotly with dark theme (revenue trends, categories, regional, heatmap)
- **AI**: Copilot panel with natural language data queries
- **Export**: CSV download of filtered data

### REST API
- **Framework**: FastAPI with Pydantic schemas
- **Auth**: JWT Bearer tokens + legacy API key
- **Middleware**: CORS, GZip, rate limiting, security headers, request logging
- **Docs**: Auto-generated Swagger UI at `/docs`

### Database Layer
- **ORM**: SQLAlchemy 2.0 with typed models
- **Repository Pattern**: SalesRepository, PipelineRunRepository
- **Migrations**: Alembic for schema management
- **Connection Pooling**: Pool size, recycle, pre-ping for MySQL

### AI Platform
- **Gateway**: Multi-provider abstraction layer
- **Context Builder**: Data-aware context injection
- **Plugins**: Extensible plugin system for custom AI capabilities
- **Security**: Permission-aware AI access control

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.10+ |
| Data handling | Pandas |
| Database | SQLite / MySQL + SQLAlchemy |
| Scheduling | APScheduler |
| Dashboard | Streamlit |
| Charts | Plotly |
| REST API | FastAPI + Pydantic |
| AI | OpenAI / Gemini / DeepSeek / Claude |
| Auth | JWT + Argon2 |
| Testing | Pytest (270+ tests) |
| Linting | Ruff + Black |
| CI/CD | GitHub Actions + Docker |
| Monitoring | Health checks + log rotation |

---

## API Endpoints Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/signup` | Public self-registration |
| POST | `/auth/logout` | User logout |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |
| GET/POST | `/users` | List/create users |
| GET/PUT/DELETE | `/users/{id}` | User CRUD |
| GET/POST | `/roles` | Role management |
| GET/POST | `/organizations` | Organization management |
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/metrics` | Platform metrics |
| GET | `/api/v1/sales` | Sales data with filters |
| GET | `/api/v1/kpis` | KPI aggregation |
| GET | `/api/v1/filters` | Filter options |
| POST | `/api/v1/pipeline/trigger` | Trigger ETL pipeline |
| GET | `/api/v1/pipeline/runs` | Pipeline run history |
| POST | `/ai/chat` | AI chat |
| GET | `/ai/assistants` | List AI assistants |
| GET | `/analytics/dashboards` | List dashboards |
| GET | `/platform/industry-packs` | List industry packs |

Full docs at http://localhost:8000/docs

---

*DataFlow v2.0.0 — Enterprise Data Intelligence Platform (AEDIP)*
