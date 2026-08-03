# Technical Debt Report

## Overview

This report catalogs technical debt identified during the system audit, classified by severity.

---

## CRITICAL

### TD-C1: No Foreign Key Constraints in Database Models
**Location**: `authentication/models.py`, all model files
**Description**: Database tables use `BigInteger` columns for `user_id`, `role_id`, `organization_id`, etc. but define no `ForeignKey` constraints. Referential integrity is enforced only at the application layer.
**Impact**: Orphaned records possible if parent records are deleted without cleanup. Data corruption risk.
**Fix**: Add `ForeignKey('users.id')` etc. to all reference columns. Run Alembic migration.

### TD-C2: In-Memory Rate Limiter Not Production-Safe
**Location**: `shared/middleware.py:86-118`
**Description**: `RateLimitMiddleware` uses an in-memory `defaultdict` for rate tracking. With multiple workers or containers, each process has its own counter, effectively multiplying the rate limit.
**Impact**: Rate limiting is ineffective in production with multiple workers. API abuse possible.
**Fix**: Replace with Redis-backed rate limiter using sliding window algorithm.

### TD-C3: No Database Connection Pool for SQLite
**Location**: `shared/database.py:56-68`
**Description**: When using SQLite, no connection pool settings are applied. The engine is created with only `pool_pre_ping=True`.
**Impact**: Potential connection issues under concurrent load in development.
**Fix**: Add `check_same_thread=False` for SQLite, or use NullPool for serverless.

### TD-C4: Frontend Has No Error Recovery for API Failures
**Location**: `frontend/components/adaptive/AdaptiveDashboard.tsx`
**Description**: Dashboard fetches data with try/catch but the error state has no retry mechanism beyond `router.refresh()`. Other pages may silently fail.
**Impact**: Users see error states with no way to recover without manual page refresh.
**Fix**: Add retry buttons and exponential backoff for critical data fetches.

---

## HIGH

### TD-H1: No API Request/Response Schema Validation
**Location**: Throughout backend routes
**Description**: Many endpoints accept raw dicts or unvalidated inputs. While FastAPI supports Pydantic models, many routes use plain `dict` parameters.
**Impact**: Inconsistent API contract, potential injection points, harder client integration.
**Fix**: Define Pydantic request/response models for all endpoints.

### TD-H2: Stale Streamlit Dashboard Alongside Next.js Frontend
**Location**: `dashboard/app.py`, `docker-compose.prod.yml:86-117`
**Description**: The platform maintains both a Streamlit dashboard and a Next.js frontend. The Docker production setup runs both. This creates maintenance burden and confusion.
**Impact**: Dual maintenance, inconsistent UX, wasted resources in production.
**Fix**: Deprecate Streamlit dashboard. Remove from docker-compose.prod.yml. Migrate any remaining features to Next.js.

### TD-H3: Frontend Test Coverage Extremely Low
**Location**: `frontend/tests/` (only 4 files)
**Description**: Only `utils.test.ts` and a few others exist. No component tests, no integration tests, no E2E tests.
**Impact**: Regressions in UI go undetected. Role-based rendering cannot be verified automatically.
**Fix**: Add Vitest component tests for adaptive components. Add Playwright E2E tests for critical workflows.

### TD-H4: No API Versioning Strategy
**Location**: `api/main.py`
**Description**: Routes are registered at root level (`/auth/login`, `/datasets`, etc.) with no version prefix. Only legacy sales endpoints use `/api/v1/`.
**Impact**: Breaking changes affect all clients. No way to maintain backward compatibility.
**Fix**: Introduce `/v1/` prefix for all routes. Use FastAPI APIRouter prefix.

### TD-H5: Hardcoded Fallback CORS for Development
**Location**: `api/main.py:362-374`
**Description**: When `CORS_ORIGINS` env var is not set, the API falls back to a regex allowing any `localhost` or `127.0.0.1` origin. This is insecure if deployed without proper env config.
**Impact**: Potential CORS misconfiguration in staging/production if env vars are missing.
**Fix**: Require explicit CORS_ORIGINS in non-development environments. Fail fast if missing.

