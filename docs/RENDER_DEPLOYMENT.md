# Backend Deployment Guide: Vercel → Render Migration

## Overview

The DataFlow backend has been migrated from Vercel serverless functions to Render
as a persistent ASGI application. The frontend remains on Vercel and proxies API
requests to the Render backend via `NEXT_PUBLIC_API_URL`.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Vercel (Next.js)│────▶│  Render (FastAPI)    │────▶│  Hostinger MySQL│
│  Frontend        │     │  Web Service         │     │                 │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Render Redis │
                        │  (Key/Value)  │
                        └──────────────┘
                               ▲
                        ┌──────────────┐
                        │  Render Worker│
                        │  (Background) │
                        └──────────────┘
```

## Prerequisites

1. **Hostinger MySQL** database with credentials ready
2. **Render account** with access to create services
3. **Vercel project** for the frontend (existing)

## Step 1: Deploy on Render

### Option A: Blueprint Deploy (Recommended)

1. Push your code to GitHub/GitLab
2. In Render dashboard: **New → Blueprint**
3. Select your repository — Render will detect `render.yaml`
4. Set the following secret environment variables in the Render dashboard:
   - `DATABASE_URL`: `mysql+pymysql://USER:PASS@HOST:3306/DB?charset=utf8mb4`
   - `JWT_SECRET_KEY`: Generate with `openssl rand -hex 32`
   - `ENCRYPTION_KEY`: Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g. `https://your-app.vercel.app`)
   - `STORAGE_BACKEND`: `r2`, `s3`, `supabase`, or `local`
   - Storage credentials (if using R2/S3/Supabase)
   - `CSP_CONNECT_SRC`: Your frontend URL for CSP headers

### Option B: Manual Deploy

1. **Create Web Service**:
   - Type: Web Service
   - Runtime: Docker
   - Dockerfile path: `./Dockerfile`
   - Health check: `/health`
   - Add all environment variables from `render.yaml`

2. **Create Background Worker**:
   - Type: Background Worker
   - Runtime: Docker
   - Docker command: `python -m performance.worker_entry`
   - Same DB/Redis env vars as web service

3. **Create Redis**:
   - Type: Key/Value (Redis)
   - Plan: Starter

## Step 2: Run Database Migrations

After the first deploy, run Alembic migrations against your Hostinger MySQL:

```bash
# Via Render shell (Shell tab in the web service)
./scripts/migrate.sh

# Or manually
alembic upgrade head
alembic current  # verify migration version
```

## Step 3: Update Vercel Frontend

In your Vercel project settings, set:

```
NEXT_PUBLIC_API_URL = https://your-render-service.onrender.com
```

This routes all `/api/*` requests from the Next.js frontend to the Render backend.

Redeploy the frontend after setting this variable.

## Step 4: Verify

1. Visit `https://your-render-service.onrender.com/health` — should return `{"status": "healthy"}`
2. Visit `https://your-render-service.onrender.com/docs` — Swagger UI should load
3. Test frontend login and API calls — CORS should allow requests from your Vercel domain

## Environment Variables Reference

See `.env.example` for the complete list. Critical ones for Render:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | MySQL connection string |
| `JWT_SECRET_KEY` | Yes | Min 32-char random secret |
| `ENCRYPTION_KEY` | Yes | Fernet key for API key encryption |
| `CORS_ORIGINS` | Yes | Comma-separated frontend URLs |
| `REDIS_URL` | Auto | Set by Render from Redis service |
| `STORAGE_BACKEND` | Yes | `r2`, `s3`, `supabase`, or `local` |
| `APP_ENV` | Yes | Set to `production` |
| `CSP_CONNECT_SRC` | Recommended | Frontend URL for CSP headers |

## Differences from Vercel

| Aspect | Vercel (old) | Render (new) |
|--------|-------------|-------------|
| Process model | Serverless functions | Persistent ASGI process |
| Background jobs | Not available (skipped) | In-process + dedicated worker |
| File system | Read-only (/tmp only) | Persistent disk |
| Health checks | N/A | `/health` endpoint |
| Max duration | 120s limit | No limit |
| Cold starts | Yes | No |
| Redis | External only | Render Key/Value (internal) |

## Troubleshooting

### Database connection issues
- Verify `DATABASE_URL` format: `mysql+pymysql://user:pass@host:port/db?charset=utf8mb4`
- Check Hostinger allows connections from Render's IP range
- `MYSQL_CONNECT_TIMEOUT=10` is set by default for remote connections

### CORS errors
- Ensure `CORS_ORIGINS` includes your exact Vercel URL (no trailing slash)
- Set `CSP_CONNECT_SRC` to the same URL

### Background jobs stuck
- Verify `REDIS_URL` is set (auto-configured from Render Redis service)
- Check worker service logs in Render dashboard
- Worker command: `python -m performance.worker_entry`

### Storage errors
- If using `local` storage, set `ALLOW_LOCAL_STORAGE_IN_PRODUCTION=1`
- For R2: ensure `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET` are all set
- For S3: ensure `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION` are all set
