# Frontend Data Decision Audit — Final Report

## Executive Summary

A comprehensive root-cause audit and optimization of the Data Integration and Analytics platform was conducted, focusing on certificate processing and the "Data to Decision" workflow. The audit was executed in two phases:

- **Phase 1** (7 fixes): Student name extraction, filtering correctness, N+1 queries, async workflow handling, batch counter accuracy.
- **Phase 2** (5 fixes): Job idempotency, composite database indexes, Data-to-Decision progress feedback, review_required counter, request_id in error responses.

All 1682 tests pass (1 skipped), linters are clean, and TypeScript type check passes.

---

## Fixes Implemented

### Fix 1: Student Name Extraction (High Priority)

**Root Cause:** The field was named `full_name` with only the generic keyword `"name"`, causing the extractor to match `"Institution Name: ..."` or `"Date of Birth: ..."` instead of the actual student name.

**Changes:**
- `capture/document_types.py` — Replaced `full_name` with `student_name` in all 9 certificate types and `GENERIC_FIELDS`. Added rich label variants: "Student Name", "Candidate Name", "Name of Student", "Name of Candidate", "Learner Name", "Full Name", "Awarded to", "Conferred upon", "This is to certify that".
- `capture/extractors.py` — Keywords sorted by length (longest first) so "Student Name" matches before "Name". Added `_looks_like_label()` helper to reject extracted values that look like other field labels (e.g., "Institution Name", "Certificate Number").
- `certificates/normalizer.py` — Added `student_name` to the normalization dispatch table.
- `certificates/analysis.py` — Consistency checks and summary now check `student_name` first, fall back to `full_name` for backward compatibility.
- `certificates/routes.py` — Added `student_name` to `EXPORT_COLUMNS` with priority over `full_name`.

### Fix 2: Filtering — Stale Data, Total Count, Silent Catch (High Priority)

**Root Cause:** Frontend silently swallowed filter errors, keeping stale data visible. Backend loaded all document IDs into memory for total count instead of using `COUNT()`.

**Changes:**
- `frontend/app/(app)/certificates/page.tsx` — `handleSearch` and `loadData` now clear certificate data on error and show toast notifications instead of silently keeping stale results.
- `certificates/routes.py` (search endpoint) — Total count uses `func.count()` instead of loading all IDs. Field loading batched into a single query for all matching documents (Fix 6).

### Fix 3: Data to Decision — Async 202 Handling (High Priority)

**Root Cause:** When the backend returned a 202 with `{ job_id, status, status_url }` (async mode with Redis), the frontend's `workflowService.runWorkflow` treated it as a `WorkflowState`, resulting in `undefined` `workflow_id`. All subsequent calls to `getProfile`, `getQuality`, etc. failed silently.

**Changes:**
- `frontend/services/workflow/workflowService.ts` — `runWorkflow` now detects async job responses (has `job_id`, no `workflow_id`), polls `/api/jobs/{jobId}` every 2 seconds (max 120s), and extracts the `WorkflowState` from the job result once completed. Added `getJobStatus` method for lightweight polling. Added `onProgress` callback for real-time progress messages during async polling.
- `frontend/app/(app)/data-to-decision/page.tsx` — Added `processingMessage` state for real-time user feedback during long async operations. Progress messages from the backend (e.g., "Profiling dataset...", "Analyzing quality...") are now displayed to the user with percentage.

### Fix 4: Certificate Batch — Succeeded Counter (High Priority)

**Root Cause:** `succeeded += 1` ran after every successful *upload*, regardless of whether processing succeeded. When local storage synchronous processing failed, the exception was caught and logged as a warning, but `succeeded` was still incremented.

**Changes:**
- `certificates/routes.py` — Added `processing_status` tracking. When synchronous processing fails, `failed` is incremented instead of `succeeded`. The document's actual post-processing status is refreshed from the database. Failed results include an `error_message`. Also added `review_required` counter increment when processing completes with `ready_for_review` status.

