# Error Handling

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Document error handling patterns and response format.

## Scope

All API error responses and exception handling.

## Audience

Backend developers and API consumers.

---

## 1. Error Response Format

All errors follow the standard JSON envelope:

```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

## 2. HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST (create) |
| 400 | Bad Request | Validation error, invalid input |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Permission denied or org access denied |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Pydantic validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unhandled exception |

## 3. Exception Handlers

### HTTPException Handler

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None},
    )
```

### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    message = "Internal server error"
    if os.getenv("DEBUG", "").lower() in ("1", "true", "yes"):
        message = f"Internal server error: {exc}"
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": message, "data": None},
    )
```

- In debug mode (`DEBUG=1`), the actual exception message is returned
- In production, a generic "Internal server error" is returned

## 4. Domain Exceptions

| Exception | HTTP Code | Description |
|-----------|-----------|-------------|
| `NotFoundError` | 404 | Resource not found |
| `AuthorizationError` | 403 | Permission or org access denied |
| `ValidationError` | 400 | Input validation failed |
| `ConflictError` | 409 | Duplicate resource |

## 5. Pydantic Validation

FastAPI automatically returns 422 for Pydantic validation errors with detailed field-level messages.

## Related Documents

- [api-overview.md](api-overview.md) — API overview
- [logging.md](logging.md) — Logging
- [../architecture/system-design.md](../architecture/system-design.md) — System design
