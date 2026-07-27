# DataFlow — Production Deployment Checklist & Next.js Migration Prep

## PART 14: Next.js Migration Preparation

### Current Architecture
```
Streamlit (dashboard/app.py) → Direct DB access + Semantic Engine + AI Gateway
FastAPI (api/main.py) → REST API with JWT auth, RBAC, audit logging
```

### Target Architecture
```
Next.js (frontend) → FastAPI (REST API) → Service Layer → MySQL
```

### API Readiness Assessment

The FastAPI backend is **already production-ready** for Next.js consumption:

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ✅ Ready | JWT + refresh tokens, RBAC with 7 roles |
| CORS | ✅ Ready | Configurable via `CORS_ORIGINS` env var |
| Response Format | ✅ Ready | Standardized `{success, data, error, meta}` envelope |
| API Documentation | ✅ Ready | OpenAPI/Swagger at `/docs` |
| Rate Limiting | ✅ Ready | 120 RPM configurable |
| Audit Logging | ✅ Ready | All actions logged |
| Multi-tenant | ✅ Ready | Organization isolation |

### API Endpoints for Next.js Frontend

| Feature | Endpoint | Method | Status |
|---------|----------|--------|--------|
| Login | `/auth/login` | POST | ✅ |
| Refresh | `/auth/refresh` | POST | ✅ |
| Users CRUD | `/users` | GET/POST/PUT/DELETE | ✅ |
| Roles | `/roles` | GET/POST | ✅ |
| Organizations | `/organizations` | GET/POST/PUT | ✅ |
| Audit Logs | `/audit/logs` | GET | ✅ |
| ETL Pipelines | `/etl/pipelines` | GET/POST | ✅ |
| AI Chat | `/ai/chat` | POST | ✅ |
| Analytics | `/analytics/kpis` | GET | ✅ |
| Semantic Analysis | `/semantic/analyze` | POST | ✅ |
| Validation | `/validation/validate` | POST | ✅ |
| Dataset Library | `/datasets` | GET/POST | ✅ |
| Performance | `/performance/metrics` | GET | ✅ |
| Notifications | `/notifications` | GET/POST | ✅ |
| Scheduler | `/scheduler/jobs` | GET/POST | ✅ |

### Migration Steps (When Ready)

1. **Create Next.js app** with App Router, TypeScript, Tailwind
2. **Install shadcn/ui** for component library
3. **Implement auth context** using `/auth/login` + `/auth/refresh`
4. **Build API client** with automatic token refresh
5. **Migrate dashboard pages** one by one:
   - Dashboard → `/dashboard` (uses `/analytics/kpis`)
   - Admin → `/admin` (uses `/users`, `/roles`)
   - Support → `/support`
   - Observability → `/observability`
6. **Replace Streamlit-specific rendering** with React components
7. **Deploy Next.js** to Vercel, FastAPI to Railway/Render

### What NOT to Migrate Yet
- Streamlit's `st.file_uploader` → Use Next.js file upload with `/etl/upload`
- Streamlit's `st.plotly_chart` → Use `react-plotly.js`
- Streamlit session state → Use React context/Zustand

---

## PART 15: Production Deployment Checklist

### Backend
- [x] FastAPI starts without errors
- [x] Environment variables configured (DB_TYPE, JWT_SECRET_KEY, etc.)
- [x] API documentation works at `/docs`
- [x] `validate_config()` runs at startup
- [x] CORS origins configured for production domain
- [x] Rate limiting enabled (120 RPM)
- [x] Security headers applied (CSP, X-Frame-Options, X-Content-Type-Options)

### Database
- [x] MySQL connection works with connection pooling
- [x] All tables created via `init_db()`
- [x] Indexes on all foreign keys and query columns
- [x] Composite indexes on (region, category) and (order_date, region)
- [x] Pipeline runs indexed on status + started_at
- [ ] **Production**: Configure MySQL backup strategy (daily + incremental)
- [ ] **Production**: Set up MySQL monitoring (slow query log, connection count)
- [ ] **Production**: Configure read replica for analytics queries

### Security
- [x] No hardcoded passwords in source code
- [x] Super admin password from `SUPER_ADMIN_PASSWORD` env var
- [x] Dashboard auth requires `AUTH_ADMIN_PASSWORD` / `AUTH_VIEWER_PASSWORD`
- [x] Argon2 password hashing
- [x] JWT with 30-min access token + 7-day refresh token
- [x] RBAC with 7 roles and 30+ permissions
- [x] Audit logging on all sensitive actions
- [x] Password history (5 passwords)
- [x] Account lockout after 5 failed attempts
- [x] JWT secret must be 32+ chars in production
- [x] CORS not `*` in production

### Performance
- [x] Redis caching with TTL (300s default)
- [x] Background workers (2-20, auto-scaling)
- [x] Chunked query support (5000 row default)
- [x] Connection pooling (10 connections)
- [ ] **Test**: 10,000 rows — should complete < 2s
- [ ] **Test**: 100,000 rows — should complete < 10s
- [ ] **Test**: 1,000,000 rows — should complete < 60s

### ETL
- [x] CSV extraction with UTF-8/latin-1 fallback
- [x] Excel (.xlsx, .xls) extraction
- [x] Unsupported format detection
- [x] Empty file detection
- [x] Transform: no assumptions about column existence
- [x] Transform: only drops rows for sales datasets with order_id
- [x] Load: batch insert with 1000-row batches
- [x] Load: duplicate detection via order_id
- [x] Load: SQLAlchemy error handling with rollback

### Semantic Engine
- [x] MIN_INDUSTRY_CONFIDENCE = 70.0 (was 40.0)
- [x] Weighted scoring: strong (3.0), medium (2.0), weak/universal (no vote)
- [x] Value-based signal detection (regex patterns for diagnosis codes, IBAN, etc.)
- [x] Tie-breaking with MIN_VOTE_MARGIN
- [x] Never silently chooses banking
- [x] Below 70%: "Industry detection uncertain"
- [x] 70-85%: Show recommendation, require confirmation
- [x] Above 85%: Auto-select

### Dashboard
- [x] Unknown datasets get generic analytics dashboard (not SME)
- [x] Confidence-based routing with user confirmation
- [x] Dataset isolation with unique UUID per upload
- [x] Auto-detect filter columns (not hardcoded to retail)
- [x] AI Copilot with suggested questions
- [x] Version footer shows v2.0.0

---

## Summary of Changes

### Files Changed
1. `semantic/semantic_engine.py` — MIN_INDUSTRY_CONFIDENCE: 40.0 → 70.0
2. `dashboard/sector_dashboards.py` — Generic dashboard for unknown, no SME fallback
3. `dashboard/semantic_dashboard.py` — Three-tier confidence routing (70/85/auto)
4. `dashboard/app.py` — Dataset isolation (UUID), generic filters, 70% threshold, v2.0.0
5. `dashboard/copilot.py` — Suggested questions for empty chat
6. `etl/extract.py` — Excel support, empty file detection, format validation
7. `etl/transform.py` — Safe column checks, no row dropping for non-sales data
8. `etl/load.py` — SQLAlchemy error handling, empty df check
9. `database/db_setup.py` — Pipeline runs indexes (status, started_at, composite)
10. `README.md` — Updated credentials and env var defaults
11. `docs/ENTERPRISE_AUDIT_V2.md` — Complete audit report (new)
12. `tests/test_enterprise_audit_fixes.py` — 16 new tests (new)

### Tests
- 16 new tests covering: confidence thresholds, weighted scoring, ETL extract/transform, dataset isolation, dashboard routing
- Full suite: 1169 passed, 1 skipped, 0 failures
