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
