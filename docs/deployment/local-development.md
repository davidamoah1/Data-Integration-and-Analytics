# Local Development

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Guide for setting up the local development environment.

## Scope

All steps to run DataFlow locally.

## Audience

Developers and new contributors.

---

## 1. Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | >=20.0.0 |
| PostgreSQL | 14+ |
| Git | Latest |

## 2. Backend Setup

```bash
# Clone repository
git clone https://github.com/davidamoah1/Data-Integration-and-Analytics.git
cd Data-Integration-and-Analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/dataflow"
export JWT_SECRET_KEY="your-secret-key"
export CORS_ORIGINS="http://localhost:3000"

# Start backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

## 4. Database Setup

```bash
# Create database
createdb dataflow

# Tables auto-created on backend startup
# Default data (roles, permissions, super admin) auto-seeded
```

## 5. Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | — | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | — | Yes | JWT signing secret |
| `CORS_ORIGINS` | — | No | Comma-separated allowed origins |
| `SEED_DEMO_DATA` | `false` | No | Enable demo data |
| `DEBUG` | — | No | Enable debug mode |

## 6. Development Workflow

1. Backend runs with `--reload` (auto-restart on changes)
2. Frontend runs with hot module replacement
3. Database tables auto-created on backend startup
4. Default roles and permissions auto-seeded

## Related Documents

- [docker.md](docker.md) — Docker deployment
- [vercel.md](vercel.md) — Vercel deployment
- [environments.md](environments.md) — Environment configuration