### TD-H6: No Database Index on Critical Query Paths
**Location**: Various models
**Description**: While primary keys and some columns are indexed, several frequently queried columns lack indexes (e.g., `role_permissions.permission_id`, `user_roles.role_id` composite index).
**Impact**: Slow queries as data grows, especially for permission checks on every request.
**Fix**: Add composite indexes on frequently joined columns.

---

## MEDIUM

### TD-M1: Mixed Response Formats
**Location**: Throughout backend
**Description**: Some endpoints use `success_response()` wrapper (`{success, data, message}`), others return raw dicts or lists. The notifications router returns a plain list, while audit returns `{logs, total, page, page_size}`.
**Impact**: Frontend must handle multiple response shapes, leading to bugs (e.g., audit page crash).
**Fix**: Standardize all API responses to use `success_response()` wrapper.

### TD-M2: Duplicate Route Registration
**Location**: `api/main.py:384, 413`
**Description**: `admin_router` is imported from both `admin.routes` and `saas.admin_routes`, and both are registered. The `saas.admin_routes` import overwrites the `admin.routes` import variable.
**Impact**: Route conflicts, unpredictable behavior, potential shadowed endpoints.
**Fix**: Rename imports to avoid collision (e.g., `saas_admin_router`).

### TD-M3: Frontend Auth State Persisted in localStorage
**Location**: `frontend/stores/authStore.ts:117-124`
**Description**: Zustand persists `user` and `isAuthenticated` in localStorage. On page load, the app considers the user authenticated before verifying the token with the backend.
**Impact**: Stale auth state if token expires. User sees authenticated UI briefly before redirect.
**Fix**: Only persist tokens (not user object). Fetch profile on app load to verify.

### TD-M4: No Request Pagination on Several Endpoints
**Location**: Various routes
**Description**: Several list endpoints return all records without pagination (e.g., some dataset, dashboard, and connector endpoints).
**Impact**: Performance degradation with large datasets.
**Fix**: Add pagination parameters (page, page_size) to all list endpoints.

### TD-M5: No Environment-Based Configuration for Frontend
**Location**: `frontend/services/api/client.ts:1`
**Description**: API URL defaults to `http://localhost:8001`. The `.env.local` file is nearly empty (2 bytes). No environment-specific configuration for staging/production.
**Impact**: Frontend may fail to connect to backend in deployed environments.
**Fix**: Document required env vars. Add validation for `NEXT_PUBLIC_API_URL`.

### TD-M6: Alembic Migrations May Be Out of Sync
**Location**: `alembic/versions/`
**Description**: The app uses both `Base.metadata.create_all()` and Alembic migrations. This dual approach can lead to schema drift.
**Impact**: Migration state may not reflect actual database schema.
**Fix**: Use Alembic as the sole schema management tool. Disable `create_all()` in production.

---

## LOW

### TD-L1: Unused Import in API Main
**Location**: `api/main.py:98`
**Description**: `from saas.admin_routes import admin_router` shadows the earlier `from admin.routes import router as admin_router`. Both are registered on lines 384 and 413.
**Fix**: Rename to `saas_admin_router`.

### TD-L2: Service Worker Unregistration Script
**Location**: `frontend/app/layout.tsx:42-46`
**Description**: Inline script unregisters all service workers on page load. This defeats PWA caching.
**Fix**: Remove or conditionally apply only during development.

### TD-L3: No Code Splitting for Adaptive Components
**Location**: `frontend/components/adaptive/`
**Description**: All adaptive components are statically imported. Role-specific components (e.g., AdaptiveOnboarding) are bundled even if never used by the current user.
**Fix**: Use dynamic imports for role-specific heavy components.

### TD-L4: Test Database Files in Repository Root
**Location**: `alembic_v31_test.db`, `test_auth.db`, `dataflow.db`
**Description**: SQLite test database files are present in the repository root.
**Fix**: Add to `.gitignore` and remove from repository.

### TD-L5: No Linting Configuration for Python
**Location**: `pyproject.toml`
**Description**: While `ruff` cache exists, there's no explicit ruff configuration in `pyproject.toml` beyond basic settings.
**Fix**: Add comprehensive ruff ruleset and enforce in CI.
