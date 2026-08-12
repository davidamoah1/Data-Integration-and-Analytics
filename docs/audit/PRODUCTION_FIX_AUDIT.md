# Production Fix Audit

**Status:** IN PROGRESS — first grounded inspection pass. Every finding below was
verified by reading the actual file/line at the time of writing. Items not yet
inspected are explicitly marked `NOT YET AUDITED` rather than assumed clean.

**Scope of this pass:** backend DB lifecycle, rate limiting, dataset workflow
state, frontend API client/Vercel config, frontend audit log component,
password hashing, and quick pattern sweeps (`create_all`, bare `except:`,
hardcoded secrets, `TODO`/`FIXME`, `console.log`). Full 46-part mandate
(RBAC matrix, OCR pipeline, PPTX export, accessibility, dark mode, CI green
run, etc.) has **not** been covered yet — see "Not Yet Audited" section.

---

## CRITICAL

### C1. `Base.metadata.create_all()` used as a production schema-creation path — FIXED
- **Where:** `@/d/etl_project/shared/database.py:48-68` (`ensure_tables()`, called from
  `get_db()` on every request, guarded only by an in-process boolean flag),
  `@/d/etl_project/api/main.py:216-227`, `@/d/etl_project/database/db_setup.py:57-80`,
  `@/d/etl_project/database/migrate_to_mysql.py` (called `create_all()` against the
  MySQL target with an incomplete/stale model import list — dozens of tables
  missing from its import block, so it would have silently created a partial
  schema).
- **Why it matters:** The mandate requires Alembic to be the *only* schema
  authority. `create_all()` builds tables straight from current ORM
  `Base.metadata`, independent of migration history. If it runs before/instead
  of `alembic upgrade head`, the live schema can diverge from what Alembic
  thinks it applied — structurally the same class of bug already hit three
  times in CI this week (FK type mismatches between models and migrations).
- **Fix applied:**
  - `shared/database.py::ensure_tables()` — now a no-op when `config.DB_TYPE
    == "mysql"` (still runs for SQLite: local dev, tests, SQLite-backed
    serverless cold starts).
  - `api/main.py` lifespan — `create_all()` call now skipped with a log line
    when `DB_TYPE == "mysql"`.
  - `database/db_setup.py::init_db()` — now raises `RuntimeError` if called
    with `DB_TYPE == "mysql"`, pointing at `alembic upgrade head` instead.
  - `database/migrate_to_mysql.py` — removed the `create_all()` call
    entirely; docstring/log now states the MySQL target schema must already
    exist via Alembic before running this data-copy script.
