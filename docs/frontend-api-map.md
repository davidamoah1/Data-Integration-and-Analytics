# DataFlow — Frontend API Map

Complete reference of all FastAPI backend endpoints for Next.js frontend integration.

**Base URL**: `http://localhost:8000` (dev) / `https://api.dataflow.io` (prod)

**Auth**: Bearer token via `Authorization: Bearer <access_token>` header

**Response format**: `{ success: boolean, data: any, message: string }`

---

## Authentication (`/auth`)

| Endpoint | Method | Auth | Request Body | Response Data | Frontend Usage |
|----------|--------|------|--------------|---------------|----------------|
| `/auth/login` | POST | None | `{ email, password, remember_me? }` | `{ access_token, refresh_token, token_type, expires_in, user }` | Login page |
| `/auth/signup` | POST | None | `{ email, password, full_name, organization_name? }` | `{ id, email, full_name, organization_id }` | Signup page |
| `/auth/logout` | POST | Bearer | `{ refresh_token }` | `null` | Logout button |
| `/auth/refresh` | POST | None | `{ refresh_token }` | `{ access_token, refresh_token, expires_in }` | Auto token refresh |
| `/auth/change-password` | POST | Bearer | `{ current_password, new_password }` | `null` | Settings page |
| `/auth/forgot-password` | POST | None | `{ email }` | `null` | Forgot password page |
| `/auth/reset-password` | POST | None | `{ token, new_password }` | `null` | Reset password page |
| `/auth/profile` | GET | Bearer | — | `{ id, email, full_name, roles, permissions, organization }` | Profile dropdown |
| `/auth/profile` | PUT | Bearer | `{ full_name?, avatar_url?, phone?, language?, timezone? }` | Updated profile | Settings page |
| `/auth/sessions` | GET | Bearer | — | `[{ id, ip_address, user_agent, last_used, is_active }]` | Security settings |
| `/auth/sessions/{id}` | DELETE | Bearer | — | `null` | Revoke session |
| `/auth/login-history` | GET | Bearer | — | `[{ id, email, ip_address, success, created_at }]` | Security settings |
| `/auth/activity` | GET | Bearer | — | `[{ id, action, resource_type, created_at }]` | Activity feed |

## User Management (`/users`)

| Endpoint | Method | Auth | Permissions | Frontend Usage |
|----------|--------|------|-------------|----------------|
| `/users` | GET | Bearer | `users.read` | Admin user list |
| `/users` | POST | Bearer | `users.create` | Create user modal |
| `/users/{id}` | GET | Bearer | `users.read` | User detail |
| `/users/{id}` | PUT | Bearer | `users.edit` | Edit user |
| `/users/{id}` | DELETE | Bearer | `users.delete` | Delete user |
| `/users/{id}/roles` | POST | Bearer | `users.manage` | Assign roles |

## Role Management (`/roles`)

| Endpoint | Method | Auth | Permissions | Frontend Usage |
|----------|--------|------|-------------|----------------|
| `/roles` | GET | Bearer | `roles.read` | Admin roles list |
| `/roles` | POST | Bearer | `roles.manage` | Create role |
| `/roles/{id}` | PUT | Bearer | `roles.manage` | Edit role |
| `/roles/{id}` | DELETE | Bearer | `roles.manage` | Delete role |
| `/roles/permissions` | GET | Bearer | `roles.read` | Permissions matrix |

## Organizations (`/organizations`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/organizations` | GET | Bearer | Org selector |
| `/organizations` | POST | Bearer | Create org (admin) |
| `/organizations/{id}` | GET | Bearer | Org detail |
| `/organizations/{id}` | PUT | Bearer | Edit org |
| `/organizations/{id}` | DELETE | Bearer | Delete org |

## Departments (`/departments`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/departments` | GET | Bearer | Department list |
| `/departments` | POST | Bearer | Create department |
| `/departments/{id}` | GET/PUT/DELETE | Bearer | Department CRUD |

## Audit (`/audit`)

| Endpoint | Method | Auth | Permissions | Frontend Usage |
|----------|--------|------|-------------|----------------|
| `/audit/logs` | GET | Bearer | `audit.view` | Audit log table |
| `/audit/security` | GET | Bearer | `audit.view` | Security logs |
| `/audit/system` | GET | Bearer | `audit.view` | System logs |

