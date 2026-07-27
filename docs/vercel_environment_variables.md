# Vercel Environment Variables

This document lists the environment variables required for a successful Vercel deployment of the DataFlow Enterprise Data Intelligence Platform.

## How to set variables in Vercel

1. Go to your project in the Vercel dashboard.
2. Navigate to **Settings → Environment Variables**.
3. Add each variable below.
4. Redeploy the project.

---

## Required Variables

These variables must be set for the application to work in production.

### Database

| Variable | Example | Purpose |
|----------|---------|---------|
| `DB_TYPE` | `mysql` | Must be `mysql` for production. |
| `MYSQL_HOST` | `your-db-host.com` or `127.0.0.1` | MySQL server hostname. |
| `MYSQL_PORT` | `3306` | MySQL server port. |
| `MYSQL_DATABASE` | `aedip` | Database name. |
| `MYSQL_USER` | `aedip_user` | Database username. |
| `MYSQL_PASSWORD` | `strong-db-password` | Database password. |

### Security

| Variable | Example | Purpose |
|----------|---------|---------|
| `JWT_SECRET_KEY` | generate with `openssl rand -hex 32` | Used to sign and verify JWT tokens. |
| `SUPER_ADMIN_EMAIL` | `admin@dataflow.io` | Email of the default super admin account. |
| `SUPER_ADMIN_PASSWORD` | `StrongPassword123!` | Password for the default super admin account. |

### Frontend / API Routing

| Variable | Example | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `/api` | Base URL for API calls from the browser. On Vercel this must be `/api` so requests are routed to the Python function. |
| `CORS_ORIGINS` | `https://dataflow-demo.vercel.app` | Comma-separated list of allowed origins. Must include your Vercel deployment domain. |

---

## Optional Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR. |
| `LOG_FORMAT` | `text` | Set to `json` for structured logs. |
| `LOG_PATH` | *(empty)* | Leave empty on Vercel for stdout-only logging. |
| `DISABLE_STARTUP_TASKS` | *(empty)* | Auto-set to `true` on Vercel. Skips DB migrations, seeding, scheduler startup. |
| `DISABLE_CONFIG_VALIDATION` | *(empty)* | Set to `true` only for debugging. Never set in production. |
| `SEED_DEMO_DATA` | `false` | Set to `true` to seed demo data on first startup. Not recommended on Vercel. |
| `AI_DEFAULT_PROVIDER` | `openai` | Default AI provider. |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key for AI features. |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key. |
| `DEEPSEEK_API_KEY` | *(empty)* | DeepSeek API key. |
| `CLAUDE_API_KEY` | *(empty)* | Anthropic Claude API key. |
| `REDIS_URL` | *(empty)* | Redis connection string for caching. |
| `CACHE_ENABLED` | `true` | Enable/disable caching. |

---

## Vercel-Specific Notes

- `NEXT_PUBLIC_API_URL` must be `/api` when both frontend and backend are deployed on the same Vercel project. If the backend is hosted separately (e.g., on a VPS), set the full URL here.
- Do **not** set `LOG_PATH` on Vercel unless you have a writable persistent volume, which serverless functions do not have.
- `DISABLE_STARTUP_TASKS` is automatically set to `true` by `api/index.py` for the Vercel environment. Database migrations and seeding must be run separately from a long-running environment.

---

## Example `.env` for Local Development

```bash
# Database
DB_TYPE=sqlite
SQLITE_DB_PATH=database/etl_database.db

# Security
JWT_SECRET_KEY=local-dev-secret-change-in-production
SUPER_ADMIN_EMAIL=admin@dataflow.io
SUPER_ADMIN_PASSWORD=Admin@12345

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
```

## Example Production Environment Variables for Vercel

```bash
DB_TYPE=mysql
MYSQL_HOST=your-hostinger-mysql-host.com
MYSQL_PORT=3306
MYSQL_DATABASE=aedip
MYSQL_USER=aedip_user
MYSQL_PASSWORD=your-strong-password

JWT_SECRET_KEY=your-64-character-random-hex-key
SUPER_ADMIN_EMAIL=admin@dataflow.io
SUPER_ADMIN_PASSWORD=YourStrongAdminPassword123!

NEXT_PUBLIC_API_URL=/api
CORS_ORIGINS=https://your-project.vercel.app

SEED_DEMO_DATA=false
```
