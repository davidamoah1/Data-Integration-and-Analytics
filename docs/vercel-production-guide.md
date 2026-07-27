# Vercel Production Deployment Guide

This guide explains how to deploy the DataFlow Enterprise Data Intelligence Platform to Vercel after the deployment fixes.

---

## Architecture on Vercel

- **Frontend**: Next.js 14 application served from `frontend/`.
- **Backend**: FastAPI Python Serverless Function exposed via `api/index.py`.
- **Routing**: `vercel.json` routes all `/api/*` requests to the Python function and all other traffic to Next.js.

---

## Prerequisites

1. A Vercel account.
2. Vercel CLI installed locally (`npm i -g vercel`).
3. A MySQL database (recommended: Hostinger MySQL or any MySQL 8+ provider).
4. The repository pushed to GitHub.

---

## Required Environment Variables

Add these in the Vercel dashboard (**Project Settings → Environment Variables**) or via the CLI.

### Database (required for production)

| Variable | Value | Example |
|----------|-------|---------|
| `DB_TYPE` | `mysql` | `mysql` |
| `MYSQL_HOST` | Database host | `127.0.0.1` or your Hostinger host |
| `MYSQL_PORT` | Database port | `3306` |
| `MYSQL_DATABASE` | Database name | `aedip` |
| `MYSQL_USER` | Database user | `aedip_user` |
| `MYSQL_PASSWORD` | Database password | `strong-password` |

### Security (required for production)

| Variable | Value | Example |
|----------|-------|---------|
| `JWT_SECRET_KEY` | >= 32 character random string | generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | Allowed origins | `https://dataflow-yourproject.vercel.app` |
| `SUPER_ADMIN_EMAIL` | Default admin email | `admin@dataflow.io` |
| `SUPER_ADMIN_PASSWORD` | Default admin password | `StrongAdminPassword123!` |

### Frontend

| Variable | Value | Example |
|----------|-------|---------|
| `NEXT_PUBLIC_API_URL` | Must be `/api` on Vercel | `/api` |

### Optional but Recommended

| Variable | Value | Example |
|----------|-------|---------|
| `LOG_FORMAT` | `json` for structured logs | `json` |
| `LOG_PATH` | Leave empty for stdout-only logs | *(empty)* |
| `DISABLE_STARTUP_TASKS` | `false` for long-running servers; `true` is auto-set on Vercel | `false` |
| `DISABLE_CONFIG_VALIDATION` | Do not set in production | *(empty)* |

---

## Local Development

### Backend only

```bash
# Windows
$env:DB_TYPE="sqlite"
$env:SQLITE_DB_PATH="database/etl_database.db"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

The frontend will proxy API calls to `http://localhost:8000` when `NEXT_PUBLIC_API_URL` is set to that value. For local development:

