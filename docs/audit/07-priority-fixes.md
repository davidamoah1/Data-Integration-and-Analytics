# Priority Fixes

## Overview

Consolidated priority list of all findings from the audit, ranked by severity and effort. This is the recommended execution order for Phase 2.

---

## P0 — Critical (Must Fix Before Production)

| # | Finding | Category | Effort | Reference |
|---|---------|----------|--------|-----------|
| 1 | Remove insecure JWT secret default; require explicit env var | Security | Low | SEC-C1 |
| 2 | Separate encryption key for API key encryption from JWT secret | Security | Low | SEC-C2 |
| 3 | Add foreign key constraints to all database models | Tech Debt | Medium | TD-C1 |
| 4 | Replace in-memory rate limiter with Redis-backed limiter | Tech Debt | Medium | TD-C2 |
| 5 | Cache permission checks in Redis (3+ DB queries per request) | Performance | Medium | PERF-C1 |
| 6 | Complete password reset flow (frontend + backend) | Missing Feature | Medium | MF-C1 |
| 7 | Add email verification flow | Missing Feature | Medium | MF-C2 |
| 8 | Create search results page | Missing Feature | Medium | MF-C3 |
| 9 | Fix audit page API response handling (partially done) | Broken Workflow | Low | BW-C1 |
| 10 | Connect onboarding flow to AdaptiveOnboarding + backend | Broken Workflow | Medium | BW-C3 |

---

## P1 — High (Fix Before Enterprise Rollout)

| # | Finding | Category | Effort | Reference |
|---|---------|----------|--------|-----------|
| 11 | Add Pydantic request/response models for all endpoints | Tech Debt | High | TD-H1 |
| 12 | Add stricter rate limiting on auth endpoints | Security | Low | SEC-H3 |
| 13 | Add CSP header to frontend | Security | Low | SEC-H4 |
| 14 | Enforce tenant isolation on all org-scoped routes | Security | High | SEC-H5 |
| 15 | Sanitize AI endpoint inputs (prompt injection) | Security | Medium | SEC-H1 |
| 16 | Deprecate Streamlit dashboard | Tech Debt | Low | TD-H2 |
| 17 | Add frontend test coverage (Vitest + Playwright) | Tech Debt | High | TD-H3 |
| 18 | Introduce API versioning (`/v1/` prefix) | Tech Debt | Medium | TD-H4 |
| 19 | Standardize API response format (success_response everywhere) | Tech Debt | Medium | TD-M1 |
| 20 | Add pagination to all list endpoints | Performance | Medium | PERF-C2 |
| 21 | Build notification delivery system (polling or WebSocket) | Missing Feature | High | MF-H4 |
| 22 | Build user profile management UI | Missing Feature | Medium | MF-H1 |
| 23 | Build organization settings UI | Missing Feature | Medium | MF-H2 |
| 24 | Build API key management UI | Missing Feature | Medium | MF-H6 |
| 25 | Connect demo & contact forms to backend | Broken Workflow | Low | BW-H2, BW-H3 |
| 26 | Add 2FA/MFA support | Missing Feature | High | MF-M6 |
| 27 | Add session revocation check on every request | Security | Medium | SEC-M3 |
| 28 | Add file upload MIME type validation | Security | Low | SEC-M4 |
| 29 | Add database composite indexes for permission queries | Performance | Low | PERF-H2 |
| 30 | Add Redis caching to hot paths | Performance | Medium | PERF-H3 |

---

## P2 — Medium (Post-Launch Improvements)

| # | Finding | Category | Effort | Reference |
|---|---------|----------|--------|-----------|
| 31 | Fix duplicate route registration (admin_router) | Tech Debt | Low | TD-M2 |
| 32 | Fix frontend auth state persistence (localStorage) | Tech Debt | Medium | TD-M3 |
| 33 | Require explicit CORS_ORIGINS in non-dev environments | Tech Debt | Low | TD-H5 |
| 34 | Use Alembic as sole schema management tool | Tech Debt | Medium | TD-M6 |
| 35 | Add frontend env var validation | Tech Debt | Low | TD-M5 |
| 36 | Remove debug mode error detail exposure | Security | Low | SEC-M1 |
| 37 | Add generic auth error messages (no enumeration) | Security | Low | SEC-M2 |
| 38 | Add audit logging for security-critical events | Security | Medium | SEC-M5 |
| 39 | Build department management UI | Missing Feature | Medium | MF-H3 |
| 40 | Build feature flag management UI | Missing Feature | Medium | MF-H5 |
| 41 | Build webhook management UI | Missing Feature | Medium | MF-H7 |
| 42 | Build billing/subscription management UI | Missing Feature | High | MF-H8 |
| 43 | Add data export/download | Missing Feature | Low | MF-M1 |
| 44 | Build report scheduling UI | Missing Feature | Medium | MF-M2 |
| 45 | Complete user invitation flow | Missing Feature | Medium | MF-M3 |
| 46 | Add session management UI | Missing Feature | Medium | MF-M7 |
| 47 | Connect TopNav notifications to API | Broken Workflow | Low | BW-H1 |
| 48 | Use SWR/React Query for frontend caching | Performance | Medium | PERF-H1 |
| 49 | Dynamic import role-specific components | Performance | Low | PERF-H4 |
| 50 | Remove service worker unregistration script | Performance | Low | PERF-M5 |

---

## P3 — Low (Backlog / Polish)

| # | Finding | Category | Effort | Reference |
|---|---------|----------|--------|-----------|
| 51 | Remove test DB files from repository | Tech Debt | Low | TD-L4 |
| 52 | Add ruff linting rules and CI enforcement | Tech Debt | Low | TD-L5 |
| 53 | Add HSTS header to frontend | Security | Low | SEC-L1 |
| 54 | Add i18n support | Missing Feature | High | MF-L2 |
| 55 | Add keyboard shortcuts documentation | Missing Feature | Low | MF-L3 |
| 56 | Add onboarding completion tracking | Missing Feature | Low | MF-L4 |
| 57 | Add image optimization (next/image) | Performance | Low | PERF-M2 |
| 58 | Add route-level code splitting for studios | Performance | Low | PERF-L1 |
| 59 | Add prefetching for sidebar links | Performance | Low | PERF-L2 |
| 60 | Add database index on activity_logs.created_at | Performance | Low | PERF-L3 |

---

## Summary

| Priority | Count | Estimated Effort |
|----------|-------|-----------------|
| P0 (Critical) | 10 | ~15 person-days |
| P1 (High) | 20 | ~45 person-days |
| P2 (Medium) | 20 | ~35 person-days |
| P3 (Low) | 10 | ~10 person-days |
| **Total** | **60** | **~105 person-days** |

### Recommended Phase 2 Focus

1. **Week 1-2**: P0 items 1-5 (security + performance foundation)
2. **Week 3-4**: P0 items 6-10 (user-facing critical workflows)
3. **Week 5-8**: P1 items 11-30 (enterprise readiness)
4. **Week 9-12**: P2 items 31-50 (post-launch improvements)
5. **Ongoing**: P3 items as bandwidth allows
