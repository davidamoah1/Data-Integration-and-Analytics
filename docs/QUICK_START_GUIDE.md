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

### Demo Credentials

On first launch, the platform auto-seeds a demo organization with 5 users:

| Email | Password | Role |
|-------|----------|------|
| `demo.admin@democorp.com` | `DemoAdmin1!` | Admin |
| `demo.analyst@democorp.com` | `DemoAnalyst1!` | Analyst |
| `demo.manager@democorp.com` | `DemoManager1!` | Viewer |
| `demo.engineer@democorp.com` | `DemoEngineer1!` | Analyst |
| `demo.viewer@democorp.com` | `DemoViewer1!` | Viewer |

### First Steps After Installation

1. **Log in** to the dashboard at `http://localhost:8501`
2. **Complete the onboarding wizard** (8-step guided tour for first-time users)
3. **Choose a data source** (Live Database or Upload File)
4. **Select an industry pack** in the sidebar (SME, Healthcare, Education, Government, Church, NGO)
5. **Explore dashboards** — sector-specific KPIs, charts, and data tables
6. **Ask the AI Copilot** a question about your data
7. **Generate a report** using AI or export filtered data to CSV
8. **Check subscription status** — navigate to Administration → Organization

### Industry Packs

Pick a template pack that matches your industry:
- **SME** — Sales, inventory, customers, profit, cash flow
- **Education** — Students, attendance, exams, fees, tuition
- **Healthcare** — Patients, billing, insurance, departments, bed occupancy
- **Church** — Membership, attendance, giving, offerings, outreach
- **Government** — Revenue, budget, projects, procurement, contractors
- **NGO** — Donors, projects, beneficiaries, grants, funding sources

Each pack includes pre-built dashboards, KPIs, ETL templates, AI prompts, and **unique dashboard layouts** with sector-specific chart types.

### Navigation

Use the sidebar **Navigation** radio to switch between:

| Page | Description |
|------|-------------|
| **Dashboard** | Main analytics view with KPIs, charts, filters, and AI Copilot |
| **Administration** | Org profile, branding, user management, roles, audit logs |
| **Support** | Submit feedback, bug reports, feature requests, view diagnostics |
| **Observability** | System health, login activity, audit logs, security events |

### Subscription Plans

| Plan | Users | Dashboards | AI Queries/mo | Upload Limit |
|------|-------|------------|----------------|--------------|
| Free Trial | 5 | 10 | 100 | 50MB |
| Starter | 10 | 25 | 500 | 200MB |
| Professional | 50 | 100 | 5,000 | 1GB |
| Enterprise | 500 | 1,000 | 50,000 | 10GB |
| Government | 1,000 | 2,000 | 100,000 | 50GB |

Manage your subscription via **Administration → Organization → Subscription Status** or via API at `POST /platform/subscription/upgrade`.

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
| `GET /platform/subscription/plans` | List subscription plans |
| `GET /platform/subscription/current` | Current org subscription |
| `POST /platform/subscription/upgrade` | Upgrade plan |
| `POST /platform/demo/seed` | Seed demo data |
| `GET /audit/logs` | Audit logs (admin) |
| `GET /audit/security-logs` | Security events (admin) |