### Fix 5: Dashboard N+1 Query (Medium Priority)

**Root Cause:** The `/dashboard` endpoint iterated through all documents and issued separate queries for `institution` and date fields per document — classic N+1.

**Changes:**
- `certificates/routes.py` — Replaced per-document field queries with two batch queries: one for all `institution` fields, one for all date fields (`date_awarded`, `date_issued`, `graduation_date`), filtered by `document_id.in_(doc_ids)`. Reduces DB round-trips from 2N+1 to 3.

### Fix 6: Search N+1 Query (Medium Priority)

**Root Cause:** The `/search` endpoint loaded `CaptureField` records per-document after filtering.

**Changes:**
- `certificates/routes.py` — Batch-loads all `CaptureField` records for matching documents in a single query, then groups them by `document_id` in memory.

### Fix 7: Student Name Normalization (Medium Priority)

Covered under Fix 1 — `student_name` added to normalizer dispatch table and analysis module with `full_name` fallback.

### Fix 8: Job Idempotency Keys (High Priority)

**Root Cause:** No deduplication mechanism for job submission. If a user double-clicks "Upload" or the network retries, the same document could be processed twice.

**Changes:**
- `jobs/models.py` — Added `idempotency_key` column (VARCHAR(255), indexed, nullable) to the `Job` model. Included in `to_dict()` output.
- `jobs/repositories.py` — Added `find_by_idempotency_key()` method that returns the most recent pending/running/completed job with the same key (failed/cancelled jobs are excluded so they can be retried).
- `jobs/service.py` — `create_job()` now accepts an optional `idempotency_key` parameter. If provided and an active/completed job with that key exists, the existing job is returned instead of creating a duplicate.
- `jobs/routes.py` — Added `idempotency_key` field to `CreateJobRequest` model so API consumers can pass a deduplication key.
- `certificates/routes.py` — OCR document jobs now use `idempotency_key=f"org_{org_id}:ocr_document:doc_{doc.id}"`.
- `services/dataset_workflow_routes.py` — Dataset workflow jobs now use `idempotency_key=f"org_{org_id}:dataset_workflow:file_{record.file_id}"`.

### Fix 9: Composite Database Indexes (Medium Priority)

**Root Cause:** Certificate search and dashboard queries filter by `(organization_id, document_type)` and `(organization_id, status)` but only single-column indexes existed, requiring index merges or full scans.

**Changes:**
- `alembic/versions/0020_job_idempotency_and_composite_indexes.py` — New migration adding:
  - `ix_capture_documents_org_type` on `(organization_id, document_type)`
  - `ix_capture_documents_org_status` on `(organization_id, status)`
  - `ix_background_jobs_idempotency_key` on `background_jobs.idempotency_key`
  - `background_jobs.idempotency_key` column

### Fix 10: Data-to-Decision Progress Feedback (Medium Priority)

**Root Cause:** During async workflow polling, the user saw only "Uploading and analyzing dataset..." with no progress updates from the backend.

**Changes:**
- `frontend/services/workflow/workflowService.ts` — `runWorkflow` now accepts an optional `onProgress(message, progress)` callback that is called with the backend's `progress_message` and `progress` value during each poll cycle.
- `frontend/app/(app)/data-to-decision/page.tsx` — Passes `onProgress` callback that updates `processingMessage` with the backend's progress message and percentage (e.g., "Profiling dataset... (45%)").

### Fix 11: Request ID in Error Responses (Low Priority)

**Root Cause:** Error responses did not include the `request_id`, making it difficult to trace errors in logs.

**Changes:**
- `api/main.py` — All three exception handlers (HTTPException, RequestValidationError, global Exception) now include `request_id` from the request context in their JSON responses.

---

## Infrastructure Fixes (Previous Session)

- `api/main.py` — Disabled in-process job worker when Redis is configured, preventing double-processing.
- `shared/database.py` — Cached `sessionmaker` in `get_session_factory` to avoid creating a new instance per request. `reset_engine` clears the cache for tests.

---

## Test Results

