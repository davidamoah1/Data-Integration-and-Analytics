# Performance Concerns

## Overview

Performance issues identified during the system audit that could impact scalability and user experience.

---

## CRITICAL

### PERF-C1: Permission Check Queries DB on Every Request
**Location**: `shared/dependencies.py:71-91`
**Description**: `get_current_user()` decodes the JWT, then queries the database for the user (`UserRepository.get_by_id`), then queries user roles (`UserRoleRepository.get_roles_for_user`), then queries all permissions (`UserRoleRepository.get_all_permissions_for_user`). This is 3+ DB queries on every authenticated request.
**Impact**: High database load under traffic. Latency on every API call.
**Fix**: Cache user roles and permissions in Redis with short TTL (e.g., 5 min). Invalidate on role/permission change.

### PERF-C2: No Pagination on List Endpoints
**Location**: Various backend routes
**Description**: Several list endpoints return all records without pagination. For example, dashboard listing, connector listing, and some dataset endpoints.
**Impact**: Memory exhaustion and slow responses as data grows.
**Fix**: Add `page` and `page_size` parameters to all list endpoints. Return paginated response format.

---

## HIGH

### PERF-H1: Frontend Dashboard Fetches All Data on Load
**Location**: `frontend/components/adaptive/AdaptiveDashboard.tsx:30-42`
**Description**: `loadData()` fetches both dashboards and datasets in parallel with no caching. Every dashboard visit triggers fresh API calls.
**Impact**: Slow dashboard load, unnecessary API calls.
**Fix**: Use SWR or React Query for client-side caching with stale-while-revalidate.

### PERF-H2: No Query Optimization for Permission Checks
**Location**: `authentication/repositories.py`
**Description**: `get_all_permissions_for_user()` likely joins `user_roles`, `role_permissions`, and `permissions` tables. Without composite indexes on `(user_id, role_id)` and `(role_id, permission_id)`, these joins are slow.
**Impact**: Slow auth on every request as user base grows.
**Fix**: Add composite indexes on `user_roles(user_id, role_id)` and `role_permissions(role_id, permission_id)`.

### PERF-H3: No Redis Caching Despite Configuration
**Location**: `config.py:80-83`, `performance/` module
**Description**: Redis is configured (`REDIS_URL`, `CACHE_ENABLED`) and the `performance/` module exists, but it's unclear if Redis caching is actually applied to hot paths (auth, datasets, dashboards).
**Impact**: Unnecessary database load. Performance module may be unused.
**Fix**: Verify Redis caching is applied to: permission checks, dashboard metadata, dataset schemas, KPI calculations.

### PERF-H4: Frontend Bundles All Adaptive Components
**Location**: `frontend/components/adaptive/`
**Description**: All adaptive components are statically imported. The `AdaptiveOnboarding` component (heavy) is bundled even for users who never see it.
**Impact**: Larger JavaScript bundle, slower initial page load.
**Fix**: Use `next/dynamic` for role-specific heavy components.

### PERF-H5: No Database Connection Pooling for SQLite
**Location**: `shared/database.py:56-68`
**Description**: SQLite engine is created without `check_same_thread=False` or pool settings. FastAPI uses async, which may require thread-safe SQLite access.
**Impact**: Potential "database is locked" errors under concurrent requests.
**Fix**: Add `connect_args={"check_same_thread": False}` for SQLite.

---

## MEDIUM

### PERF-M1: No Gzip on Frontend Static Assets
**Location**: `frontend/next.config.js`
**Description**: Next.js production build uses `output: 'standalone'` but no explicit compression configuration.
**Fix**: Enable compression in Next.js or rely on nginx gzip.

### PERF-M2: No Image Optimization
**Location**: `frontend/`
**Description**: No `next/image` usage for optimized images. Landing page uses inline SVGs but any future images would be unoptimized.
**Fix**: Use `next/image` for all images.

### PERF-M3: No Database Query Count Monitoring
**Location**: Throughout backend
**Description**: No instrumentation to track number of DB queries per request. N+1 query problems can go undetected.
**Fix**: Add SQLAlchemy event listeners to count queries in development/staging.

### PERF-M4: No API Response Caching Headers
**Location**: Throughout backend
**Description**: No `Cache-Control` or `ETag` headers on API responses. Clients cannot cache responses.
**Fix**: Add conditional response headers for cacheable endpoints (e.g., dashboard metadata, KPI lists).

### PERF-M5: Frontend Service Worker Unregistered on Every Load
**Location**: `frontend/app/layout.tsx:42-46`
**Description**: Inline script unregisters all service workers on every page load. PWA caching is defeated.
**Impact**: No offline support, no cached assets, slower repeat visits.
**Fix**: Remove the unregistration script or make it conditional on development only.

---

## LOW

### PERF-L1: No Lazy Loading for Studios Module
**Location**: `frontend/app/(app)/studios/`
**Description**: Studios module has 11 sub-routes. All are bundled in the main route.
**Fix**: Use route-level code splitting.

### PERF-L2: No Prefetching for Navigation Items
**Location**: `frontend/components/layout/Sidebar.tsx`
**Description**: Sidebar links do not use Next.js prefetching.
**Fix**: Add `prefetch` prop to sidebar `Link` components.

### PERF-L3: No Database Index on `activity_logs.created_at`
**Location**: `authentication/models.py:152-163`
**Description**: Activity logs are likely queried by date range but `created_at` is not indexed.
**Fix**: Add index on `created_at`.

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 5 |
| Medium | 5 |
| Low | 3 |
| **Total** | **15** |
