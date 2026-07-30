# Operations Monitoring

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Monitoring and observability for production operations.

## Scope

Health checks, metrics, alerting, and log monitoring.

## Audience

DevOps engineers and operations team.

---

## 1. Health Checks

| Endpoint | Frequency | Alert If |
|----------|-----------|----------|
| `GET /api/health` | 30s | Non-200 response |
| `GET /api/ready` | 60s | Database disconnected |

## 2. Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API response time (p95) | < 200ms | > 500ms |
| Error rate | < 1% | > 5% |
| Database connection pool | < 80% | > 95% |
| Disk usage | < 80% | > 90% |
| Memory usage | < 80% | > 95% |
| Uptime | > 99.9% | < 99.5% |

## 3. Log Monitoring

### Application Logs

- `RequestLoggingMiddleware` logs all HTTP requests
- Global exception handler logs unhandled exceptions
- `logger` instance for application events

### Audit Logs

- `AuditLog` table records all critical actions
- Queryable via `/api/audit/logs` with `audit.view` permission
- Monitor for unusual patterns (mass deletions, role changes)

### Security Logs

- `SecurityLog` table records security events
- Monitor for: failed logins, access denied, cross-tenant attempts

## 4. Planned Monitoring Stack

> **⚠️ Planned**: The following are not yet implemented.

| Component | Tool | Purpose |
|-----------|------|---------|
| Metrics | Prometheus + Grafana | Time-series metrics |
| Logs | ELK or Datadog | Log aggregation |
| Alerts | PagerDuty or Opsgenie | Alert routing |
| Uptime | UptimeRobot or Pingdom | External uptime |
| APM | New Relic or Datadog | Application performance |
| Error tracking | Sentry | Error monitoring |

## Related Documents

- [../deployment/monitoring.md](../deployment/monitoring.md) — Deployment monitoring
- [../backend/logging.md](../backend/logging.md) — Application logging
- [../governance/audit-logging.md](../governance/audit-logging.md) — Audit logging
- [incident-response.md](incident-response.md) — Incident response