| Check | Result |
|-------|--------|
| pytest (full suite) | **1682 passed**, 1 skipped, 0 failures |
| black | All files formatted |
| ruff | All checks passed |
| bandit | 1 low-severity false positive (grade string "Pass") |
| TypeScript (`tsc --noEmit`) | No errors |

### New Regression Tests (`tests/test_audit_fixes.py` — 22 tests)

- **TestStudentNameFieldSpec** (6 tests) — All cert types have `student_name`, no `full_name`, required, rich keywords, in `GENERIC_FIELDS`.
- **TestExtractorKeywordPriority** (4 tests) — Longest-keyword-first matching, "Student Name" preferred over "Name", "Name of Student" and "Candidate Name" extracted correctly.
- **TestLabelRejection** (5 tests) — "Institution Name" and "Certificate Number" rejected as name values; real names not rejected; non-name fields not checked.
- **TestStudentNameNormalization** (4 tests) — Title-case conversion, mixed-case preservation, None handling, backward compat with `full_name`.
- **TestAnalysisStudentNameFallback** (3 tests) — Consistency checks work via `student_name` and via `full_name` fallback.

### Updated Existing Tests

- `tests/test_certificates.py` — Updated field assertions from `full_name` to `student_name`.
- `tests/test_certificate_intelligence.py` — Updated all test data from `full_name` to `student_name` (10 edits across completeness, consistency, anomaly, recommendation, analysis, and batch analytics tests).

---

## Files Modified

| File | Changes |
|------|---------|
| `capture/document_types.py` | `student_name` field in all cert types, `GENERIC_FIELDS` |
| `capture/extractors.py` | Keyword sorting, `_looks_like_label` helper |
| `certificates/normalizer.py` | `student_name` in dispatch table |
| `certificates/analysis.py` | `student_name` priority with `full_name` fallback |
| `certificates/routes.py` | Export columns, search N+1, dashboard N+1, batch counter, review_required counter, idempotency keys for OCR jobs |
| `frontend/services/workflow/workflowService.ts` | Async 202 handling, job polling, onProgress callback |
| `frontend/app/(app)/data-to-decision/page.tsx` | Processing message state, progress feedback during polling |
| `frontend/app/(app)/certificates/page.tsx` | Stale data clearing on error |
| `api/main.py` | Disabled in-process worker when Redis configured, request_id in error responses |
| `shared/database.py` | Cached sessionmaker |
| `jobs/models.py` | Added `idempotency_key` column |
| `jobs/repositories.py` | Added `find_by_idempotency_key()` method |
| `jobs/service.py` | Idempotency check in `create_job()` |
| `jobs/routes.py` | Added `idempotency_key` to `CreateJobRequest` |
| `services/dataset_workflow_routes.py` | Idempotency key for dataset workflow jobs |
| `alembic/versions/0020_job_idempotency_and_composite_indexes.py` | New migration: idempotency column + composite indexes |
| `tests/test_audit_fixes.py` | New — 22 regression tests |
| `tests/test_certificates.py` | Updated for `student_name` |
| `tests/test_certificate_intelligence.py` | Updated for `student_name` |

---

## Architecture Observations

### What's Working Well
- **Deferred startup**: Heavy seeding and scheduler init run in a background task, so the app accepts requests quickly.
- **Health checks**: `/health` is a simple in-memory check (no DB call), `/ready` does a `SELECT 1`.
- **Audit middleware**: Writes to DB via `asyncio.to_thread()`, avoiding request blocking.
- **Monitoring middleware**: Combines Prometheus, OpenTelemetry, and Sentry with minimal overhead.
- **Job queue**: Redis-backed with in-memory fallback, priority queues, retry logic, and dead letter queue.
- **Worker isolation**: Dedicated worker process on Render (`performance.worker_entry`), web service doesn't compete when Redis is configured.
- **Frontend polling**: Certificate status polling has timeout (120s), consecutive failure tracking (5 max), and proper cleanup.
- **API client**: 30s timeout, token refresh on 401, retry on network errors, upload with progress via XHR.

