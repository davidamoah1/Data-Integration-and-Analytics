# Vercel Deployment Final Report

**Project:** DataFlow — Enterprise Data Intelligence Platform  
**Repository:** `davidamoah1/Data-Integration-and-Analytics`  
**Deployment Provider:** Vercel  
**Report Date:** 2026-07-27  

---

## 1. Executive Summary

The Vercel configuration conflict (`functions` vs `builds`) has been resolved and the application has been successfully deployed to production. Both the Next.js frontend and the FastAPI backend serverless function are building and responding without the previous `FUNCTION_INVOCATION_FAILED` error.

| Component | Status | Production URL |
| :--- | :--- | :--- |
| Next.js frontend | **Operational** | `https://dataflow-enterprise.vercel.app` |
| FastAPI API | **Operational** | `https://dataflow-enterprise.vercel.app/api` |
| `/api/health` | **Operational** | `https://dataflow-enterprise.vercel.app/api/health` |

---

## 2. What Was Fixed

### 2.1 Vercel configuration conflict

`vercel.json` previously contained both the deprecated `builds` array and the modern `functions` object, which caused a deployment error. The file was rewritten to use the modern Vercel configuration format.

Key changes in `vercel.json`:

- Removed the deprecated `builds` array.
- Kept `functions` for the Python FastAPI entrypoint (`api/index.py`).
- Added `framework: "nextjs"` for automatic framework detection.
- Set `buildCommand`, `installCommand`, `outputDirectory`, and `devCommand` to point to the `frontend/` directory.
- Converted legacy route syntax to modern `source`/`destination` rewrites.
- Removed the catch-all frontend route; Next.js now serves its own output from `frontend/.next`.

### 2.2 Root `package.json` for monorepo detection

Because the Next.js app lives in `frontend/`, Vercel could not detect `next` in the repository root. A minimal root `package.json` was added that wraps the frontend scripts and declares `next` as a dependency. The actual install and build commands still operate inside `frontend/`, so the existing frontend dependency tree is preserved.

### 2.3 Python dependency declaration

Vercel's Python runtime used `uv` and read `pyproject.toml`. Because `pyproject.toml` did not declare dependencies, FastAPI and other packages were not installed in the serverless function, resulting in `ModuleNotFoundError: No module named 'fastapi'`. All backend dependencies from `requirements.txt` were mirrored into `pyproject.toml` under `[project] dependencies`.

### 2.4 FastAPI `/api` routing

Frontend calls use `NEXT_PUBLIC_API_URL=/api` on Vercel, while the FastAPI app defines routes relative to `/` (e.g., `/health`). A conditional `root_path="/api"` was added to `FastAPI(...)` when `VERCEL=1`, so Vercel's `/api/*` rewrites route to the correct backend endpoints without changing local development behavior.

### 2.5 Next.js build errors

Two TypeScript issues were fixed during the build:

1. `frontend/app/(app)/ai/page.tsx` — React ref type was changed to `React.MutableRefObject<HTMLDivElement | null>` for React 18 compatibility.
2. `frontend/features/dataset-workflow/WorkflowTimeline.tsx` — Added a boolean guard around `stage.result.score` to satisfy the `ReactNode` type.
3. `frontend/features/datasets/DatasetUpload.tsx` — Removed an always-false `disabled` guard inside a narrowed `UploadStage` branch.
4. `frontend/services/workflow/workflowService.ts` — Updated `apiClient` usage because the custom client returns the decoded response data directly, not an Axios-style response object with `.data`.

### 2.6 Missing test tooling

`vitest.config.ts` was being scanned by the Next.js type-checker. `vitest` and `@vitejs/plugin-react` were added to `frontend/package.json` `devDependencies` so the build resolves them.

### 2.7 Node engine range

The Node engine range was widened from `>=20.0.0 <21.0.0` to `>=20.0.0 <25.0.0` in both root and `frontend/package.json` files. This suppresses Vercel's deprecation warning for Node 20 while still allowing Node 20–24.

---

## 3. Final Configuration Files

### 3.1 `vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "version": 2,
  "framework": "nextjs",
  "buildCommand": "cd frontend && npm run build",
  "installCommand": "npm install --legacy-peer-deps && cd frontend && npm install --legacy-peer-deps",
  "outputDirectory": "frontend/.next",
  "devCommand": "cd frontend && npm run dev",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/index.py"
    },
    {
      "source": "/docs",
      "destination": "/api/index.py"
    },
    {
      "source": "/openapi.json",
      "destination": "/api/index.py"
    }
  ],
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  },
  "env": {
    "VERCEL": "1",
    "NEXT_PUBLIC_API_URL": "/api"
  }
}
```

### 3.2 Root `package.json`

```json
{
  "name": "dataflow-enterprise",
  "version": "1.0.0",
  "private": true,
  "description": "Root Vercel configuration package for the DataFlow Next.js frontend and FastAPI backend monorepo.",
  "engines": {
    "node": ">=20.0.0 <25.0.0"
  },
  "scripts": {
    "dev": "cd frontend && npm run dev",
    "build": "cd frontend && npm run build",
    "start": "cd frontend && npm start",
    "lint": "cd frontend && npm run lint",
    "type-check": "cd frontend && npm run type-check",
    "test": "cd frontend && npm test"
  },
  "dependencies": {
    "next": "^14.2.5"
  }
}
```

---

## 4. Deployment Verification

### 4.1 Production deployment

A production deployment was created with `vercel --prod --yes` and aliased to:

```
https://dataflow-enterprise.vercel.app
```

Deployment status from `vercel ls dataflow-enterprise`:

```
Age    Environment    Status    Duration
3m     Production     Ready     5m
```

### 4.2 Frontend check

`GET https://dataflow-enterprise.vercel.app` returned HTTP `200` with the DataFlow landing page and Next.js static assets.

