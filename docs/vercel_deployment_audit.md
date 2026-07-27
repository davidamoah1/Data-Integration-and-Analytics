# Vercel Deployment Audit

**Repository:** `davidamoah1/Data-Integration-and-Analytics`  
**Date:** 2026-07-27  
**Objective:** Fix `500 FUNCTION_INVOCATION_FAILED` and make the application production-ready on Vercel.

---

## Summary

The application currently deploys to Vercel but crashes immediately with `FUNCTION_INVOCATION_FAILED`. The root causes are a combination of:

1. **Missing root-level Vercel configuration** for the Python backend.
2. **Fatal startup logic** inside FastAPI `lifespan` (database migrations, seeding, scheduler startup).
3. **Configuration that raises at import time** when required env vars are missing.
4. **Filesystem writes during module import** (logging setup creates directories).
5. **Frontend runtime incompatible with the installed Node.js version** (SWC binary failure).
6. **Frontend API client falls back to `localhost`** instead of a relative/Vercel-safe URL.
7. **Missing dependency declarations** for platform-specific packages.

---

## Phase 1 — Full Deployment Audit Findings

### 1.1 Vercel Configuration

| File | Issue | Severity |
|------|-------|----------|
| `frontend/vercel.json` | Exists only inside `frontend/`; no root `vercel.json` to deploy Python functions | **Critical** |
| `vercel.json` (root) | Missing entirely | **Critical** |
| `frontend/next.config.js` | Uses `env:` (redundant), no `output: 'standalone'`, no rewrites to `/api` | **High** |

### 1.2 FastAPI Entrypoint

| File | Issue | Severity |
|------|-------|----------|
| `api/main.py` | Correctly creates `app = FastAPI(...)`, but no `api/index.py` adapter for Vercel Serverless Functions | **Critical** |
| `api/main.py` | `lifespan` performs `Base.metadata.create_all()`, seeds data, starts APScheduler, schedules backups — all crash-prone in serverless | **Critical** |

### 1.3 Configuration (`config.py`)

| Issue | Severity |
|-------|----------|
| Raises `ValueError` at import if `DB_TYPE` is unset | **Critical** |
| No graceful fallback for missing optional env vars | High |
| `JWT_SECRET_KEY` default is weak and flagged | High |
| `CORS_ORIGINS` validation raises at startup | Medium |

### 1.4 Database Initialization

| File | Issue | Severity |
|------|-------|----------|
| `api/main.py` | `create_all()` runs on every cold start | **Critical** |
| `api/main.py` | `seed_default_data()` runs on every cold start | **Critical** |
| `api/main.py` | `ReportScheduler().start()` runs on every cold start | **Critical** |
| `api/main.py` | Backup cron job added on every cold start | **Critical** |

### 1.5 Import-time Side Effects

| File | Issue | Severity |
|------|-------|----------|
| `etl/logging_config.py` | `setup_logging()` called at module import; creates `logs/` directory | **Critical** |
| `etl/logging_config.py` | `RotatingFileHandler` tries to write to local filesystem | High |
| `config.py` | `load_dotenv()` called at import; fine, but combined with validation it crashes | Medium |

### 1.6 Filesystem Access

| File | Issue | Severity |
|------|-------|----------|
| `services/backup_service.py` | Creates `backups/` directory at import via `_backup_dir()` | **Critical** |
| `services/backup_service.py` | Reads `.env` and writes backup files to local disk | High |
| `shared/contracts/plugins.py` | `Path.open()` to load plugin manifests | Medium |
| `etl/file_security.py` | Imports `magic` (`python-magic`), which may not be available on Vercel | Medium |

### 1.7 Background Services

| File | Issue | Severity |
|------|-------|----------|
| `scheduler/report_scheduler.py` | APScheduler background scheduler started in lifespan | **Critical** |
| `performance/worker_entry.py` | Worker pool entrypoint not invoked automatically, but imported modules may trigger side effects | Medium |

### 1.8 Next.js / Frontend

| File | Issue | Severity |
|------|-------|----------|
| `frontend/package.json` | No `engines` field; Node 24 incompatible with Next.js 14.2 SWC | **Critical** |
| `frontend/services/api/client.ts` | Falls back to `http://localhost:8000` | **Critical** |
| `frontend/next.config.js` | No rewrites to proxy API calls to the Python function | High |
| `frontend/vercel.json` | `NEXT_PUBLIC_API_URL: "@dataflow_api_url"` references a Vercel secret that may not exist | High |

### 1.9 Requirements

| File | Issue | Severity |
|------|-------|----------|
| `requirements.txt` | `streamlit` and `plotly` not needed for FastAPI serverless deployment | Medium |
| `requirements.txt` | Missing explicit `python-magic-bin` / `libmagic` note for Windows vs Linux | Medium |
| `requirements.txt` | `mysqlclient` not listed; project uses `pymysql` (good) | Low |

### 1.10 Health Checks

| File | Issue | Severity |
|------|-------|----------|
| `api/main.py` | `/health` exists but depends on `SalesRepository`, which may fail if DB is unavailable | Medium |
| `api/main.py` | `/ready` exists but queries heavy models; acceptable but could be lighter | Medium |

---

## Phase 2 — Startup Crash Root Causes

The Vercel function crashes during cold start because:

