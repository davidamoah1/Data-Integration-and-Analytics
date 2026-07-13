# DataFlow — Enterprise Data Intelligence Platform

A production-ready ETL pipeline and business intelligence platform that
automatically extracts, transforms, and loads sales data into a database
(SQLite for dev, MySQL for production), with a Streamlit dashboard,
REST API, scheduling, and monitoring.

---

## Project Structure

```
etl_project/
├── config.py                     # Central configuration with .env support
├── pyproject.toml                # Linting (ruff) + formatting (black) config
├── requirements.txt              # Pinned Python dependencies
├── Dockerfile                    # Container deployment
├── .env.example                  # Template for environment variables
├── .gitignore
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── dataset/
│   ├── Superstore.csv            # Primary dataset (9,994 rows)
│   └── Financial_Sales_Data.csv  # Secondary sample dataset
├── data/
│   ├── raw/                      # Place custom CSV files here
│   └── processed/                # Cleaned data saved here automatically
├── etl/
│   ├── __init__.py
│   ├── extract.py                # CSV extraction
│   ├── transform.py              # Data cleaning, transformation, validation
│   ├── load.py                   # Database loading with batch inserts
│   └── logging_config.py         # Shared logging with rotation
├── pipeline/
│   ├── __init__.py
│   └── run_pipeline.py           # ETL orchestrator
├── scheduler/
│   ├── __init__.py
│   └── scheduler.py              # APScheduler-based daily scheduler
├── database/
│   ├── __init__.py
│   ├── db_setup.py               # SQLAlchemy ORM models + table creation
│   ├── repositories.py           # Repository pattern (SalesRepository, PipelineRunRepository)
│   ├── migrate_to_mysql.py       # SQLite → MySQL migration script
│   └── etl_database.db           # SQLite database (local dev)
├── services/
│   ├── __init__.py
│   ├── etl_service.py            # ETL service with retry logic + metadata tracking
│   └── dashboard_data_service.py # Dashboard data service (DB + file modes)
├── api/
│   ├── __init__.py
│   ├── main.py                   # FastAPI REST API
│   ├── schemas.py                # Pydantic request/response schemas
│   └── auth.py                   # API key authentication
├── dashboard/
│   ├── __init__.py
│   ├── app.py                    # Streamlit dashboard (main entry)
│   ├── styles.py                 # CSS themes and chart layouts
│   ├── charts.py                 # Chart components
│   ├── utils.py                  # Formatting + sanitization utilities
│   └── auth.py                   # Dashboard authentication
├── monitoring/
│   ├── __init__.py
│   └── health_check.py           # Health checks + monitoring
├── tests/
│   ├── __init__.py
│   ├── test_extract.py           # Extract tests
│   ├── test_transform.py         # Transform + validation tests
│   ├── test_load.py              # Load tests
│   ├── test_repository.py        # Repository pattern tests
│   ├── test_dashboard_service.py # Dashboard data service tests
│   └── test_api.py               # API endpoint tests
├── logs/
│   └── pipeline.log
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/etl_project.git
cd etl_project
```

### 2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` to set your database connection, data paths, and schedule time.
Defaults work out-of-the-box with SQLite and the included dataset.

### 4. Run the pipeline manually
```bash
python pipeline/run_pipeline.py
```

### 5. Start the dashboard
```bash
streamlit run dashboard/app.py
```
Default credentials: admin/admin123, viewer/viewer123

### 6. Run the scheduler (optional, for automation)
```bash
python scheduler/scheduler.py
```

### 7. Start the REST API (optional)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
API docs available at http://localhost:8000/docs

### 8. Run health check (optional)
```bash
python monitoring/health_check.py
```

### 9. Docker deployment (optional)
```bash
docker build -t dataflow .
docker run -p 8000:8000 --env-file .env dataflow
```

---

## Running Tests
```bash
pytest tests/ -v
```

