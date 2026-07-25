# DataFlow — Enterprise Data Intelligence Platform

## Architecture Documentation

### Overview

DataFlow is an enterprise-grade data intelligence platform that integrates ETL pipelines,
analytics, AI-powered insights, and enterprise IAM into a unified system.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard (:8501)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Analytics │  │ ETL Mgmt │  │ AI Copilot│  │ Admin/IAM    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP (API Key / JWT)
┌───────────────────────▼─────────────────────────────────────────┐
│                    FastAPI Backend (:8000)                       │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐   │
│  │ Auth │  │ Sales│  │ ETL  │  │ AI   │  │Audit │  │ Org  │   │
│  │Router│  │Router│  │Router│  │Router│  │Router│  │Router│   │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Middleware: CORS | GZip | SecurityHeaders | RateLimit   │  │
│  │               RequestContext | RequestLogging            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────┘
                        │ SQLAlchemy ORM
┌───────────────────────▼─────────────────────────────────────────┐
│              Database (MySQL 8.0 / SQLite)                       │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐          │
│  │Sales │  │ ETL  │  │ AI   │  │ Auth │  │ Audit    │          │
│  │Tables│  │Tables│  │Tables│  │Tables│  │ Tables   │          │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Technology | Port | Description |
|-----------|-----------|------|-------------|
| Backend API | FastAPI + SQLAlchemy | 8000 | REST API with JWT auth, RBAC, rate limiting |
| Dashboard | Streamlit + Plotly | 8501 | Interactive analytics dashboard with AI Copilot |
| Database | MySQL 8.0 (prod) / SQLite (dev) | 3306 | Primary data store with indexed tables |
| ETL Engine | Custom pipeline with APScheduler | — | Data extraction, transformation, loading |
| AI Platform | Multi-provider (OpenAI, Gemini, Claude, etc.) | — | AI Gateway with caching, memory, audit |

### Security Architecture

- **Authentication**: JWT-based (access + refresh tokens), Argon2 password hashing
- **Authorization**: RBAC with granular permissions per module
- **API Security**: API key auth for legacy endpoints, JWT for enterprise endpoints
- **Rate Limiting**: In-memory sliding window (120 RPM default, configurable)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
- **CORS**: Configurable origins (no wildcard in production)
- **Input Validation**: Pydantic schemas, SQL parameterized queries, file upload validation
- **Audit Logging**: All sensitive operations logged with user, action, resource, IP

### Observability

- **Structured Logging**: JSON or text format with request/correlation IDs
- **Health Endpoints**: `/health` (liveness), `/ready` (readiness with subsystem checks)
- **Metrics**: `/metrics` endpoint with table counts
- **Request Tracing**: X-Request-ID and X-Correlation-ID headers

### Reliability

- **Retry**: Exponential backoff decorator for transient failures
- **Circuit Breaker**: Protects external service calls (AI providers)
- **Connection Pooling**: SQLAlchemy pool with pre-ping, recycling, overflow
- **Graceful Errors**: Global exception handler, consistent JSON error responses

### Deployment

- **Docker**: Multi-service docker-compose (API, Dashboard, MySQL)
- **CI/CD**: GitHub Actions with lint, format, and test stages
- **Health Checks**: Docker HEALTHCHECK + application-level endpoints
- **Environment Separation**: `.env` files, production validation at startup

### Semantic Engine (Industry Classification)

```
┌──────────────────────────────────────────────────────────┐
│                  Semantic Engine Pipeline                 │
│                                                          │
│  Upload → Column Profiling → Entity Matching → Voting    │
│                                                          │
│  Entity Matching:                                        │
│    - Exact synonym match (confidence=1.0)                │
│    - Partial synonym match (min len 5, threshold 0.65)   │
│    - Fuzzy match (min len 6, threshold 0.65)             │
│                                                          │
│  Weighted Scoring:                                       │
│    - Each entity has a weight (1.0–3.0)                  │
│    - Industry vote = sum(entity_weight × confidence)     │
│    - Universal entities (date, revenue) don't vote       │
│                                                          │
│  Tie-Breaking:                                           │
│    - If top-2 industries within 0.5 votes → "unknown"    │
│    - If best industry vote share < 40% → "unknown"       │
│    - "unknown" triggers user confirmation UI             │
│                                                          │
│  Dashboard Routing:                                      │
│    - Confidence ≥ 85% → auto-render industry dashboard   │
│    - Confidence < 85% → admin confirmation required      │
│    - "unknown" → generic fallback dashboard              │
└──────────────────────────────────────────────────────────┘
```

**Supported Industries**: Healthcare, Education, Banking, Agriculture, Government,
Retail, Church, NGO, Manufacturing, Insurance, Hospitality, Telecommunications.

**Entity Library**: ~60+ entities with industry-specific synonyms, weights, KPIs,
attributes, and relationships. Generic financial terms (balance, transaction, account)
are universal entities that map columns but don't vote for any industry.

### Module Map

| Module | Path | Description |
|--------|------|-------------|
| API | `api/` | FastAPI app, routers, schemas, legacy auth |
| Authentication | `authentication/` | JWT IAM: users, roles, permissions, sessions |
| ETL | `etl/` | Extract, transform, load, connectors, pipeline builder |
| Semantic Engine | `semantic/` | Entity library, classification, dashboard registry |
| Dashboard | `dashboard/` | Streamlit app, auth, semantic dashboard rendering |
| AI Platform | `ai/` | Multi-provider AI gateway, copilot, plugins |
| Analytics | `analytics/` | KPI aggregation, sales queries |
| Audit | `audit/` | Security event logging, audit trails |
| Enterprise | `enterprise/` | Subscriptions, demo data, branding |
| Organizations | `organizations/` | Org/department management |
| Notifications | `notifications/` | Email, SMS, WhatsApp, push |
| Scheduler | `scheduler/` | APScheduler-based report scheduling |
| Validation | `validation/` | Data quality checks, validation rules |
| Shared | `shared/` | Database, security, middleware, dependencies, exceptions |
| Database | `database/` | Legacy sales/pipeline_run repositories |
| Services | `services/` | ETL service, backup service |
| Config | `config.py` | Central config from env vars, production validation |

### Known Technical Debt

1. **`etl/extract.py`**: Hardcoded to CSV only — needs connector-based extraction like the pipeline builder
2. **`etl/load.py`**: Hardcoded to `sales` table — needs dynamic table routing
3. **`etl/transform.py`**: Retail-specific column assumptions (sales, quantity, discount) — needs generic cleaning
4. **`database/`**: Legacy `db_setup.py` uses a separate `Base` from `shared/database.py` — should be unified
5. **Rate limiter**: In-memory only — needs Redis for multi-worker deployments
6. **`docker-compose.yml`**: Dev compose uses SQLite, should have MySQL option for integration testing