## ETL (`/etl`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/etl/connectors/test` | POST | Bearer | Connector test |
| `/etl/connectors/discover` | POST | Bearer | Schema discovery |
| `/etl/import/upload` | POST | Bearer | File upload (multipart) |
| `/etl/import/preview` | POST | Bearer | Import preview |
| `/etl/import/execute` | POST | Bearer | Execute import |
| `/etl/profile` | POST | Bearer | Data profiling |
| `/etl/profiles/{job_id}` | GET | Bearer | Profile result |
| `/etl/quality/check` | POST | Bearer | Quality check |
| `/etl/quality/fix` | POST | Bearer | Apply quality fixes |
| `/etl/quality/reports/{job_id}` | GET | Bearer | Quality report |
| `/etl/transform` | POST | Bearer | Transform data |
| `/etl/transformations/templates` | GET/POST | Bearer | Template CRUD |
| `/etl/pipelines` | GET/POST | Bearer | Pipeline list/create |
| `/etl/pipelines/{id}` | GET/PUT | Bearer | Pipeline detail |
| `/etl/pipelines/{id}/execute` | POST | Bearer | Execute pipeline |
| `/etl/pipelines/{id}/versions` | GET | Bearer | Version history |
| `/etl/pipelines/{id}/rollback` | POST | Bearer | Rollback |
| `/etl/jobs` | GET | Bearer | Job list |
| `/etl/jobs/stats` | GET | Bearer | Job statistics |
| `/etl/jobs/{id}` | GET | Bearer | Job detail |
| `/etl/jobs/{id}/steps` | GET | Bearer | Job steps |
| `/etl/lineage` | GET | Bearer | Lineage graph |
| `/etl/schedules` | GET/POST | Bearer | Schedule CRUD |
| `/etl/schedules/{id}` | DELETE | Bearer | Delete schedule |
| `/etl/templates` | GET | Bearer | Import templates |
| `/etl/dashboard` | GET | Bearer | ETL dashboard |
| `/etl/ai/hooks` | GET | Bearer | AI hooks |

## Analytics (`/analytics`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/analytics/dashboards` | GET/POST | Bearer | Dashboard list/create |
| `/analytics/dashboards/{id}` | GET/PUT/DELETE | Bearer | Dashboard CRUD |
| `/analytics/dashboards/{id}/widgets` | POST | Bearer | Add widget |
| `/analytics/dashboards/{id}/widgets/{wid}` | DELETE | Bearer | Remove widget |
| `/analytics/dashboards/{id}/favorite` | POST | Bearer | Toggle favorite |
| `/analytics/kpis` | GET/POST | Bearer | KPI list/create |
| `/analytics/kpis/{id}` | GET | Bearer | KPI detail |
| `/analytics/kpis/{id}/record` | POST | Bearer | Record KPI value |
| `/analytics/kpis/{id}` | DELETE | Bearer | Delete KPI |
| `/analytics/alerts` | GET/POST | Bearer | Alert list/create |
| `/analytics/alerts/{id}/acknowledge` | POST | Bearer | Acknowledge alert |

