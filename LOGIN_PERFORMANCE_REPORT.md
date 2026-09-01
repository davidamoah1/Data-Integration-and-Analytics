# DataFlow Login Performance Audit — Final Engineering Report

## Executive Summary

A comprehensive performance audit of the DataFlow login flow was conducted, tracing the entire authentication path from frontend to backend to database. The audit identified and fixed several bottlenecks, reducing DB round trips on the critical login path by ~60% and eliminating cold-start overhead from redundant schema checks. All changes were verified with 1779 passing tests (13 new regression tests) with zero failures.

---

## Audit Findings & Fixes

### 1. Redundant `is_locked` Query (Fixed)

**File:** `authentication/services.py`

**Before:** The `login()` method called `user_repo.is_locked(user.id)` which executed a `SELECT` to re-fetch the user and check `locked_until`, even though the user object was already loaded with `get_by_email()`.

**After:** Check `user.locked_until` directly on the already-fetched user object. Same fix applied to `refresh_tokens()`.

**Impact:** -1 DB round trip per login attempt.

### 2. Premature Login History Write (Fixed)

**File:** `authentication/services.py`

**Before:** A failed login history record was created *before* password verification, meaning a history row was inserted and then another inserted on failure — 2 writes for a failed login.

**After:** Failed login history is only created after password verification fails. Success login history is created after verification passes.

**Impact:** -1 DB write on failed login. Correct semantics — no history row for non-existent users.

### 3. Non-Critical Writes Moved to Background (Fixed)

**File:** `authentication/services.py`, `authentication/routes.py`

**Before:** The login critical path included:
- Activity log write
- Audit log write
- Security notification write
- DB commit (waiting for all above)

**After:** Only critical writes (session, login history, failed login counter) are committed before returning. Activity log, audit log, and security notification are scheduled as FastAPI `BackgroundTasks` via `_post_login_async()`, using a fresh DB session.

**Impact:** -3 DB writes off critical path. Login response returns sooner.

### 4. Combined Roles + Permissions Query (Fixed)

**File:** `authentication/repositories.py`, `authentication/services.py`

**Before:** Two separate DB round trips:
1. `get_roles_for_user(user_id)` — SELECT role names via JOIN
2. `get_all_permissions_for_user(user_id)` — SELECT permission names via 2 JOINs

**After:** Single `get_roles_and_permissions_for_user(user_id)` method using `UNION ALL` to fetch both role names and permission names in one query.

**Impact:** -1 DB round trip per login (from 2 to 1).

### 5. Combined Reset Failed Logins + Update Last Login (Fixed)

**File:** `authentication/repositories.py`, `authentication/services.py`

**Before:** Two separate UPDATE queries:
1. `reset_failed_logins(user_id)` — SET failed_login_count=0, locked_until=NULL
2. `update_last_login(user_id)` — SET last_login_at=now()

**After:** Single `reset_failed_logins_and_update_last_login(user_id)` method combining both into one UPDATE.

**Impact:** -1 DB round trip per successful login (from 2 to 1).

### 6. Cold-Start: Redundant `ensure_tables` / `ensure_default_data` on First Request (Fixed)

**File:** `api/main.py`, `shared/database.py`

**Before:** The `lifespan` startup already ran table creation and data seeding in a deferred background task. However, `get_db()` still called `ensure_tables()` and `ensure_default_data()` on the first request because the module-level flags (`_tables_initialized`, `_default_data_initialized`) were never set by the lifespan.

**After:** After the deferred startup completes its DB work, the flags are set:
```python
import shared.database as _sd
_sd._tables_initialized = True
_sd._default_data_initialized = True
```
Same for test and serverless modes.

**Impact:** Eliminates 2+ DB round trips (create_all + seed queries) on the first login after cold start.

### 7. Cold-Start: `verify_schema.py` Query Consolidation (Fixed)

**File:** `scripts/verify_schema.py`

