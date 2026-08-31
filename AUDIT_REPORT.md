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
