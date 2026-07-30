# API Examples

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Practical API request/response examples.

## Scope

Common API operations with curl examples.

## Audience

API consumers and developers.

---

## 1. Authentication

### Login

```bash
curl -X POST /api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Password123!"}'
```

**Response** (200):
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "rt_abc123...",
    "user": { "id": 1, "email": "admin@example.com", "full_name": "Admin" }
  }
}
```

### Error (401):
```json
{ "success": false, "message": "Invalid email or password", "data": null }
```

## 2. User Management

### List Users

```bash
curl -X GET "/api/users?page=1&page_size=20" \
  -H "Authorization: Bearer eyJ..."
```

**Response** (200):
```json
{
  "success": true,
  "message": "Users retrieved",
  "data": {
    "items": [
      { "id": 1, "email": "user@example.com", "full_name": "John Doe" }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### Create User

```bash
curl -X POST "/api/users" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"email": "new@example.com", "password": "Pass123!", "full_name": "New User"}'
```

## 3. Invitations

### Create Invitation

```bash
curl -X POST "/api/invitations" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"email": "invite@example.com", "role_name": "data_analyst"}'
```

### Accept Invitation

```bash
curl -X POST "/api/invitations/accept" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "inv_token_abc123",
    "email": "invite@example.com",
    "full_name": "Invited User",
    "password": "Pass123!"
  }'
```

## 4. Datasets

### Upload Dataset

```bash
curl -X POST "/api/datasets" \
  -H "Authorization: Bearer eyJ..." \
  -F "file=@data.csv"
```

## 5. Analytics

### List Dashboards

```bash
curl -X GET "/api/dashboards" \
  -H "Authorization: Bearer eyJ..."
```

## 6. Audit Logs

### List Audit Logs

```bash
curl -X GET "/api/audit/logs?page=1&page_size=50" \
  -H "Authorization: Bearer eyJ..."
```

## 7. Error Responses

### 403 Forbidden
```json
{ "success": false, "message": "Insufficient permissions", "data": null }
```

### 404 Not Found
```json
{ "success": false, "message": "Resource not found", "data": null }
```

### 422 Validation Error
```json
{
  "success": false,
  "message": "Validation error",
  "data": { "email": ["Field required"] }
}
```

## Related Documents

- [authentication.md](authentication.md) — API authentication
- [openapi.md](openapi.md) — OpenAPI spec
- [../backend/endpoints.md](../backend/endpoints.md) — Endpoint catalog