### Areas for Future Improvement
- **Redis queue persistence**: Currently using in-memory fallback for development; production should use Redis with persistence enabled.
- **Connection pool tuning**: `POOL_SIZE=10`, `MAX_OVERFLOW=20` may need adjustment based on actual load testing.
- **CDN for static assets**: Frontend on Vercel already benefits from Edge network, but backend static files (if any) could use a CDN.
- **Query result caching**: Consider Redis caching for frequently accessed dashboard data with short TTL.

---

## Phase 3 — Production Database Schema Drift Fix (2026-08-31)

### Root Cause

Migration `0020_job_idempotency_and_composite_indexes` (revision `b3c4d5e6f7a8`) was committed to the codebase and pushed, adding `background_jobs.idempotency_key` to the SQLAlchemy model. The production Hostinger MySQL database was at revision `a1b2c3d4e5f6` (migration 0019), one step behind head. The Render deployment did not run `alembic upgrade head` on startup, so the schema drift went undetected until a user triggered the "Process Dataset" workflow, which queries `background_jobs.idempotency_key`.

### Production Migration Version

| | Version | Description |
|---|---|---|
| **Before fix** | `a1b2c3d4e5f6` | Migration 0019 — workspace and invitation tables |
| **After fix** | `b3c4d5e6f7a8` | Migration 0020 — job idempotency + composite indexes (HEAD) |

### Migration Applied

```
alembic upgrade head
# Running upgrade a1b2c3d4e5f6 -> b3c4d5e6f7a8
# Add job idempotency_key column and composite indexes for certificate queries.
```

### Tables/Columns Changed

| Table | Change | Type |
|---|---|---|
| `background_jobs` | Added `idempotency_key` column | `VARCHAR(255)`, nullable, indexed |
| `background_jobs` | Added `ix_background_jobs_idempotency_key` index | B-tree on `idempotency_key` |
| `capture_documents` | Added `ix_capture_documents_org_type` index | Composite on `(organization_id, document_type)` |
| `capture_documents` | Added `ix_capture_documents_org_status` index | Composite on `(organization_id, status)` |

### Schema Drift Audit Results

| Check | Result |
|---|---|
| Tables in models but not in production | **0** — all 135 model tables exist |
| Tables in production but not in models | 1 (`alembic_version` — expected) |
| Missing columns on key tables | **0** — all columns match |
| Missing indexes on `background_jobs` | **0** — all indexes present |
| Missing indexes on `capture_documents` | **0** — all indexes present |
| `audit_logs` index naming mismatch | 4 model indexes not in production (pre-existing, migrations intentionally dropped/renamed them — low priority) |

### Error Handling Fix

**Before**: `shared/database.py` `get_db()` raised `HTTPException(500, detail="Database initialization error: OperationalError: (1054, \"Unknown column 'background_jobs.idempotency_key' in 'SELECT'\")")` — exposing raw SQL errors to users.

**After**: In production (non-DEBUG mode), returns generic message: *"Something went wrong while preparing your dataset. Please try again or contact your administrator."* Full error details remain in server logs.

### Deployment Safeguards Added

1. **Dockerfile CMD** now runs: `alembic upgrade head && python scripts/verify_schema.py && uvicorn ...`
2. **`scripts/verify_schema.py`** — Pre-start verification:
   - Database connectivity (`SELECT 1`)
   - Alembic version matches migration head
   - Critical columns exist (`background_jobs.idempotency_key`, etc.)
   - Exits non-zero if any check fails, preventing app startup with drift
3. **Worker container** does NOT run migrations (only web service does)

### Background Job Architecture Verification

- When `REDIS_URL` is set: web service does NOT start in-process worker (confirmed in `api/main.py` lifespan)
- Dedicated Render worker (`performance.worker_entry`) processes jobs from Redis queue
- `background_jobs` table persists job state in MySQL
- Idempotency key prevents duplicate job submissions

### Test Results