## Linting & Formatting
```bash
ruff check .
black --check .
black .
```

---

## Environment Variables

| Variable            | Default                  | Description                         |
|---------------------|--------------------------|-------------------------------------|
| `RAW_DATA_PATH`     | `dataset/Superstore.csv` | Path to source CSV                  |
| `PROCESSED_DATA_PATH`| `data/processed/cleaned_data.csv` | Cleaned output path       |
| `DB_TYPE`           | `sqlite`                 | `sqlite` or `mysql`                |
| `SQLITE_DB_PATH`    | `database/etl_database.db` | SQLite database path              |
| `MYSQL_HOST`        | (empty)                  | MySQL server host                  |
| `MYSQL_PORT`        | `3306`                   | MySQL server port                  |
| `MYSQL_DATABASE`    | (empty)                  | MySQL database name                |
| `MYSQL_USER`        | (empty)                  | MySQL username                     |
| `MYSQL_PASSWORD`    | (empty)                  | MySQL password                     |
| `LOG_PATH`          | `logs/pipeline.log`      | Log file path                      |
| `LOG_LEVEL`         | `INFO`                   | Logging level                      |
| `PIPELINE_RUN_TIME` | `08:00`                  | Daily schedule time (24h format)   |
| `API_HOST`          | `0.0.0.0`                | API server host                    |
| `API_PORT`          | `8000`                   | API server port                    |
| `API_KEY`           | `change-this-in-production` | API authentication key          |
| `CORS_ORIGINS`      | `*`                      | Comma-separated allowed origins    |
| `AUTH_ADMIN_PASSWORD`| `admin123`             | Dashboard admin password           |
| `AUTH_VIEWER_PASSWORD`| `viewer123`           | Dashboard viewer password          |

---

## Architecture

### ETL Pipeline
1. **Extract**: Reads raw CSV data from the configured `RAW_DATA_PATH`
2. **Transform**: Cleans duplicates, fixes data types, standardizes dates, validates data quality
3. **Load**: Batch-inserts new records into the database (skips duplicates by `order_id`)
4. **Schedule**: APScheduler runs the pipeline daily with retry logic and metadata tracking

### Dashboard
- **Authentication**: Session-based login with role-based access (admin/viewer)
- **Data Sources**: Toggle between live database queries and file upload
- **Caching**: Streamlit cache for DB queries (5-10 min TTL)
- **Charts**: Revenue trends, category breakdowns, regional analysis, profit margins, heatmap
- **Export**: Download filtered data as CSV
- **Security**: XSS sanitization, file upload size limits (50MB)

### REST API
- **Framework**: FastAPI with Pydantic schemas
- **Auth**: API key via `X-API-Key` header or `?api_key` query parameter
- **Endpoints**: Sales CRUD, KPIs, filter options, pipeline trigger/status, health check
- **Docs**: Auto-generated Swagger UI at `/docs`

### Database Layer
- **ORM**: SQLAlchemy 2.0 with typed models (Date types, indexes, timestamps)
- **Repository Pattern**: `SalesRepository` and `PipelineRunRepository`
- **Migration**: `migrate_to_mysql.py` for SQLite → MySQL data migration
- **Connection Pooling**: Pool size, recycle, and pre-ping for MySQL

---

## Tech Stack

| Layer         | Tool                        |
|---------------|-----------------------------|
| Language      | Python 3.10+                |
| Data handling | Pandas                      |
| Database      | SQLite / MySQL + SQLAlchemy |
| Scheduling    | APScheduler                 |
| Dashboard     | Streamlit                   |
| Charts        | Plotly                      |
| REST API      | FastAPI + Pydantic          |
| Testing       | Pytest + TestClient         |
| Linting       | Ruff + Black                |
| Config        | python-dotenv (.env files)  |
| CI/CD         | GitHub Actions + Docker     |
| Monitoring    | Health checks + log rotation|

---

*DataFlow — Enterprise Data Intelligence Platform*