## AI (`/ai`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/ai/chat` | POST | Bearer | AI Copilot chat |
| `/ai/chat/stream` | POST | Bearer | Streaming chat (SSE) |
| `/ai/conversations` | GET | Bearer | Conversation list |
| `/ai/conversations/{id}/messages` | GET | Bearer | Message history |
| `/ai/conversations/{id}` | DELETE | Bearer | Delete conversation |
| `/ai/conversations/search` | GET | Bearer | Search conversations |
| `/ai/conversations/{id}/export` | GET | Bearer | Export conversation |
| `/ai/messages/{id}/feedback` | POST | Bearer | Message feedback |
| `/ai/assistants` | GET | Bearer | List assistants |
| `/ai/providers` | GET/POST | Bearer | Provider list/create |
| `/ai/providers/{id}` | PUT | Bearer | Update provider |
| `/ai/providers/{name}/test` | POST | Bearer | Test provider |
| `/ai/sql/generate` | POST | Bearer | NL to SQL |
| `/ai/sql/execute` | POST | Bearer | Execute SQL |
| `/ai/etl/generate` | POST | Bearer | NL to ETL |
| `/ai/dashboard/generate` | POST | Bearer | NL to Dashboard |
| `/ai/quality/analyze` | POST | Bearer | AI quality analysis |
| `/ai/reports/generate` | POST | Bearer | AI report writer |
| `/ai/reports` | GET | Bearer | Report list |
| `/ai/reports/{id}` | GET | Bearer | Report detail |
| `/ai/reports/{id}/export` | GET | Bearer | Export report |
| `/ai/decision/analyze` | POST | Bearer | Decision center |
| `/ai/insights` | GET | Bearer | Insights list |
| `/ai/forecast` | POST | Bearer | Forecast |
| `/ai/forecasts` | GET | Bearer | Forecast list |
| `/ai/forecasts/{id}` | GET | Bearer | Forecast detail |
| `/ai/anomaly/detect` | POST | Bearer | Anomaly detection |
| `/ai/anomaly/alerts` | GET | Bearer | Anomaly alerts |
| `/ai/anomaly/alerts/{id}/resolve` | POST | Bearer | Resolve alert |
| `/ai/kpi/recommend` | POST | Bearer | KPI recommendations |
| `/ai/kpi/monitor` | GET | Bearer | KPI monitoring |

## Semantic Engine (`/semantic`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/semantic/entities` | GET | None | Entity browser |
| `/semantic/entities/{industry}` | GET | None | Industry entities |
| `/semantic/industries` | GET | None | Industry list |
| `/semantic/industries/{industry}` | GET | None | Industry detail |
| `/semantic/analyze` | POST | None (multipart) | Dataset analysis |
| `/semantic/analyze-with-overrides` | POST | None (multipart) | Analysis with overrides |
| `/semantic/detect-industry` | POST | None (multipart) | Quick industry detection |
| `/semantic/search` | POST | None | Semantic search |
| `/semantic/glossary` | GET | None | Business glossary |
| `/semantic/dashboard-registry/{industry}` | GET | None | Dashboard template |
| `/semantic/kpi-registry/{industry}` | GET | None | KPI definitions |
| `/semantic/widget-registry` | GET | None | Widget types |
| `/semantic/report-registry/{industry}` | GET | None | Report types |
| `/semantic/knowledge-graph/stats` | GET | None | KG statistics |
| `/semantic/health` | GET | None | Health check |

## Validation (`/validation`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/validation/run` | POST | None (multipart) | Run validation |
| `/validation/status/{id}` | GET | None | Validation status |
| `/validation/report/{id}` | GET | None | Validation report |
| `/validation/report/{id}/export` | GET | None | Export report |
| `/validation/approve/{id}` | POST | None | Approve validation |
| `/validation/reject/{id}` | POST | None | Reject validation |
| `/validation/rules` | GET | None | Validation rules |
| `/validation/rules/toggle` | POST | None | Toggle rule |
| `/validation/history` | GET | None | Validation history |
| `/validation/audit` | GET | None | Audit log |

## Dataset Library (`/datasets`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/datasets/` | GET | None | Dataset list |
| `/datasets/{id}` | GET | None | Dataset detail |
| `/datasets/{id}/preview` | GET | None | Data preview |
| `/datasets/{id}/schema` | GET | None | Schema info |
| `/datasets/production/upload` | POST | None | Register upload |
| `/datasets/production/database` | POST | None | Register DB connection |
| `/datasets/{id}` | DELETE | None | Remove dataset |
| `/datasets/industries/list` | GET | None | Industry list |
| `/datasets/tiers/list` | GET | None | Tier list |

## Notifications (`/notifications`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/notifications` | GET | Bearer | Notification list |
| `/notifications/{id}/read` | POST | Bearer | Mark read |
| `/notifications/{id}` | DELETE | Bearer | Delete notification |

## Scheduler (`/scheduler/reports`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/scheduler/reports` | GET/POST | Bearer | Scheduled reports |
| `/scheduler/reports/{id}/toggle` | POST | Bearer | Toggle schedule |
| `/scheduler/reports/{id}` | DELETE | Bearer | Delete schedule |
| `/scheduler/reports/sync` | POST | Bearer | Sync schedules |