| Check | Result |
|---|---|
| pytest | **1682 passed, 1 skipped, 0 failures** |
| black --check . | **All 524 files clean** |
| ruff check . | **All checks passed** |
| bandit -r . -ll | **0 high, 0 new medium findings** (9 pre-existing B608 false positives with nosec annotations) |

### Production Verification

| Check | Status |
|---|---|
| Hostinger MySQL reachable | ✅ Connected from local machine |
| Alembic version at head | ✅ `b3c4d5e6f7a8` |
| Single Alembic head | ✅ Confirmed |
| `background_jobs.idempotency_key` exists | ✅ `varchar(255)`, nullable, indexed |
| `ix_background_jobs_idempotency_key` exists | ✅ |
| `ix_capture_documents_org_type` exists | ✅ |
| `ix_capture_documents_org_status` exists | ✅ |
| No raw DB errors exposed to users | ✅ Fixed in `shared/database.py` |
| Background worker architecture intact | ✅ No duplicate workers when Redis configured |

### Remaining Risks

1. **Render redeploy required**: The Dockerfile change (CMD with `alembic upgrade head`) will take effect on next Render deploy. The migration has already been applied manually, so the deploy will be a no-op for the DB.
2. **`audit_logs` index naming mismatch**: 4 indexes defined in the SQLAlchemy model (`idx_audit_action_resource`, `idx_audit_resource`, `idx_audit_org_created`, `ix_audit_logs_organization_id`) are not in production. These were intentionally dropped/renamed in migrations. Low priority — does not affect functionality.
3. **Production smoke test**: Cannot be performed from local machine. After Render redeploys, verify: `/health`, `/ready`, login, Data to Decision → Upload → Process Dataset workflow.
4. **Filter correctness**: Verified in code — empty results display "No results found", stale data cleared on error. Cannot verify in production from local machine.

### Exact Render Deployment Steps

1. Push to `main` (done — commit `f7edc1a`)
2. Render auto-deploys from `main` branch
3. Docker build runs: `alembic upgrade head` (no-op, already at head) → `verify_schema.py` (passes) → `uvicorn` starts
4. Worker container starts with `python -m performance.worker_entry` (no migration, just job processing)
5. Verify: `GET /health` → 200, `GET /ready` → 200
6. Test: Login → Data to Decision → Upload CSV → Process Dataset → Background job created → Workflow completes

### Confirmation: Hostinger MySQL is the Production Database

- Host: `srv1925.hstgr.io:3306`
- Database: `u344535597_dataflow`
- User: `u344535597_dataflow`
- 136 tables confirmed in production
- Alembic version table present and at head `b3c4d5e6f7a8`

---

## Full Production Readiness Audit — All Phases

### Test Results
- **1682 passed, 1 skipped, 0 failures** (12 min runtime)
- No TODO/FIXME/HACK/XXX items in codebase
- No hardcoded secrets, no localhost dependencies in production paths
- No pickle usage, no subprocess with shell=True

### Phase 1: Repository Inspection ✅
- No hardcoded secrets in source files
- No localhost references in production code paths
- `DEBUG` flag properly gates error detail exposure (off by default)
- `VERCEL` env var used only for serverless detection via `IS_SERVERLESS` abstraction
- All sensitive values use `sync: false` in render.yaml (set in dashboard)

### Phase 2-3: Database Schema & Migration Safety ✅
- Alembic head: `b3c4d5e6f7a8`
- Dockerfile runs `alembic upgrade head` → `verify_schema.py` before app start
- MySQL production: 136 tables, all critical columns verified
- Schema drift audit script created and run

### Phase 4: DB Connection Pooling ✅
- `pool_pre_ping=True` — dead connections detected before use
- `POOL_SIZE=10`, `MAX_OVERFLOW=20`, `POOL_RECYCLE=3600`, `POOL_TIMEOUT=30`
- `MYSQL_CONNECT_TIMEOUT=10` for Hostinger reliability
- Engine cached as singleton, session factory cached per engine
- Slow query listener attached (`SLOW_QUERY_THRESHOLD_MS`)
- Error handling: full traceback logged server-side, generic message to user in production

