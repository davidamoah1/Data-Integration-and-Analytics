# Deployment Monitoring

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Document monitoring setup for deployed applications.

## Scope

Health checks, alerting, and observability.

## Audience

DevOps engineers and operations team.

---

## 1. Health Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | Public | Basic health check |
| `/api/ready` | GET | Public | Readiness check (DB connectivity) |

### Health Response

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-07-30T12:00:00Z"
}
```

## 2. Monitoring Strategy

### Current

- Vercel built-in monitoring (response time, error rate)
- Application logs via `RequestLoggingMiddleware`
- Error logging via global exception handler

### Planned

> **⚠️ Planned**: The following are not yet implemented.

- Uptime monitoring (external service)
- Alerting on error rate spike
- Database connection pool monitoring
- API response time percentiles
- Frontend Core Web Vitals tracking

## 3. Log Aggregation

### Current

- Vercel function logs (available in Vercel dashboard)
- `RequestLoggingMiddleware` logs all requests
- `logger` instance for application events

### Planned

- Centralized log aggregation (Datadog, CloudWatch, or ELK)
- Structured JSON logging
- Log-based alerting

## Related Documents

- [../operations/monitoring.md](../operations/monitoring.md) — Operations monitoring
- [../backend/logging.md](../backend/logging.md) — Application logging
- [production.md](production.md) — Production deployment
