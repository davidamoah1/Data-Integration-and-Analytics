# Vercel Configuration Conflict Audit

**Repository:** `davidamoah1/Data-Integration-and-Analytics`  
**Date:** 2026-07-27  
**Issue:** Vercel deployment fails with `The \`functions\` property cannot be used in conjunction with the \`builds\` property. Please remove one of them.`

---

## Current Problems

### 1. Conflicting Vercel Configuration (`vercel.json`)

`@/d:\etl_project\vercel.json` contains **both** legacy `builds` and modern `functions` blocks:

```json
"builds": [ { "src": "frontend/package.json", "use": "@vercel/next", ... }, ... ],
"functions": { "api/index.py": { "maxDuration": 30 } }
```

Vercel v3 rejects this combination. Only one deployment model can be used.

### 2. Legacy `builds` Array

`builds` is a Vercel v2 concept and is deprecated for framework projects. It forces explicit build definitions and disables many zero-config optimizations for Next.js.

### 3. Frontend is in a Subdirectory

There is no `package.json` at the repository root. The Next.js app lives in `frontend/`. Vercel must be told how to build from that directory via `buildCommand` / `installCommand` / `outputDirectory`.

### 4. Rewrite Syntax Mix

Current `routes` use legacy `src`/`dest` keys. Modern Vercel config prefers `source`/`destination` (both are accepted, but `source`/`destination` is clearer when not using `builds`).

### 5. API Catch-All Routing

The catch-all route `"src": "/(.*)"`, `"dest": "frontend/$1"` is not how Vercel serves a Next.js build. With modern config, Next.js is built and its output is served automatically; explicit frontend routing is unnecessary and may conflict.

---

## Required Changes

1. **Remove `builds` array** from `vercel.json`.
2. **Keep `functions`** for the Python FastAPI endpoint so `maxDuration` can be configured.
3. **Set `framework: "nextjs"`** explicitly.
4. **Set `buildCommand`, `installCommand`, `outputDirectory`** to point to `frontend/`.
5. **Convert rewrites** to modern `source`/`destination` syntax.
6. **Remove the catch-all frontend route**; Vercel handles Next.js output routing automatically.
7. **Keep `/api/*`, `/docs`, `/openapi.json`, `/health`, `/ready` rewrites** pointing to `api/index.py`.

---

## Final Deployment Architecture

```
Repository root
├── frontend/          → Next.js 14 app (built by Vercel)
│   ├── package.json
│   ├── next.config.js
│   └── app/
├── api/
│   └── index.py       → FastAPI ASGI entrypoint (Vercel Python function)
├── requirements.txt   → Python dependencies for api/index.py
├── vercel.json        → Modern Vercel configuration
└── config.py          → App configuration
```

### How requests flow

| Request | Destination |
|---------|-------------|
| `/` | Next.js static/generated landing page |
| `/dashboard` | Next.js App Router page |
| `/api/health` | FastAPI `/health` endpoint |
| `/api/docs` | FastAPI Swagger UI |
| `/api/(any)` | FastAPI route handler |
| `/docs`, `/openapi.json`, `/health`, `/ready` | FastAPI route handler |

### Vercel build flow

1. Vercel detects `vercel.json`.
2. Frontend: uses `framework: nextjs`, runs `cd frontend && npm install --legacy-peer-deps`, then `cd frontend && npm run build`, outputs to `frontend/.next`.
3. Python: builds `api/index.py` as a serverless function using `requirements.txt`.

---

## Notes

- `api/index.py` must expose an ASGI `app` callable.
- `api/main.py` must not start background schedulers, run migrations, or seed data during import/cold start.
- `config.py` must be import-safe when env vars are missing (already fixed in previous pass).
- Database migrations and seeding must be run outside Vercel (e.g., via a manual script or CI/CD) because serverless functions are stateless and short-lived.