### Phase 5-6: Login Performance & Cold Start ✅
- Login flow: indexed lookups (email, user_id), bcrypt verification, JWT creation
- No N+1 queries in login — roles/permissions loaded in bounded queries
- Cold start: deferred startup task (`asyncio.create_task`) binds port immediately
- Render health check (`/health`) responds in <10ms (no DB call)
- `keep-render-awake.yml` pings every 10 minutes to prevent free-tier sleep

### Phase 7-8: Health Checks & Background Jobs ✅
- `/health` — lightweight liveness (no DB, <10ms)
- `/ready` — DB connectivity (`SELECT 1`), returns 503 if DB down
- `/health/detailed` — admin-only, all subsystems
- `/health/db`, `/health/ocr`, `/health/storage`, `/health/ai`, `/health/workers` — granular checks
- Background worker: dedicated Render worker container (`python -m performance.worker_entry`)
- Worker only starts in-memory queue when Redis is NOT configured (no double-processing)
- Graceful shutdown via SIGINT/SIGTERM signal handlers

### Phase 9-11: Dataset Upload, Data-to-Decision, Async Processing ✅
- File uploads use UUID-based storage keys (no user filenames in paths)
- Path traversal protection in `LocalFileBackend._full_path()`
- Async workflow execution: requires Redis + non-serverless, falls back to sync
- Job idempotency: jobs have status tracking, `mark_running` prevents duplicate execution

### Phase 12-14: Certificate Intelligence ✅
- Certificate search has proper pagination (`limit`/`offset`)
- Batch analytics bounded by `batch_id`
- Export endpoints (CSV/XLSX) now have `MAX_EXPORT_LIMIT=10000` safety cap
- Report/presentation endpoints also capped
- N+1 prevention: batch-load fields with `IN()` query for all docs in page

### Phase 15-18: Analytics, AI, Middleware ✅
- GZip middleware (min 1000 bytes)
- Request size limit middleware (`MAX_REQUEST_BODY_BYTES`)
- Security headers middleware
- Monitoring middleware (Sentry, OpenTelemetry, Prometheus)
- Audit middleware (auto-logs mutating requests)

### Phase 19-22: Tenant Isolation, Auth, SQL Security ✅
- 4-layer tenant isolation: middleware → route → query → resource
- JWT claims include `org_id` (no DB hit for tenant context)
- Fallback: older tokens without `org_id` fetch from DB
- Cross-tenant access attempts logged at 403
- `validate_sql_identifier()` used before all dynamic SQL
- All parameterized queries use `:param` syntax
- `# nosec B608` annotations only on validated identifiers

### Phase 23-26: SSRF, File Security, Rate Limiting ✅
- `validate_url()` blocks: localhost, private networks (10.x, 172.16.x, 192.168.x), link-local (169.254.x), IPv6 loopback/ULA, cloud metadata
- DNS resolution check prevents DNS rebinding
- File storage: UUID keys, path traversal protection, content-type guessing
- Rate limiting: `RateLimitMiddleware` (120 RPM default), Redis-backed when available
- No `pickle` deserialization anywhere in codebase

### Phase 27-29: CORS, Error Handling ✅
- CORS: explicit origins only, `*` rejected by `validate_config()`
- Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Allowed headers: Authorization, Content-Type, X-API-Key, X-Correlation-ID, X-Request-ID
- Global exception handler: logs + Sentry capture + generic message in production
- Validation error handler: strips `input` field to prevent XSS reflection
- HTTPException handler: consistent JSON with `request_id`
- Frontend: ErrorBoundary + global-error.tsx with error digest

### Phase 30-33: Frontend API Config, Pagination ✅
- `NEXT_PUBLIC_API_URL` → Render backend (with fallback)
- `next.config.js` rewrites: `/api/*` → Render, root endpoints → Render
- Frontend security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
- `poweredByHeader: false`
- PWA configured with service worker
- Jobs repository: proper `limit`/`offset` pagination
- Certificate list: proper `limit`/`offset` pagination