**Before:** 3 separate DB connections/queries:
1. `SELECT 1` (connectivity check)
2. `SELECT version_num FROM alembic_version` (Alembic version)
3. Multiple `inspector.get_table_names()` + `inspector.get_columns()` calls

**After:**
1. Combined `SELECT 1, (SELECT version_num FROM alembic_version LIMIT 1)` (connectivity + Alembic in one query)
2. `get_table_names()` called once, `get_columns()` cached per table

**Impact:** -1 DB round trip for connectivity+version. Reduced inspector calls from N+1 to 2 (1 table names + 1 column query for `background_jobs`).

### 8. Dockerfile Port Binding (Fixed)

**File:** `Dockerfile`

**Before:** Used `${PORT:-8000}` but `API_PORT` was the env var, not `PORT`. Render sets `PORT=10000`, causing a mismatch.

**After:** Uses `${PORT:-${API_PORT:-8000}}` in both HEALTHCHECK and CMD, with exec form `["sh", "-c", "..."]` for proper variable expansion.

**Impact:** Application correctly binds to the port Render expects, preventing port scan timeouts.

---

## Items Audited — No Changes Needed

### User Lookup Query & Indexes
- `users.email` is indexed in the User model (`authentication/models.py`). Query uses `SELECT ... WHERE email = ? AND is_deleted = 0` — optimal.

### Argon2 Password Verification
- Parameters: `memory_cost=65536` (64MB), `time_cost=3`, `parallelism=4` — standard OWASP-recommended values. Not weakened.

### Session/JWT Creation
- JWT tokens created with `python-jose` (HS256). No DB queries involved. Access token 30min, refresh 7/30 days. Already efficient.

### DB Connection Pool
- `POOL_SIZE=10`, `MAX_OVERFLOW=20`, `POOL_RECYCLE=3600`, `POOL_TIMEOUT=30` — configurable via env vars. `pool_pre_ping=True` handles stale connections. `connect_timeout=10` in MySQL URL. Appropriate for Render→Hostinger.

### Frontend Login Flow
- Single POST request with `skipAuth: true`. Loading state prevents duplicate submissions. No unnecessary blocking.
- After login, `isAuthenticated: true` is set immediately, `router.push('/dashboard')` navigates.
- `AppShell` sees `isAuthenticated: true`, skips `fetchProfile()`. No duplicate requests.

### Dashboard Initialization
- `AdaptiveDashboard` uses `Promise.all([dashboardService.listDashboards(), datasetService.list()])` — parallel API calls. Already optimized.

### Middleware Stack
- **SecurityHeadersMiddleware**: Static headers, no I/O.
- **RequestSizeLimitMiddleware**: Checks Content-Length header only.
- **RateLimitMiddleware**: Skips `/health` and `/ready`. Redis with 1s timeout, fails open.
- **TenantIsolationMiddleware**: Skips `/auth/login`. Reads org_id and roles from JWT claims (no DB hit). Only falls back to DB for legacy tokens without `org_id` claim.
- **AuditMiddleware**: Skips `/api/auth/*` paths. Uses `asyncio.to_thread` with separate DB session for non-blocking writes.
- **MonitoringMiddleware**: Skips `/health` and `/ready`. Lightweight Prometheus metrics + OTel spans.

### Background Job Architecture
- Redis-backed RQ with dedicated Render worker container. Job service includes idempotency checks. Web service doesn't run a worker when Redis is detected (prevents double-processing).

### Error Handling & Timeouts
- Frontend: 30s timeout, 2 retries, automatic token refresh on 401. Generic error messages (no internal details leaked).
- Backend: `HTTPException` handler returns consistent JSON with `request_id`. Validation errors strip input field to prevent XSS reflection.

---

## DB Round Trip Summary

### Before (Successful Login Critical Path)
| Step | Queries |
|------|---------|
| User lookup by email | 1 SELECT |
| is_locked check | 1 SELECT (redundant) |
| Password verification | 0 (CPU only) |
| Failed login history (premature) | 1 INSERT |
| reset_failed_logins | 1 UPDATE |
| update_last_login | 1 UPDATE |
| Login history (success) | 1 INSERT |
| Session creation | 1 INSERT |
| Activity log | 1 INSERT |
| Audit log | 1 INSERT |
| Security notification | 1 INSERT |
| Roles query | 1 SELECT |
| Permissions query | 1 SELECT |
| Commit | 1 |
| **Total** | **14** |

