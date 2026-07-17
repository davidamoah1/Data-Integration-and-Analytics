# Developer Guide

## Project Structure

```
etl_project/
├── ai/                 # AI Intelligence Platform
│   ├── assistants/     # AI assistant definitions
│   ├── gateway.py      # Central AI request orchestrator
│   ├── models.py       # AI SQLAlchemy models
│   ├── plugins/        # AI plugin system
│   ├── routes.py       # AI API endpoints
│   └── services/       # AI business logic
├── api/                # FastAPI application
│   ├── auth.py         # API key authentication
│   ├── main.py         # App setup, middleware, endpoints
│   └── schemas.py      # Pydantic response schemas
├── audit/              # Audit logging
├── authentication/     # Enterprise IAM (JWT, RBAC)
├── database/           # Legacy database models & repositories
├── dashboard/          # Streamlit dashboard
│   ├── app.py          # Main dashboard application
│   ├── auth.py         # Dashboard session auth
│   ├── copilot.py      # AI Copilot chat panel
│   ├── styles.py       # CSS themes
│   └── utils.py        # Formatting & sanitization
├── docs/               # Documentation
├── etl/                # ETL pipeline engine
│   ├── file_security.py # File upload validation
│   ├── logging_config.py # Structured logging
│   ├── models.py       # ETL SQLAlchemy models
│   └── routes.py       # ETL API endpoints
├── monitoring/         # Health checks & observability
├── organizations/      # Organization management
├── shared/             # Shared infrastructure
│   ├── context.py      # Request-scoped context vars
│   ├── database.py     # SQLAlchemy engine & Base
│   ├── dependencies.py # FastAPI auth dependencies
│   ├── middleware.py   # Security, rate limit, logging middleware
│   ├── resilience.py   # Retry & circuit breaker utilities
│   └── security.py     # Password hashing, JWT, validation
├── tests/              # Test suite
├── config.py           # Configuration management
├── Dockerfile          # Container definition
├── docker-compose.yml  # Multi-service orchestration
├── pyproject.toml      # Project metadata, linting, testing config
└── requirements.txt    # Python dependencies
```

## Development Setup

1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. `pip install ruff black pytest`
4. Copy `.env.example` to `.env` and configure for SQLite dev

## Code Quality

- **Linter**: `ruff check .`
- **Formatter**: `black .`
- **Tests**: `pytest -q`
- All three run in CI via GitHub Actions

## Adding a New API Endpoint

1. Define the Pydantic schema in `api/schemas.py`
2. Add the endpoint in `api/main.py` or a router module
3. Use `Depends(get_api_key)` for legacy auth or `Depends(require_permissions([...]))` for RBAC
4. Add tests in `tests/`
5. Run `ruff check . && black --check . && pytest -q`

## Adding a New Database Model

1. Define the model in the appropriate `models.py` file
2. Import it in `api/main.py` lifespan so it registers with `Base.metadata`
3. Add indexes on frequently queried columns
4. Run `Base.metadata.create_all(engine)` to create tables
5. For production migrations, use Alembic

## Adding a New AI Assistant

1. Define the assistant in `ai/assistants/assistants.py`
2. Create a prompt template in the database
3. The AI Gateway will automatically route to it based on `assistant_type`
