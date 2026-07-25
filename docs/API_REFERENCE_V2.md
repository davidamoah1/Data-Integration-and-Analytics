# DataFlow API Reference v2.0

> Base URL: `http://localhost:8000`
> Interactive docs: `http://localhost:8000/docs` (Swagger UI)
> ReDoc: `http://localhost:8000/redoc`

## Authentication

All endpoints except `/auth/login`, `/auth/signup`, `/auth/refresh`, `/health`, and `/ready` require a JWT Bearer token:

```
Authorization: Bearer <access_token>
```

### Obtain a token

```bash
POST /auth/login
Content-Type: application/json

{
  "email": "admin@dataflow.io",
  "password": "Admin@12345"
}
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### Refresh a token

```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

---

## Standard Response Format

All endpoints return a consistent envelope:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

---

## 1. Authentication (`/auth`)

| Method | Path | Description | Auth | Permissions |
|--------|------|-------------|------|-------------|
| POST | `/auth/login` | Authenticate and receive JWT tokens | None | Public |
| POST | `/auth/signup` | Public self-registration | None | Public |
| POST | `/auth/logout` | Revoke current session | Bearer | Any user |
| POST | `/auth/refresh` | Refresh access token | None (refresh token in body) | Public |
| POST | `/auth/change-password` | Change current user's password | Bearer | Any user |
| POST | `/auth/forgot-password` | Request password reset email | None | Public |
| POST | `/auth/reset-password` | Reset password with token | None | Public |
| GET | `/auth/profile` | Get current user's profile | Bearer | Any user |
| PUT | `/auth/profile` | Update current user's profile | Bearer | Any user |
| GET | `/auth/sessions` | List active sessions | Bearer | Any user |
| DELETE | `/auth/sessions/{session_id}` | Revoke a session | Bearer | Any user |
| GET | `/auth/login-history` | Get login history | Bearer | Any user |
| GET | `/auth/activity` | Get activity log | Bearer | Any user |

### Example: Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@dataflow.io", "password": "Admin@12345"}'
```

---

## 2. User Management (`/users`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/users` | List all users (paginated) | `users.read` |
| POST | `/users` | Create a new user | `users.create` |
| GET | `/users/{user_id}` | Get a specific user | `users.read` |
| PUT | `/users/{user_id}` | Update a user | `users.update` |
| DELETE | `/users/{user_id}` | Soft-delete a user | `users.delete` |
| POST | `/users/{user_id}/roles` | Assign roles to a user | `users.assign_roles` |

### Example: List users

```bash
curl http://localhost:8000/users?page=1&page_size=20 \
  -H "Authorization: Bearer <token>"
```

---

## 3. Role Management (`/roles`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/roles` | List all roles | `roles.read` |
| POST | `/roles` | Create a custom role | `roles.create` |
| GET | `/roles/permissions` | List all permissions | `roles.read` |
| GET | `/roles/{role_id}` | Get a specific role | `roles.read` |
| PUT | `/roles/{role_id}` | Update a role | `roles.update` |
| DELETE | `/roles/{role_id}` | Delete a non-system role | `roles.delete` |

### System Roles

| Role | Description |
|------|-------------|
| `super_admin` | Full platform access |
| `org_admin` | Organization-level administration |
| `analyst` | Data analysis and dashboard access |
| `manager` | Manage pipelines and reports |
| `viewer` | Read-only dashboard access |

---

## 4. Organization Management (`/organizations`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/organizations` | List organizations | `organizations.read` |
| POST | `/organizations` | Create an organization | `organizations.create` |
| GET | `/organizations/{org_id}` | Get an organization | `organizations.read` |
| PUT | `/organizations/{org_id}` | Update an organization | `organizations.update` |
| DELETE | `/organizations/{org_id}` | Delete an organization | `organizations.delete` |

---

## 5. Audit Endpoints (`/audit`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/audit/logs` | List audit logs (paginated) | `audit.view` |
| GET | `/audit/security` | List security logs | `audit.view` |
| GET | `/audit/system` | List system logs | `audit.view` |

---

## 6. Sales & KPIs (`/api/v1`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/sales` | Sales data with filters | Bearer or API Key |
| GET | `/api/v1/kpis` | KPI aggregation | Bearer or API Key |
| GET | `/api/v1/filters` | Filter options (regions, categories) | Bearer or API Key |
| POST | `/api/v1/pipeline/trigger` | Trigger ETL pipeline | Bearer |
| GET | `/api/v1/pipeline/runs` | Pipeline run history | Bearer |

### Example: Get sales with filters

```bash
curl "http://localhost:8000/api/v1/sales?region=Greater%20Accra&category=Electronics&date_from=2024-01-01&date_to=2024-12-31" \
  -H "Authorization: Bearer <token>"
```

---

## 7. AI Intelligence (`/ai`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| POST | `/ai/chat` | AI chat with data context | `ai.chat` |
| GET | `/ai/assistants` | List AI assistants | `ai.assistants.read` |
| POST | `/ai/assistants` | Create an AI assistant | `ai.assistants.create` |
| POST | `/ai/quality-score` | Score data quality | `ai.quality_score` |
| POST | `/ai/anomaly-detection` | Detect anomalies in data | `ai.anomaly_detection` |
| POST | `/ai/forecast` | Time-series forecasting | `ai.forecast` |
| POST | `/ai/document-chat` | Chat with documents (PDF, DOCX, XLSX) | `ai.document_chat` |