## Platform Features (`/platform`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/platform/audit/summary` | GET | Bearer | Audit summary |
| `/platform/audit/categories` | GET | Bearer | Category stats |
| `/platform/audit/user/{id}` | GET | Bearer | User audit trail |
| `/platform/roles/hierarchy` | GET | Bearer | Role hierarchy |
| `/platform/roles/permissions-matrix` | GET | Bearer | Permissions matrix |
| `/platform/tenant/context` | GET | Bearer | Tenant context |
| `/platform/seed` | POST | Bearer | Seed enterprise data |

## Enterprise (`/platform`)

| Endpoint | Method | Auth | Frontend Usage |
|----------|--------|------|----------------|
| `/platform/templates` | GET/POST | Bearer | Template marketplace |
| `/platform/templates/{id}` | GET | Bearer | Template detail |
| `/platform/templates/{id}/install` | POST | Bearer | Install template |
| `/platform/templates/{id}/rate` | POST | Bearer | Rate template |
| `/platform/comments` | GET/POST | Bearer | Comments |
| `/platform/comments/{id}/resolve` | POST | Bearer | Resolve comment |
| `/platform/share` | POST | Bearer | Share resource |
| `/platform/shared` | GET | Bearer | Shared resources |
| `/platform/activity` | GET | Bearer | Activity timeline |
| `/platform/branding` | GET/PUT | Bearer | Branding settings |
| `/platform/search` | POST | Bearer | Enterprise search |
| `/platform/industry-packs` | GET | Bearer | Industry packs |
| `/platform/industry-packs/{key}` | GET | Bearer | Pack detail |
| `/platform/demo/seed` | POST | Bearer | Seed demo data |
| `/platform/demo/status` | GET | Bearer | Demo status |
| `/platform/subscription/plans` | GET | None | Pricing plans |
| `/platform/subscription/current` | GET | Bearer | Current subscription |
| `/platform/subscription/upgrade` | POST | Bearer | Upgrade plan |
| `/platform/subscription/cancel` | POST | Bearer | Cancel subscription |
| `/platform/subscription/features` | GET | None | Feature list |
| `/platform/subscription/feature-check` | GET | Bearer | Feature check |
| `/platform/subscription/feature-flag` | PUT | Bearer | Feature flag |
| `/platform/backups` | GET/POST | Bearer | Backup management |

## Performance (`/performance`)

| Endpoint | Method | Auth | Permissions | Frontend Usage |
|----------|--------|------|-------------|----------------|
| `/performance/overview` | GET | Bearer | `settings.manage` | Performance dashboard |
| `/performance/queue/stats` | GET | Bearer | `settings.manage` | Queue stats |
| `/performance/cache/stats` | GET | Bearer | `settings.manage` | Cache stats |
| `/performance/cache/clear` | DELETE | Bearer | `settings.manage` | Clear cache |
| `/performance/db/stats` | GET | Bearer | `settings.manage` | DB stats |
| `/performance/db/ensure-indexes` | POST | Bearer | `settings.manage` | Create indexes |

---

## Missing APIs (Identified for Frontend)

| Feature | Needed Endpoint | Priority |
|---------|----------------|----------|
| Dataset upload (direct) | `POST /datasets/upload` (multipart) | HIGH |
| Semantic analysis (JSON) | `POST /semantic/analyze-data` (JSON body, not multipart) | MEDIUM |
| Dashboard config by dataset | `GET /analytics/dashboards/by-dataset/{dataset_id}` | MEDIUM |
| User dashboard preferences | `GET/PUT /users/me/preferences` | LOW |
| System health check | `GET /health` | LOW |

---

## RBAC Roles & Permissions

| Role | Key Permissions |
|------|----------------|
| Super Admin | All permissions (bypasses checks) |
| Org Admin | `users.*`, `organizations.manage`, `departments.manage`, `audit.view` |
| Data Analyst | `datasets.view`, `analytics.view`, `ai.use`, `reports.view` |
| Dept Manager | `dashboard.view`, `reports.view`, `datasets.view` |
| Viewer | `dashboard.view`, `profile.update` |

## CORS Configuration
Backend allows origins: `http://localhost:8501,http://localhost:3000`
For production, set `CORS_ORIGINS=https://app.dataflow.io` env var.
