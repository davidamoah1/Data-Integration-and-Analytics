# DataFlow — Africa's Data Intelligence Platform (AEDIP) v2.0.0

> **Built in Africa, for the world.**

DataFlow is a production-ready ETL, analytics, and AI platform that ingests any
tabular dataset, automatically maps business semantics, and generates governed
KPIs and dashboards. It ships with a FastAPI REST layer, Streamlit dashboard,
AI Copilot, job scheduling, audit logging, multi-tenant IAM, Africa Intelligence
Layer, and performance infrastructure for millions of records.

## Why DataFlow?

- **Upload any spreadsheet → get insights in minutes** — no data engineer required
- **Understands African data** — currencies (GHS, NGN, KES, ZAR), regions, industries
- **AI-powered** — semantic column mapping, anomaly detection, forecasting, natural language queries
- **Enterprise-grade** — RBAC, audit logs, multi-tenant, Argon2, JWT, rate limiting
- **Scales to millions** — Redis caching, background workers, chunked queries, connection pooling
- **1,150+ tests passing** — production-validated with comprehensive CI/CD

---

## Project Structure

```
etl_project/
├── config.py                     # Central configuration with .env support
├── pyproject.toml                # Linting (ruff) + formatting (black) config
├── requirements.txt              # Pinned Python dependencies
├── Dockerfile                    # Container deployment
├── docker-compose.yml            # Dev: API + Dashboard + MySQL + Redis + Worker
├── docker-compose.prod.yml       # Prod: + Nginx + SSL + Health checks
├── .env.example                  # Template for environment variables
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── static/index.html             # Beautiful landing page
├── alembic/                      # Database migrations
├── dataset/                      # Sample datasets
├── demo_datasets/                # 12 industry demo datasets (CSV)
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
├── africa_intelligence/          # Africa Layer (country profiles, recognizer, currency, industry)
├── performance/                  # Queue, workers, cache, DB optimization, routes
├── platform_features/            # Connector marketplace, workflow automation, notifications
├── semantic/                     # Semantic mapping engine
├── validation/                   # Data validation engine with approval workflow
├── shared/                       # Shared utilities (security, database, middleware, response)
├── monitoring/                   # Health checks
├── tests/                        # Comprehensive test suite (1,150+ tests)
├── logs/                         # Application logs
└── docs/                         # Full documentation (60+ documents)
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
- Redis: localhost:6379
- Worker: Background task processor

### 8. Production deployment
```bash
docker compose -f docker-compose.prod.yml up -d
```
Adds Nginx reverse proxy with SSL, health checks, and resource limits.
See `docs/DEPLOYMENT.md` for details.

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

### Semantic Mapping Engine
- AI-powered column recognition (100+ patterns)
- Auto-maps abbreviations: `rev` → `revenue`, `dt` → `date`, `amt` → `amount`
- Business domain detection (sales, HR, finance, operations)
- Confidence scoring for each mapping
- Africa-aware pattern matching

### Dashboard
- Session-based authentication with RBAC (admin/viewer)
- Live database queries or file upload mode
- Interactive filters (region, category, date range)
- KPI cards, 7 chart types, heatmap, data table
- CSV export of filtered data
- AI Copilot with natural language queries
- 12 industry pack templates (Retail, Banking, Healthcare, Education, Government, NGO, etc.)
- Onboarding wizard and quick-start checklist
- Responsive dark theme with accessibility support
- PWA support for mobile
- Sector-specific dashboards
- Semantic mapping dashboard
- Validation dashboard with approval workflow

### REST API
- FastAPI with Pydantic schemas and OpenAPI docs
- JWT-based authentication (access + refresh tokens)
- API key backward compatibility
- Sales CRUD, KPIs, filter options, pipeline management
- Enterprise IAM: users, roles, permissions, organizations, departments
- AI endpoints: chat, assistants, quality scoring, anomaly detection, forecasting
- Analytics endpoints: dashboards, widgets, KPIs, alerts
- Africa intelligence: country profiles, currency conversion, industry mapping
- Performance: queue stats, cache management, DB optimization, index management
- Platform features: connectors, workflows, notifications, report builder, universal search
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
- Executive Decision Center with AI-powered recommendations

### Africa Intelligence Layer
- **4 country profiles**: Ghana, Nigeria, Kenya, South Africa
- **Currency converter**: GHS, NGN, KES, ZAR, USD, EUR, GBP with live rates
- **Industry mapper**: Agriculture, Mining, Telecommunications, Banking, Oil & Gas, Tourism
- **Column recognizer**: Detects African data patterns (regions, phone formats, names)
- **Education data**: Universities, programs, degree patterns
- **Healthcare data**: Hospitals, diseases, insurance patterns
- **Agriculture data**: Crops, livestock, rainfall, fertilizer patterns
- Integrated into semantic mapping pipeline

### Performance & Global Scale
- **Task Queue**: Multi-priority (high, ETL, normal, reports, notifications, low) with Redis backend + in-memory fallback
- **Background Workers**: Dynamic scaling (2-20 workers), health monitoring, graceful shutdown
- **Redis Caching**: TTL-based, namespace isolation, pattern invalidation, `@cached` decorator
- **DB Optimization**: 10 critical indexes, chunked queries for millions of rows, slow query tracking
- **Connection Pooling**: Configurable pool size, timeout, recycle, max overflow
- **Dead Letter Queue**: Permanently failed tasks with retry tracking

### Enterprise Features
- Multi-tenant architecture with organization isolation
- 5 system roles: super_admin, org_admin, analyst, manager, viewer
- Custom role creation with fine-grained permissions
- White-label branding (logo, colors, custom domain)
- Template marketplace with one-click install
- Collaboration and activity tracking

### Platform Features
- **Connector Marketplace**: 12+ data connectors (CSV, Excel, MySQL, PostgreSQL, API, S3, etc.)
- **Workflow Automation**: Visual workflow builder with triggers and conditions
- **Notification Center**: Email, in-app, webhook notifications with templates
- **Report Builder**: Drag-and-drop report creation with scheduling
- **Universal Search**: Search across all data, dashboards, and reports
- **Dashboard Builder**: Custom dashboard creation with widgets
- **Formula/KPI Engine**: Custom KPI formulas with expression parser
- **Plugin Framework**: Extensible plugin system for custom integrations

### Security
- Argon2 password hashing
- JWT with configurable expiry
- Password policy enforcement
- Account lockout after failed attempts
- RBAC with fine-grained permissions (30+ permissions)
- XSS sanitization in dashboard
- Security headers (CSP, X-Frame-Options, etc.)
- Rate limiting per client IP
- Audit logging for all critical actions
- File upload size limits and type validation
- Session management with revocation
- Login history and activity tracking

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
| `REDIS_URL` | (empty) | Redis connection URL for caching/queues |
| `CACHE_ENABLED` | `true` | Enable Redis caching layer |
| `CACHE_DEFAULT_TTL` | `300` | Default cache TTL in seconds |
| `CACHE_KEY_PREFIX` | `aedip` | Cache key prefix for namespacing |
| `WORKER_MIN_WORKERS` | `2` | Minimum background workers |
| `WORKER_MAX_WORKERS` | `20` | Maximum background workers |
| `WORKER_SCALE_UP_THRESHOLD` | `10` | Queue depth to trigger scale-up |
| `WORKER_SCALE_DOWN_THRESHOLD` | `2` | Queue depth to trigger scale-down |
| `CHUNK_SIZE_DEFAULT` | `5000` | Default chunk size for batch queries |
| `POOL_SIZE` | `10` | Database connection pool size |
| `POOL_TIMEOUT` | `30` | Connection pool timeout |
| `POOL_RECYCLE` | `3600` | Connection recycle interval (seconds) |
| `MAX_OVERFLOW` | `20` | Max overflow connections beyond pool size |

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

### Africa Intelligence Layer
- **Country Profiles**: Ghana, Nigeria, Kenya, South Africa with regions, currencies, industries
- **Column Recognizer**: Detects African data patterns in uploaded datasets
- **Currency Converter**: Real-time conversion between GHS, NGN, KES, ZAR, USD, EUR, GBP
- **Industry Mapper**: Maps African industries to standardized categories

### Performance Infrastructure
- **Task Queue**: Redis-backed multi-priority queue with retry and dead letter
- **Worker Pool**: Dynamic scaling with health monitoring
- **Cache Layer**: Redis caching with `@cached` decorator and pattern invalidation
- **DB Optimization**: Index management, chunked queries, slow query tracking

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.10+ |
| Data handling | Pandas |
| Database | SQLite / MySQL + SQLAlchemy |
| Caching | Redis + in-memory fallback |
| Task Queue | Redis-backed multi-priority queue |
| Scheduling | APScheduler |
| Dashboard | Streamlit + Plotly |
| REST API | FastAPI + Pydantic |
| AI | OpenAI / Gemini / DeepSeek / Claude / Local LLM |
| Auth | JWT + Argon2 |
| Testing | Pytest (1,150+ tests) |
| Linting | Ruff + Black |
| CI/CD | GitHub Actions + Docker |
| Monitoring | Health checks + log rotation + observability |
| Deployment | Docker Compose + Nginx + SSL |

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
| GET | `/africa/countries` | List African country profiles |
| POST | `/africa/convert-currency` | Convert between currencies |
| GET | `/performance/overview` | Performance stats overview |
| GET | `/performance/cache/stats` | Cache hit/miss statistics |
| DELETE | `/performance/cache/clear` | Clear entire cache |
| GET | `/performance/db/stats` | Database statistics |
| POST | `/performance/db/ensure-indexes` | Create critical DB indexes |

Full interactive docs at http://localhost:8000/docs

---

## Demo Datasets

DataFlow ships with 12 industry-specific demo datasets in `demo_datasets/`:

| Dataset | Records | Use Case |
|---------|---------|----------|
| Agriculture | 200 | Crop yields, livestock, rainfall |
| Banking | 200 | Accounts, transactions, loans |
| Church | 200 | Members, donations, events |
| Education | 200 | Students, grades, enrollment |
| Government | 200 | Programs, budgets, citizens |
| Healthcare | 200 | Patients, diagnoses, billing |
| Hospitality | 200 | Bookings, revenue, occupancy |
| Insurance | 200 | Policies, claims, premiums |
| Manufacturing | 200 | Production, defects, supply chain |
| NGO | 200 | Beneficiaries, projects, funding |
| Retail | 200 | Sales, products, regions |
| Telecommunications | 200 | Subscribers, usage, churn |

Plus Africa-specific datasets for Ghana, Nigeria, Kenya, and South Africa.

---

## Documentation

Comprehensive documentation is in the `docs/` directory:

| Document | Description |
|----------|-------------|
| `QUICK_START_GUIDE.md` | Get running in 5 minutes |
| `ARCHITECTURE.md` | System architecture overview |
| `API_ENDPOINTS.md` | Full API endpoint reference |
| `DEVELOPER_GUIDE.md` | Development setup and conventions |
| `END_USER_GUIDE.md` | End-user dashboard guide |
| `ADMINISTRATOR_GUIDE.md` | Admin and configuration guide |
| `DEPLOYMENT.md` | Production deployment guide |
| `DATABASE_ARCHITECTURE.md` | Database design and schema |
| `AUTH_ARCHITECTURE.md` | Authentication and RBAC design |
| `RBAC_PERMISSION_MATRIX.md` | Role-permission matrix |
| `TROUBLESHOOTING.md` | Common issues and solutions |
| `PHASE9_PERFORMANCE_ENGINEERING.md` | Performance architecture |
| `PHASE9_SECURITY_HARDENING.md` | Security hardening details |
| `PHASE9_OBSERVABILITY_CENTER.md` | Monitoring and observability |
| `PHASE9_BACKUP_DISASTER_RECOVERY.md` | Backup and DR procedures |

---

## Testing

```bash
# Full test suite (1,150+ tests)
pytest tests/ -v