- **Verification:**
  - `ensure_tables()` confirmed to actually create tables under
    `DB_TYPE=sqlite` (ran against a fresh temp SQLite file).
  - `ensure_tables(None)` confirmed to return without touching the engine
    argument at all under `DB_TYPE=mysql` (passed `None` as the engine and it
    didn't error, proving `create_all` was never reached).
  - `pytest tests/test_repository.py tests/test_api.py` — 19/19 passed
    (SQLite-backed, exercises `db_setup.py`/repository code paths).
  - `black --check` and `ruff check` clean on all four touched files.
  - **Not yet verified:** an actual `DB_TYPE=mysql` FastAPI startup against a
    real MySQL instance (no live MySQL available in this session) — the
    no-op path is verified in isolation, not the full lifespan end-to-end.

### C2. In-memory rate limiter (`shared/middleware.py`)
- **Where:** `@/d/etl_project/shared/middleware.py:86-118` — `RateLimitMiddleware`
  stores hits in `self._hits: dict[str, list[float]]`, a plain Python dict on
  the middleware instance. Docstring literally says *"For production with
  multiple workers, replace with Redis-backed limiter."*
- **Why it matters:** Any deployment with more than one worker process (or
  serverless, where each invocation is a fresh process) gives every
  worker/instance its own independent counter — the limit is effectively
  `requests_per_minute × worker_count`, and restarts silently reset it.
  Login/signup/password-reset brute-force protection is not real in a
  multi-instance deployment.
- **Not yet fixed.** Needs a Redis-backed sliding-window or token-bucket
  implementation using `config.REDIS_URL`, applied at minimum to
  login/signup/password-reset per the mandate.

### C3. Dataset workflow state lives in a module-level Python object
- **Where:** `@/d/etl_project/services/dataset_workflow_routes.py:42-43`:
  ```python
  # Global orchestrator instance (in production, use Redis/DB for state)
  _orchestrator = DatasetWorkflowOrchestrator()
  ```
  `@/d/etl_project/services/dataset_workflow.py` implements the orchestrator's
  state machine in-memory (no DB/Redis persistence layer observed).
- **Why it matters:** Matches Part 8 exactly. A workflow started on one
  worker/instance is invisible to any other instance, and is lost entirely on
  restart or redeploy. This is incompatible with horizontal scaling,
  serverless, or rolling deploys.
- **Not yet fixed.** Requires persisting `WorkflowState`/`StageResult` to a
  MySQL table (job/workflow metadata) with Redis for queue coordination, per
  the mandate's Part 8/9 architecture. This is a substantial change — needs
  its own design pass before implementation (data model, backward
  compatibility with in-flight workflows, API contract for
  `/dataset-workflow/{id}/status` etc.).
- **Positive finding:** tenant isolation IS enforced on this router —
  `_ensure_workflow_access()` (`@/d/etl_project/services/dataset_workflow_routes.py:95-107`)
  checks `state.organization_id != user_org` and rejects with 403. The
  isolation logic is correct; only the storage medium is wrong.

### C4. ETL runs synchronously inside the HTTP request
- **Where:** `@/d/etl_project/services/dataset_workflow_routes.py:110-159`
  (`POST /dataset-workflow/run`) calls `_orchestrator.start(df, ...)` directly
  in the request handler, not via a queued background job.
- **Why it matters:** Matches Part 9. Large file processing will block the
  request/worker for the full pipeline duration, risking timeouts (especially
  on Vercel's 30s `maxDuration` set in `@/d/etl_project/vercel.json:37`) and
  preventing concurrent throughput.
- **Not yet fixed** — same dependency as C3 (needs durable job model +
  queue first).

### C5. Frontend audit log UI renders hardcoded fake data — FIXED
- **Where:** `@/d/etl_project/frontend/components/settings/AuditLogSettings.tsx`
  previously had a `mockEntries` array with literal names
  `kwame.mensah@org.com`, `ama.boateng@org.com`, fake IPs, and fixed
  timestamps, rendered directly with no API call at all.
- **Why it matters:** Exactly Part 18. Every organization using this UI saw
  identical fabricated "audit history" that never touched the backend audit
  log (`@/d/etl_project/audit/routes.py` has a real, working, org-scoped
  audit API — the component just never called it).
- **Fix applied:** Rewired to the existing
  `@/d/etl_project/frontend/services/audit/auditService.ts` (`listLogs`,
  `getFilters`). Removed `mockEntries`. Added: loading spinner, error state,
  empty state ("No activity has been recorded yet."), action filter (from
  `getFilters()`), date range filter, client-side search across
  action/resource/user, user-id → name resolution via `/api/users`, and a
  "Load more" pager against the real `total`/`offset`/`limit` from the API.
- **Verification:** `tsc --noEmit` clean, `eslint` clean, `npm run build`
  succeeded (production build, `/settings` route compiles). **Not yet
  verified:** manual browser test against a running backend with real audit
  log rows (no live backend/DB running in this session).

---

## HIGH

### H1. Vercel double `/api` prefix (FIXED this session)
- **Where:** `@/d/etl_project/vercel.json` previously set
  `NEXT_PUBLIC_API_URL: "/api"` while every frontend service
  (`@/d/etl_project/frontend/services/**`) already hardcodes the `/api/...`
  prefix in call paths, and `@/d/etl_project/frontend/services/api/client.ts`
  concatenates `${API_URL}${path}`. On Vercel this produced
  `/api/api/auth/login`, which does not match any FastAPI route (all backend
  routers are mounted with `prefix="/api/..."`, confirmed by grep across
  `authentication/routes.py`, `studios/routes.py`, `audit/routes.py`, etc.).
- **Fix applied:** `vercel.json` now sets `NEXT_PUBLIC_API_URL: ""`;
  `client.ts` fallback logic changed from `... || 'http://localhost:8001'`
  (which treated `""` as falsy and silently reverted to localhost) to an
  explicit `!== undefined` check so an intentional empty string is respected.
  Local dev (`frontend/.env.example` = `http://localhost:8000`) is unaffected.
- **Verification status:** Fix is logically verified against the actual
  backend route prefixes and the existing `vercel.json` rewrite
  (`/api/:path* → /api/index.py`), and JSON-validated. **Not yet verified
  against a real Vercel deployment** (no live environment available in this
  session) — recommend a smoke test of `/api/auth/login` on the next Vercel
  preview deploy before calling this fully closed.

---

## MEDIUM

*(Not yet exhaustively audited — placeholder pending deeper pass.)*

- `except Exception:` appears 97 times across 61 backend files
  (non-test code). A first pass shows no bare silent `except: pass` (searched
  and found zero matches), but a systematic review of whether each of the 97
  logs/re-raises appropriately vs. silently swallowing has **not** been done.
- Docker/Nginx/CI configuration referenced in `docker-compose.prod.yml`,
  `.github/workflows/*.yml` — not yet audited in this pass.

---

## LOW

*(Not yet audited.)*

---

## Verified Clean (no action needed)

- **Password hashing:** `@/d/etl_project/shared/security.py:31-50` uses
  `passlib.CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto", ...)`
  — Argon2 primary with proper memory/time cost params, bcrypt fallback for
  legacy hashes. No plaintext storage found.
- **Hardcoded credentials:** grep for `password = "..."`, `secret = "..."`,
  `api_key = "..."` literal-string patterns across all `.py` files
  (excluding tests) returned zero matches.
- **Bare `except:` / silent `except: pass`:** zero matches in `.py` files.
- **`console.log`:** zero matches across frontend `.ts`/`.tsx`.
- **`TODO`/`FIXME`:** zero matches across backend `.py` and frontend
  `.ts`/`.tsx` (excluding tests/node_modules).

---

## Not Yet Audited (explicitly out of scope for this pass)

To be honest about what has and hasn't been verified, per the mandate's own
rule against claiming unverified things work:

- Full RBAC permission matrix (Part 15) — roles exist in
  `@/d/etl_project/authentication/`, not yet cross-checked against the
  specific permission list in the mandate.
- Multi-tenant isolation (Part 16) — only spot-checked on the dataset
  workflow router. Not yet systematically tested against every
  organization-owned resource (datasets, files, reports, dashboards, jobs,
  users, audit logs) with a real cross-org access attempt.
- File storage backend (R2/S3/local) security (Part 10) — not yet audited.
- OCR/document processing pipeline (Part 11) — not yet audited.
- PPTX/PDF/Excel export — not yet verified by actually generating and
  opening a file (Part 12/26).
- Landing page content/UX (Part 28), accessibility (Part 29), responsive
  design (Part 30), dark mode (Part 31) — require visual/browser
  verification, not yet done.
- CI/CD pipeline health (Part 34) — three real bugs were found and fixed via
  live CI failures earlier in this workstream (FK type mismatches between
  MySQL/SQLite and ORM models across three commits); CI has not been
  re-verified green end-to-end since the last fix.
- New-account blank-workspace guarantee (Part 17) — not yet audited.
- Health/readiness endpoints (Part 37) and observability/logging (Part 38)
  — not yet audited.

---

## Next Steps

1. Decide fix order for C1–C5 (recommend C1 first — it's a single-file,
   low-risk gate; C3/C4 are the largest, needing a design pass for durable
   job storage before code changes).
2. Systematically test multi-tenant isolation (Part 16) with two real
   organizations before touching any resource-scoped endpoint.
3. Continue the "Not Yet Audited" list in priority order once C1–C5 have
   fixes with passing tests.