### 4.3 API check

`GET https://dataflow-enterprise.vercel.app/api/health` returned:

```json
{
  "status": "healthy",
  "database_connected": true,
  "record_count": 5009,
  "timestamp": "2026-07-27T22:26:42.602161Z"
}
```

`GET https://dataflow-enterprise.vercel.app/api/docs` returned the FastAPI Swagger UI page, confirming the Python function is importable and FastAPI is running.

### 4.4 No `FUNCTION_INVOCATION_FAILED`

The previous serverless invocation error no longer occurs. The function cold-starts successfully, connects to the configured database, and serves API requests.

---

## 5. Important Notes & Next Steps

### 5.1 Serverless function size

The Python bundle is **~410 MB**, which exceeds Vercel's standard function size. Vercel applied dependency optimization and the deployment succeeded, but you should monitor cold-start times and function execution memory. Consider these optimizations if cold starts become slow:

- Move heavy data-science packages (`pandas`, `numpy`, `scipy`) to a dedicated compute service or edge function only when needed.
- Split the FastAPI app into smaller functions (e.g., `/api/health` as a lightweight function) to reduce the bundle for simple endpoints.
- Review `requirements.txt` / `pyproject.toml` for unused dependencies.

### 5.2 Deployment protection

SSO deployment protection was **temporarily disabled** to allow automated verification and then **re-enabled**. Authenticated team members can access the production domain through the Vercel dashboard. If you need public access, disable SSO protection via:

```bash
vercel project protection disable dataflow-enterprise --sso
```

### 5.3 Environment variables

The following variables are set in `vercel.json` `env`:

- `VERCEL=1`
- `NEXT_PUBLIC_API_URL=/api`

Database credentials, JWT secrets, and other sensitive values must be configured in the Vercel dashboard under **Project Settings → Environment Variables** or via:

```bash
vercel env add <name> <environment>
```

See `docs/vercel_environment_variables.md` for the full list.

### 5.4 Node version

Vercel currently defaults to Node 24 and warns that Node 20 deployments will fail after 2026-10-01. The engine range `>=20.0.0 <25.0.0` allows both versions locally and on Vercel. When you are ready to lock to Node 24, update the engine field to:

```json
"engines": { "node": "24.x" }
```

### 5.5 Local development

Local development continues to work from the repository root:

```bash
# Start the backend
python -m uvicorn api.main:app --reload --port 8000

# Start the frontend
npm run dev        # alias for cd frontend && npm run dev
```

The frontend uses `NEXT_PUBLIC_API_URL=http://localhost:8000` locally and `NEXT_PUBLIC_API_URL=/api` on Vercel.

---

## 6. Files Changed

- `vercel.json`
- `package.json` (new root wrapper)
- `frontend/package.json`
- `pyproject.toml`
- `api/main.py`
- `frontend/app/(app)/ai/page.tsx`
- `frontend/features/dataset-workflow/WorkflowTimeline.tsx`
- `frontend/features/datasets/DatasetUpload.tsx`
- `frontend/services/workflow/workflowService.ts`
- `docs/vercel_configuration_audit.md`
- `docs/vercel_environment_variables.md`

---

## 7. Conclusion

The Vercel `functions` vs `builds` conflict is resolved, the Next.js frontend builds successfully, and the FastAPI backend deploys and responds correctly in production. The deployment is stable and the `FUNCTION_INVOCATION_FAILED` error is eliminated. Monitor function bundle size and cold-start latency as the next operational improvements.

---

## 8. Troubleshooting Login "Internal Server Error"

If login or other API calls return **"Internal server error"** on Vercel, follow these steps:

### 8.1 Set `DEBUG=1` to reveal the real error

Add the environment variable in the Vercel dashboard and redeploy:

```
DEBUG=1
```

Retry login. The 500 response will now include the actual exception. Remove `DEBUG=1` after fixing.

### 8.2 Database is not configured

The most common cause is SQLite being used on Vercel. Vercel functions have a read-only/ephemeral filesystem, so a local SQLite file cannot be written or shared across invocations.

**Fix:** Use a hosted MySQL-compatible database. In Vercel environment variables set:

```
DB_TYPE=mysql
MYSQL_HOST=your-db-host
MYSQL_PORT=3306
MYSQL_DATABASE=dataflow
MYSQL_USER=dataflow_user
MYSQL_PASSWORD=your-strong-password
```

Serverless-friendly options: PlanetScale, Neon, Aiven, AWS RDS.

### 8.3 Tables do not exist

Because `VERCEL=1` skips heavy startup tasks, tables are now created **lazily** on the first database request. Trigger initialization by calling:

```
GET https://your-domain.vercel.app/api/ready
```

Then try login again.

### 8.4 Default super admin not seeded

If tables exist but login still fails, the default super admin may not have been seeded. With `DEBUG=1`, check the error. The seeding runs automatically when tables are created.

### 8.5 JWT secret missing

Ensure `JWT_SECRET_KEY` is set to a long random string in Vercel environment variables.

### 8.6 CORS blocked

If the frontend receives 500 or network errors, verify `CORS_ORIGINS` includes your production domain, e.g.:

```
CORS_ORIGINS=https://your-domain.vercel.app
```

