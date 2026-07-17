# AEDIP Quick Start Guide

## Get Running in 10 Minutes

### Option 1: Docker (Recommended)

```bash
# 1. Clone and configure
git clone <repo-url> && cd etl_project
cp .env.example .env
# Edit .env: set JWT_SECRET_KEY, API_KEY, DB credentials

# 2. Launch all services
docker-compose up -d

# 3. Access
# API:      http://localhost:8000
# Dashboard: http://localhost:8501
```

### Option 2: Local Development

```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 2. Database
alembic upgrade head

# 3. Start API
uvicorn api.main:app --reload --port 8000

# 4. Start Dashboard (new terminal)
streamlit run dashboard/app.py
```

### First Steps After Installation

1. **Log in** to the dashboard at `http://localhost:8501`
2. **Complete the onboarding wizard** (first-time users)
3. **Choose a data source** (Live Database or Upload File)
4. **Explore dashboards** — KPIs, charts, and data tables
5. **Ask the AI Copilot** a question about your data
6. **Export filtered data** to CSV

### Industry Packs

Pick a template pack that matches your industry:
- SME, Education, Healthcare, Church, Government, NGO

Each pack includes pre-built dashboards, KPIs, ETL templates, and AI prompts.

### Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /ready` | Readiness check |
| `GET /metrics` | Platform metrics |
| `GET /docs` | Interactive API docs (Swagger) |
| `GET /platform/industry-packs` | List industry packs |
| `GET /platform/templates` | Browse template marketplace |
| `POST /platform/search` | Enterprise search |