### Example: AI Chat

```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the total revenue by region?", "context": {"dataset": "retail_demo"}}'
```

---

## 8. Analytics (`/analytics`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/analytics/dashboards` | List dashboards | `analytics.read` |
| POST | `/analytics/dashboards` | Create a dashboard | `analytics.create` |
| GET | `/analytics/dashboards/{id}` | Get a dashboard | `analytics.read` |
| GET | `/analytics/widgets` | List widgets | `analytics.read` |
| GET | `/analytics/kpis` | List KPIs | `analytics.read` |
| GET | `/analytics/alerts` | List alerts | `analytics.read` |
| POST | `/analytics/alerts` | Create an alert | `analytics.create` |

---

## 9. Africa Intelligence (`/africa`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/africa/countries` | List all country profiles | Bearer |
| GET | `/africa/countries/{code}` | Get a specific country profile | Bearer |
| POST | `/africa/convert-currency` | Convert between currencies | Bearer |
| GET | `/africa/industries/{country_code}` | List industries for a country | Bearer |
| POST | `/africa/recognize` | Recognize African data patterns in columns | Bearer |

### Example: Currency conversion

```bash
curl -X POST http://localhost:8000/africa/convert-currency \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "from": "GHS", "to": "USD"}'
```

Response:
```json
{
  "success": true,
  "data": {
    "amount": 1000,
    "from": "GHS",
    "to": "USD",
    "rate": 0.0769,
    "converted": 76.92
  }
}
```

---

## 10. Performance (`/performance`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/performance/overview` | Cache + DB stats overview | `performance.view` |
| GET | `/performance/queue/stats` | Task queue statistics | `performance.view` |
| GET | `/performance/cache/stats` | Cache hit/miss stats | `performance.view` |
| DELETE | `/performance/cache/clear` | Clear entire cache | `performance.manage` |
| DELETE | `/performance/cache/namespace/{ns}` | Clear namespace | `performance.manage` |
| GET | `/performance/db/stats` | Database statistics | `performance.view` |
| POST | `/performance/db/ensure-indexes` | Create critical indexes | `performance.manage` |
| GET | `/performance/db/indexes/{table}` | List table indexes | `performance.view` |

### Example: Get performance overview

```bash
curl http://localhost:8000/performance/overview \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "success": true,
  "data": {
    "cache": {
      "hits": 1245,
      "misses": 87,
      "hit_rate": 93.5,
      "backend": "memory",
      "memory_size": 42
    },
    "database": {
      "table_count": 12,
      "total_rows": 45200,
      "index_count": 18
    }
  }
}
```

---

## 11. Platform Features (`/platform`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/platform/industry-packs` | List industry packs | Any user |
| GET | `/platform/connectors` | List data connectors | `platform.read` |
| POST | `/platform/connectors/{id}/test` | Test a connector | `platform.manage` |
| GET | `/platform/workflows` | List workflows | `platform.read` |
| POST | `/platform/workflows` | Create a workflow | `platform.manage` |
| GET | `/platform/notifications` | List notifications | Any user |
| GET | `/platform/reports` | List reports | `platform.read` |
| POST | `/platform/reports` | Create a report | `platform.create` |
| GET | `/platform/search` | Universal search | Any user |

---

## 12. Enterprise (`/enterprise`)

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/enterprise/templates` | List templates | `enterprise.read` |
| POST | `/enterprise/templates/{id}/install` | Install a template | `enterprise.manage` |
| GET | `/enterprise/branding` | Get organization branding | `enterprise.read` |
| PUT | `/enterprise/branding` | Update branding | `enterprise.manage` |
| GET | `/enterprise/activity` | Get activity feed | `enterprise.read` |

---

## 13. Health & Monitoring

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Health check (liveness) | None |
| GET | `/ready` | Readiness check | None |
| GET | `/metrics` | Platform metrics | Bearer |

### Health check response

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## Rate Limiting

- Default: 120 requests per minute per IP
- Configurable via `RATE_LIMIT_RPM` environment variable
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

---

## SDK Examples

### Python

```python
import requests

base_url = "http://localhost:8000"

# Login
resp = requests.post(f"{base_url}/auth/login", json={
    "email": "admin@dataflow.io",
    "password": "Admin@12345"
})
token = resp.json()["data"]["access_token"]

# Authenticated request
headers = {"Authorization": f"Bearer {token}"}
sales = requests.get(f"{base_url}/api/v1/sales", headers=headers)
print(sales.json())
```

### JavaScript

```javascript
const baseUrl = "http://localhost:8000";

// Login
const loginResp = await fetch(`${baseUrl}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "admin@dataflow.io", password: "Admin@12345" })
});
const { data } = await loginResp.json();
const token = data.access_token;

// Authenticated request
const sales = await fetch(`${baseUrl}/api/v1/sales`, {
  headers: { Authorization: `Bearer ${token}` }
});
const salesData = await sales.json();
```

---

## Default Credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@dataflow.io` | `Admin@12345` | super_admin |
| `viewer@dataflow.io` | `Viewer@12345` | viewer |

---

*DataFlow API v2.0.0 — AEDIP*