### Phase 34-39: Render, Docker, Environment ✅
- `render.yaml`: web service + worker service + Redis
- Worker has `APP_ENV=production`, `STORAGE_BACKEND`, `ALLOW_LOCAL_STORAGE_IN_PRODUCTION` (fixed)
- Dockerfile: non-root user (`appuser`), health check, dynamic PORT
- `--proxy-headers --forwarded-allow-ips='*'` for Render load balancer
- Alembic migration + schema verification before app start
- Redis: `allkeys-lru` eviction, internal-only IP allow list

### Phase 40-41: CI/CD ✅
- 6-stage CI pipeline: lint → security scan → unit tests → integration tests → build → deploy health check
- Lint: ruff, black, mypy, ESLint, TypeScript check
- Security: pip-audit, bandit, npm audit, Trivy filesystem scan, CodeQL
- Unit tests: SQLite, coverage report
- Integration tests: MySQL 8.4 + Redis 7, Alembic migrations
- Build: backend import check, Alembic migration check, frontend build, Docker build
- Deploy health check: pings Render `/health` (fixed from Vercel)
- `keep-render-awake.yml`: cron ping every 10 minutes
- Dependabot configured

### Phase 44-49: UX, Mobile, Observability ✅
- Viewport: `device-width`, `initialScale=1`, `userScalable=true`
- Mobile: sidebar drawer with overlay, auto-close on route change
- Content padding adapts: `p-4 md:p-6`
- PWA: manifest, service worker, apple touch icons
- ErrorBoundary: user-friendly fallback with retry
- Global error page: error digest for support reference
- Sentry + OpenTelemetry + Prometheus integration (no-op if not configured)

### Fixes Applied in This Audit Session

1. **`render.yaml` worker service**: Added missing `APP_ENV=production`, `STORAGE_BACKEND`, `ALLOW_LOCAL_STORAGE_IN_PRODUCTION` env vars
2. **`certificates/routes.py`**: Added `MAX_EXPORT_LIMIT=10000` safety cap to 4 unbounded export/report/presentation queries (CSV export, XLSX export, report, presentation)
3. **`.github/workflows/ci.yml`**: Fixed deploy health check to ping Render backend instead of Vercel

### Production Gate Checklist

| Check | Status |
|-------|--------|
| All tests pass (1682/0/1) | ✅ |
| No hardcoded secrets | ✅ |
| No localhost in production paths | ✅ |
| No TODO/FIXME items | ✅ |
| DB connection pooling configured | ✅ |
| Error handling sanitizes DB errors | ✅ |
| Health checks lightweight and correct | ✅ |
| Background worker no double-processing | ✅ |
| Tenant isolation 4-layer defense | ✅ |
| SQL injection prevention (validate_sql_identifier) | ✅ |
| SSRF protection (URL validation) | ✅ |
| File upload security (UUID keys, path traversal) | ✅ |
| Rate limiting configured | ✅ |
| CORS explicit origins only | ✅ |
| Frontend error boundaries | ✅ |
| Mobile responsive layout | ✅ |
| CI/CD pipeline complete | ✅ |
| Docker non-root user | ✅ |
| Render health check in CI | ✅ |
| Keep-alive cron for Render free tier | ✅ |
| Export query safety limits | ✅ |

### Remaining Recommendations (Non-Blocking)

1. **Rotate old secrets in git history**: Previous secrets (DataflowProd2026!, AdminPass2026!) exist in git history. Rotate passwords and keys if not already done.
2. **Production smoke test**: After Render redeploy, manually verify: login → Data to Decision → Upload → Process → Workflow completes.
3. **`audit_logs` index naming**: 4 indexes in SQLAlchemy model not in production MySQL (intentionally dropped/renamed in migrations). Low priority.
4. **Render plan upgrade**: Consider upgrading from `free` Redis plan for production reliability.