# Run specific module tests
pytest tests/test_performance.py -v
pytest tests/test_africa_intelligence.py -v
pytest tests/test_rbac.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

Test categories:
- **ETL Pipeline**: Extraction, transformation, loading, validation
- **Authentication**: JWT, RBAC, sessions, password policy
- **AI Platform**: Chat, assistants, quality scoring, anomaly detection
- **Africa Intelligence**: Country profiles, currency, industry mapping
- **Performance**: Queue, workers, cache, DB optimization
- **API Endpoints**: All REST endpoints with auth checks
- **Dashboard**: Data service, charts, onboarding
- **Enterprise**: Organizations, templates, branding

---

## Roadmap

- [x] Phase 1-3: Core ETL, Dashboard, REST API
- [x] Phase 4: Enterprise IAM (JWT, RBAC, Organizations)
- [x] Phase 5: AI Intelligence Platform
- [x] Phase 6: Analytics & Alerting
- [x] Phase 7: Executive Decision Center
- [x] Phase 8: Platform Features (Connectors, Workflows, Reports, Search)
- [x] Phase 9: Enterprise Hardening (Security, Observability, Backup, Performance)
- [x] Phase 10: Performance & Global Scale (Workers, Queue, Redis, DB Optimization)
- [x] Phase 11: Final Product Polish (UI, Docs, Marketing, Demo Data, Investor Materials)
- [ ] Phase 12: Mobile apps and offline-first sync

---

## License

Proprietary. © 2025 DataFlow (AEDIP). All rights reserved.

---

*DataFlow v2.0.0 — Africa's Data Intelligence Platform (AEDIP)*
*Built in Africa, for the world.*