```bash
# In a .env.local inside frontend/
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Deploy to Vercel

### 1. Link project

```bash
vercel link
```

### 2. Pull environment variables

```bash
vercel env pull .env
```

### 3. Deploy

```bash
vercel --prod
```

Vercel will:

1. Build the Next.js frontend from `frontend/package.json`.
2. Build the Python Serverless Function from `api/index.py`.
3. Route `/api/*` to the Python function and all other routes to Next.js.

---

## First-Time Database Setup

Because Vercel Serverless Functions are stateless and short-lived, **database migrations and seeding must be run outside the function cold start**.

### Option A: Run migrations from your local machine

```bash
# Set production database env vars, then:
alembic upgrade head
python -c "from api.main import app; from config import DB_TYPE; ..."
```

> Note: create a one-off `scripts/init_db.py` if you need to seed the super admin outside Vercel.

### Option B: Use Vercel CLI to run a one-off command

```bash
vercel --prod --command "python -m alembic upgrade head"
```

(Requires Alembic command configuration.)

---

## Verifying the Deployment

After deployment, check the following endpoints:

| Endpoint | Expected Result |
|----------|-----------------|
| `https://<your-domain>/` | Next.js landing page |
| `https://<your-domain>/api/health` | `200 OK`, `status: healthy` |
| `https://<your-domain>/api/ready` | `200 OK` or `503` with JSON error |
| `https://<your-domain>/api/docs` | FastAPI Swagger UI |

---

## Troubleshooting

### `FUNCTION_INVOCATION_FAILED` (500)

This means the Python function crashed during cold start. Check the **Function Logs** in the Vercel dashboard.

Common causes:

1. **Missing environment variables**
   - Set `DB_TYPE`, `MYSQL_*`, `JWT_SECRET_KEY`, `CORS_ORIGINS`.
2. **Database unreachable**
   - Check Hostinger allows connections from Vercel IPs.
   - Verify firewall / network access rules.
3. **Module not found**
   - Make sure all packages are in `requirements.txt`.
   - Remove `streamlit`, `plotly`, `schedule` if not used by the backend.
4. **Filesystem write error**
   - Ensure `LOG_PATH` is empty or omitted on Vercel.
   - The backup service and logging now handle readonly filesystems gracefully.

### `Module not found: next/swc-win32-x64-msvc`

This is a local Node.js version mismatch.

Fix:

- Use Node `20.x` or `18.x` (not Node 24).
- Delete `frontend/node_modules` and reinstall.

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Frontend cannot reach backend

1. Confirm `NEXT_PUBLIC_API_URL=/api` in Vercel env vars.
2. Check `vercel.json` routes `/api/*` to `api/index.py`.
3. Ensure CORS origins include your Vercel domain.

### Database connection errors

1. Verify `DB_TYPE=mysql`.
2. Check `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`.
3. Test connectivity from your local machine using a MySQL client.
4. Ensure the database user has privileges on the target schema.

### Slow cold starts

- Keep `DISABLE_STARTUP_TASKS=true` on Vercel (auto-set by `VERCEL=1`).
- Do not run `Base.metadata.create_all()` in serverless.
- Use connection pooling only on long-running servers.
- Reduce heavy imports at module level where possible.

---

## Rollback Procedure

1. In Vercel dashboard, go to **Deployments**.
2. Find the previous working deployment.
3. Click **... → Promote to Production**.

To roll back code:

```bash
git revert <bad-commit>
git push
vercel --prod
```

---

## Security Checklist

- [ ] `JWT_SECRET_KEY` is >= 32 random characters.
- [ ] `CORS_ORIGINS` is not `*` and lists only trusted domains.
- [ ] `SUPER_ADMIN_PASSWORD` is strong and changed after first login.
- [ ] MySQL user has minimal required privileges.
- [ ] `SEED_DEMO_DATA=false` in production.
- [ ] AI provider API keys are stored as Vercel secrets, not committed.
- [ ] `.env` and `database/*.db` are in `.gitignore`.

---

## Recommended Vercel Settings

| Setting | Recommendation |
|---------|----------------|
| Node Version | `20.x` |
| Function Region | Same region as your database (e.g., `iad1` for US East) |
| Function Max Duration | 30s default; increase for long-running reports |
| Build Command | `cd frontend && npm install --legacy-peer-deps && npm run build` |
| Output Directory | `frontend/.next` |
| Install Command | `cd frontend && npm install --legacy-peer-deps` |

---

## Files Added/Changed for Deployment

- `vercel.json` — root Vercel configuration.
- `api/index.py` — Vercel Python function entrypoint.
- `config.py` — import-safe configuration, default to SQLite when unset.
- `api/main.py` — serverless-aware lifespan, graceful health checks.
- `shared/database.py` — lazy engine cache, graceful failures.
- `etl/logging_config.py` — stdout-only logging by default, optional file logging.
- `etl/file_security.py` — guarded `python-magic` import.
- `services/backup_service.py` — graceful readonly filesystem handling.
- `requirements.txt` — cleaned dependencies.
- `frontend/next.config.js` — standalone output, API rewrites.
- `frontend/package.json` — pinned Node engine.
- `frontend/services/api/client.ts` — relative `/api` fallback.
- `docs/vercel_deployment_audit.md` — deployment blocker audit.
- `docs/environment_variables.md` — full env var reference.
- `docs/vercel-production-guide.md` — this guide.

---

## Support

If the deployment still fails after following this guide, inspect the **Vercel Function Logs** and look for:

- Missing environment variable errors.
- Database connection timeouts.
- Import errors for modules not in `requirements.txt`.
- Filesystem write errors from third-party packages.
