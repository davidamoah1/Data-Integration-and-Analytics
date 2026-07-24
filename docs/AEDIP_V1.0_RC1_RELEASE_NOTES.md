# AEDIP v1.0.0 RC1 — Release Notes

**Release:** 1.0.0 (Release Candidate 1)  
**Date:** 2026-07-23  
**Codename:** DataFlow Enterprise Data Intelligence Platform

---

## Executive Summary

AEDIP v1.0.0 RC1 is a production-hardened release candidate that consolidates the FastAPI backend, Streamlit dashboard, semantic layer, industry-specific analytics, AI Copilot, RBAC/IAM, audit logging, and containerized deployment. This RC fixes the critical default JWT secret exposure in Docker Compose, removes repository clutter, aligns all version strings to v1.0.0, resolves deprecation warnings, and validates the platform with 431 automated tests and a clean lint run.

---

## What Changed

### Security & Configuration
- `docker-compose.yml` no longer falls back to the insecure placeholder `change-this-to-a-strong-random-secret-min-32-chars` for `JWT_SECRET_KEY`. Startup now fails fast when the secret is missing, preventing accidental deployment with a well-known key.
- Streamlit server configuration fixed: removed `enableCORS = false` so XSRF protection is no longer silently disabled and the startup warning is gone.
- All API/dashboard version strings aligned to `v1.0.0`.

### Code Quality
- Replaced deprecated `datetime.utcnow()` with timezone-aware `datetime.now(timezone.utc).isoformat()` in `semantic/metadata_extractor.py` and `semantic/governance.py`.
- Removed duplicate root-level helper scripts: `init_super_admin.py` and `test_login.py` (functionality is covered by `database/db_setup.py` and the test suite).
- Cleaned temporary databases, `__pycache__`, `.pytest_cache`, `.ruff_cache`, and stale log files.
- Updated `test_api.py` assertion to match the new API root name.

### Version Alignment
- `pyproject.toml` version and description updated.
- `api/main.py` FastAPI and root endpoint versions updated.
- `README.md` title updated to v1.0.0.
- `dashboard/app.py` footer and empty-state copy made industry-neutral.

### Report Export (CSV / Excel / PDF)
- Added `services/report_export_service.py` with `ReportExportService` exporting any `AIReportGeneration` record to CSV, Excel (xlsx), or PDF using the persisted `data_sources` payload.
- New authenticated endpoint: `GET /ai/reports/{report_id}/export?format=csv|excel|pdf`.
- `ai/engines/report_writer.py` now stores gathered `report_data` in `AIReportGeneration.data_sources` so exports contain the underlying tables.
- Added `fpdf2==2.8.3` to `requirements.txt` for PDF generation.
- Added `tests/test_report_export.py` with 6 unit tests covering all supported formats.

### Notifications (Email / In-App / Stubs)
- Added `notifications/models.py` `Notification` table and `notifications/service.py` `NotificationService` supporting email (SMTP), in-app, and provider stubs for SMS, WhatsApp, and push.
- Wired workflow `notify` and `email` steps in `ai/workflow.py` to create in-app notifications and send email when SMTP is configured.
- Added `notifications/routes.py` with `GET /notifications`, `POST /notifications/{id}/read`, and `DELETE /notifications/{id}` endpoints.
- Registered `notifications.models` in `database/db_setup.py` and `tests/conftest.py`.
- Added `tests/test_notifications.py` and `tests/test_notifications_api.py` with unit/integration tests.

### Scheduled Reports
- Added `scheduler/models.py` `ScheduledReport` table to define cron-based recurring report jobs.
- Added `scheduler/report_scheduler.py` `ReportScheduler` using APScheduler to run `AIReportWriter` on cron schedules and notify the owner.
- Added `scheduler/routes.py` with `GET/POST /scheduler/reports`, `POST /scheduler/reports/{id}/toggle`, `DELETE /scheduler/reports/{id}`, and `POST /scheduler/reports/sync` endpoints.
- Wired `ReportScheduler` startup into `api/main.py` lifespan (disabled during tests via `PYTEST_RUNNING`).
- Registered `scheduler.models` in `database/db_setup.py`, `tests/conftest.py`, and `api/main.py` lifespan.
- Added `tests/test_scheduler.py` integration tests.

### Validation
- `python -m ruff check .` — passed.
- `python -m pytest tests/ -q` — **451 passed**.
- `python -c "import config; config.validate_config()"` — passed.
- `python -c "from api.main import app"` — passed.

---

## Migration Notes

### Local Development
No breaking changes. Existing SQLite databases and `.env` files continue to work.

Recommended steps after pulling this RC:
1. Ensure `.env` contains a strong `JWT_SECRET_KEY` (done automatically for local dev).
2. Run `python database/db_setup.py` to create/upgrade tables and seed default roles/users if needed.
3. Start the API and dashboard as usual:
   ```powershell
   Start-Process python -ArgumentList "-m uvicorn api.main:app --host 127.0.0.1 --port 8000" -WindowStyle Hidden
   Start-Process streamlit -ArgumentList "run dashboard/app.py --server.port 8501" -WindowStyle Hidden
   ```

### Docker / Production
- The `docker-compose.yml` `api` service now requires `JWT_SECRET_KEY` to be set in `.env` (no default fallback). Before running `docker compose up`, generate a strong secret and add it to `.env`.
- MySQL defaults remain in `docker-compose.yml` for local containerized testing; replace with production credentials and secrets before deploying.

### Alembic
- Migrations `0001` through `0007` are applied in order. New installs start from `Base.metadata.create_all` + `seed_default_data`; existing installations should run:
  ```bash
  alembic upgrade head
  ```

---

## Known Issues & Limitations

- **Real SMS/WhatsApp/push providers:** Email and in-app notifications are wired; SMS, WhatsApp, and push are stubs that need real providers (Twilio, WhatsApp Business, Firebase Cloud Messaging).
- **Scheduled report delivery:** Reports can be generated and exported on demand, but scheduled/background report jobs are not yet wired.
- **Redis:** No Redis-backed cache or rate limiter is wired. The current rate limiter is in-memory (suitable for single-worker deployments only).
- **Nginx / HTTPS:** `docker-compose.yml` exposes API and dashboard directly. Production deployments should add an Nginx reverse proxy with TLS termination and cert management.
- **Frontend:** The user-facing UI is Streamlit. A dedicated Next.js/React frontend with full WCAG/i18n support does not exist in this repository.
- **NL-to-SQL sandbox:** `ai/engines/nl_to_sql.py` validates SQL with keyword allow-lists and executes generated SQL directly. This is acceptable for demo/controlled use but should be hardened with read-only connections, row-level security, and a SQL parser sandbox before untrusted users can access it.
- **Industry report writer:** `ai/engines/report_writer.py` gathers summary data from a hardcoded `sales` table for executive/monthly/annual reports. It should be made semantic-model-driven in a future release.

---

## API Credentials (Local Dev)

- **FastAPI / REST:** `admin@dataflow.io` / `Admin@12345`
- **Streamlit dashboard:** `admin` / `admin123` and `viewer` / `viewer123`
- **OpenAPI docs:** http://127.0.0.1:8000/docs
- **Dashboard:** http://127.0.0.1:8501

---

## Next Steps Toward GA

1. Add scheduled/background report jobs.
2. Wire real SMS/WhatsApp/push notification providers.
3. Introduce Redis for caching, session store, and distributed rate limiting.
4. Add Nginx + TLS production compose variant.
5. Harden NL-to-SQL execution and add query cost/timeout guards.
6. Build or integrate a dedicated frontend (Next.js/React) if required for the target user experience.
