# Logging

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Document the logging architecture and log levels.

## Scope

Application logging, request logging, and audit logging.

## Audience

Backend developers and DevOps engineers.

---

## 1. Logging Setup

- **Library**: Python `logging` via `etl/logging_config.py`
- **Logger**: `logger` instance used across the application
- **Format**: Structured log messages with timestamps

## 2. Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed diagnostic info (enabled with `DEBUG=1`) |
| `INFO` | Normal operations (startup, seeding, scheduler) |
| `WARNING` | Unexpected but non-critical issues |
| `ERROR` | Failures (DB errors, seed failures, scheduler errors) |
| `CRITICAL` | System-critical failures |

## 3. Request Logging

`RequestLoggingMiddleware` logs every HTTP request with:
- Method, path, status code
- Response time
- Request ID and correlation ID

## 4. Request Context

`RequestContextMiddleware` attaches:
- `X-Request-ID` header (UUID per request)
- `X-Correlation-ID` header (if provided by client)

## 5. Audit Logging

Separate from application logging — see [../governance/audit-logging.md](../governance/audit-logging.md).

## 6. Key Files

| File | Purpose |
|------|---------|
| `etl/logging_config.py` | Logger configuration |
| `shared/middleware.py` | `RequestLoggingMiddleware` |
| `shared/context.py` | `request_id`, `correlation_id` context vars |

## Related Documents

- [error-handling.md](error-handling.md) — Error handling
- [../governance/audit-logging.md](../governance/audit-logging.md) — Audit logging
- [../operations/monitoring.md](../operations/monitoring.md) — Monitoring
