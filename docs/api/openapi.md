# OpenAPI Specification

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Overview of the OpenAPI specification and how to access it.

## Scope

API documentation via FastAPI auto-generated OpenAPI.

## Audience

API consumers and developers.

---

## 1. Accessing API Documentation

FastAPI auto-generates interactive API documentation:

| URL | Interface | Description |
|-----|-----------|-------------|
| `/docs` | Swagger UI | Interactive API testing |
| `/redoc` | ReDoc | Clean API documentation |
| `/openapi.json` | JSON | Raw OpenAPI specification |

> **⚠️ Note**: These are available in development mode. In production, consider disabling or protecting these endpoints.

## 2. API Metadata

```python
app = FastAPI(
    title="DataFlow — Enterprise Data Intelligence API",
    description="Enterprise REST API for ETL, analytics, IAM, and pipeline management.",
    version="1.0.0",
)
```

## 3. Endpoint Documentation

Each endpoint is documented with:
- HTTP method and path
- Required permissions
- Request body schema (Pydantic)
- Response schema
- Query parameters
- Error responses

## 4. Authentication in Swagger

1. Use the `/api/auth/login` endpoint to get tokens
2. Click "Authorize" button in Swagger UI
3. Enter the access token
4. All subsequent requests include the Bearer token

## Related Documents

- [authentication.md](authentication.md) — API authentication
- [examples.md](examples.md) — API examples
- [../backend/api-overview.md](../backend/api-overview.md) — API overview
- [../backend/endpoints.md](../backend/endpoints.md) — Endpoint catalog