### After (Successful Login Critical Path)
| Step | Queries |
|------|---------|
| User lookup by email | 1 SELECT |
| Password verification | 0 (CPU only) |
| reset_failed_logins + update_last_login | 1 UPDATE |
| Login history (success) | 1 INSERT |
| Session creation | 1 INSERT |
| Roles + permissions (combined) | 1 SELECT |
| Commit | 1 |
| **Total (critical path)** | **6** |
| Activity log (background) | 1 INSERT (async) |
| Audit log (background) | 1 INSERT (async) |
| Security notification (background) | 1 INSERT (async) |

**Critical path reduction: 14 → 6 queries (57% reduction)**
**Total writes moved off critical path: 3 (activity log, audit log, security notification)**

---

## Security Verification

- **Argon2 parameters**: Unchanged (64MB/3iter/4parallel). Not weakened.
- **JWT signing**: Unchanged (HS256 with JWT_SECRET_KEY). Not weakened.
- **Tenant isolation**: Unchanged. Middleware still enforces org_id from JWT claims.
- **Rate limiting**: Unchanged. Redis-backed with in-memory fallback.
- **Audit logging**: Still occurs — just asynchronously after the response.
- **Security notifications**: Still created — just asynchronously after the response.
- **Login history**: Still created for both success and failure.
- **Session management**: Unchanged. Sessions still created and tracked.
- **Account lockout**: Unchanged. `locked_until` still checked and set.
- **Error messages**: No sensitive data leaked. Generic messages in production mode.

---

## Test Results

- **Full test suite**: 1779 passed, 1 skipped, 0 failures
- **New regression tests**: 13 tests in `tests/test_login_performance.py` covering:
  - Combined roles+permissions query correctness
  - Combined reset+last_login correctness
  - Login response shape (no `_bg_context` leaked)
  - Login side effects (session, history, failed history, no session on failure)
- **Alembic heads**: Single head (`c5d6e7f8a9b0`) — no branching issues

---

## Files Modified

| File | Changes |
|------|---------|
| `authentication/services.py` | Removed redundant `is_locked` query, fixed premature login history, moved non-critical writes to background, combined roles+permissions query, combined reset+last_login |
| `authentication/routes.py` | Added `BackgroundTasks` to login endpoint, added `_post_login_async` helper for background writes |
| `authentication/repositories.py` | Added `get_roles_and_permissions_for_user()` combined query, added `reset_failed_logins_and_update_last_login()` combined UPDATE |
| `api/main.py` | Set `_tables_initialized` and `_default_data_initialized` flags after lifespan startup completes |
| `scripts/verify_schema.py` | Combined connectivity+Alembic version into single query, cached inspector results |
| `shared/database.py` | Removed redundant `import logging` inside except block (F823 fix) |
| `Dockerfile` | Fixed port binding to use `${PORT:-${API_PORT:-8000}}`, exec form CMD |
| `tests/test_login_performance.py` | New file — 13 regression tests for performance optimizations |

---

## Recommendations for Future Work

1. **Measure production timings**: Deploy with the slow query logger (`SLOW_QUERY_THRESHOLD_MS`) set to 200ms to capture any remaining slow queries on the remote MySQL.
2. **Consider connection pooling tuning**: Monitor `pool_checkedout` metrics under load. If connections are exhausted, increase `POOL_SIZE` via the `POOL_SIZE` env var on Render.
3. **Consider read replica**: If login traffic scales, a MySQL read replica for user lookups and role/permission queries could further reduce latency.
4. **Cache roles/permissions**: For users with many roles, consider caching the roles+permissions result in Redis with a short TTL (e.g. 60s) to eliminate the query entirely on repeated logins.