1. `config.py` is imported by many modules.
2. If `DB_TYPE` is not set, it raises `ValueError` immediately.
3. If `DB_TYPE=mysql` but MySQL env vars are missing, it raises `ValueError`.
4. `etl/logging_config.py` runs `setup_logging()` at import and tries to create `logs/`.
5. `api/main.py` lifespan runs `create_all()`, seeds data, starts scheduler, schedules backups.
6. Any DB connection failure during these steps causes the function to crash before handling a request.

**Fix strategy:**
- Make configuration import-safe; validate only when explicitly requested.
- Make lifespan startup lazy and idempotent; skip heavy operations when `VERCEL=1` or `DISABLE_STARTUP_TASKS=1`.
- Remove filesystem writes at import time.

---

## Phase 3 — FastAPI Entrypoint

Vercel Python Serverless Functions expect an `api/index.py` that exposes an `app` callable (ASGI) or a handler function.

**Fix strategy:**
- Create `api/index.py` that imports and re-exports `api.main:app` for Vercel.
- Keep `api/main.py` as the canonical application definition.

---

## Phase 4 — Vercel Configuration

**Fix strategy:**
- Create root `vercel.json` with:
  - `builds` for the Python function.
  - `routes`/`rewrites` so Next.js frontend calls `/api/*` proxied to the Python function.
  - `regions` and environment variables.
- Update `frontend/next.config.js` with rewrites to `/api`.

---

## Phase 5 — Requirements

**Fix strategy:**
- Pin `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `pymysql`, `cryptography`.
- Remove `streamlit`, `plotly` if not used by backend (move to a separate dev/requirements if needed).
- Add note about `python-magic` / `libmagic1` on Linux.

---

## Phase 6 — Environment Variables

See `docs/environment_variables.md` for the full list.

**Fix strategy:**
- Make all optional variables have safe defaults.
- Only fail validation when `DISABLE_CONFIG_VALIDATION` is not set.
- Provide clear error messages.

---

## Phase 7 — Database Connections

**Fix strategy:**
- Do not call `create_all()` in lifespan on Vercel.
- Use `pool_pre_ping=True` and short timeouts.
- Return `503` from `/ready` if DB is unreachable instead of crashing.
- Document that migrations should be run via a separate migration command (e.g., Alembic) or a one-off Vercel function.

---

## Phase 8 — Import Errors

No circular imports detected in the current audit, but heavy import-time side effects exist.

---

## Phase 9 — Filesystem Access

**Fix strategy:**
- Move `etl/logging_config.py` file-handler creation out of import time.
- Make `services/backup_service.py` not create directories at import.
- Make plugin manifest loading lazy.

---

## Phase 10 — Background Services

**Fix strategy:**
- Disable APScheduler startup when `VERCEL=1`.
- Provide `/scheduler/trigger` endpoint or Vercel Cron to run scheduled reports externally.

---

## Phase 11 — Next.js API Calls

**Fix strategy:**
- Update `frontend/services/api/client.ts` to use a relative URL (`/api`) when `NEXT_PUBLIC_API_URL` is not set, so Vercel rewrites handle routing.
- Remove hardcoded `localhost:8000` fallback.

---

## Phase 12 — Error Handling

**Fix strategy:**
- Wrap lifespan in broad try/except and log errors without crashing.
- Return 503 from health endpoints when subsystems fail.
- Never return stack traces to clients.

---

## Phase 13 — Logging

**Fix strategy:**
- Use stdout logging by default on Vercel.
- Only enable file logging when `LOG_PATH` is explicitly set and writable.
- Add structured JSON logging option.

---

## Phase 14 — Health Checks

`/health` and `/ready` already exist but need to be hardened.

**Fix strategy:**
- Make `/health` lightweight (return 200 if app boots).
- Make `/ready` gracefully return 503 if DB is unavailable.

---

## Phase 15 — Production Hardening

**Fix strategy:**
- Pin Node engine to `20.x` in `frontend/package.json`.
- Remove unused heavy imports.
- Use `output: 'standalone'` in Next.js config.
- Disable file logging in serverless.

---

## Phase 16 — Test Deployment

After fixes, verify:
- `vercel --prod` or `vercel dev` boots.
- `GET /health` returns 200.
- `GET /ready` returns 200 or 503 gracefully.
- Frontend loads and API calls succeed.

---

## Phase 17 — Documentation

See `docs/vercel-production-guide.md` for deployment steps.

---

## Severity Summary

| Severity | Count | Examples |
|----------|-------|----------|
| Critical | 12 | Missing `vercel.json`, `DB_TYPE` crash, lifespan `create_all`, scheduler startup, filesystem writes, Node/SWC mismatch, localhost fallback |
| High | 8 | Weak JWT default, backup service filesystem access, missing rewrites, redundant env config |
| Medium | 6 | Plugin manifest loading, python-magic platform dependency, health check dependencies |
| Low | 2 | Unused requirements, minor config defaults |

## Recommended Fix Order

1. Create `api/index.py` Vercel adapter.
2. Create root `vercel.json`.
3. Fix `config.py` to be import-safe.
4. Fix `etl/logging_config.py` to avoid filesystem writes at import.
5. Fix `api/main.py` lifespan to skip heavy tasks on Vercel.
6. Update `requirements.txt`.
7. Fix `frontend/package.json` Node engine and upgrade Next.js if needed.
8. Fix `frontend/services/api/client.ts` URL fallback.
9. Update `frontend/next.config.js` with rewrites and standalone output.
10. Add/harden `/health` and `/ready`.
11. Create documentation.
