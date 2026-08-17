# Production Monitoring

**Version:** 1.0.0
**Last Updated:** 2025-01-17

---

## Health Endpoints

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `GET /health` | Basic health + DB connectivity | `{"status": "healthy"}` |
| `GET /ready` | Readiness for traffic | 200 if DB reachable, 503 otherwise |
| `GET /health/detailed` | Full system status | All subsystem statuses |
| `GET /metrics` | Prometheus-compatible metrics | Text format metrics |

## Key Metrics

### Application

| Metric | Alert Threshold | Severity |
|--------|----------------|----------|
| Error rate (5xx) | > 1% of requests | P2 |
| Response time P95 | > 2000ms | P3 |
| Response time P99 | > 5000ms | P2 |
| Request rate drop | > 50% sudden drop | P2 |

### Database

| Metric | Alert Threshold | Severity |
|--------|----------------|----------|
| Connection pool usage | > 80% | P3 |
| Slow queries/min | > 10 | P3 |
| Replication lag | > 5s | P2 |
| Disk usage | > 80% | P2 |
| Disk usage | > 95% | P1 |

### Worker/Queue

| Metric | Alert Threshold | Severity |
|--------|----------------|----------|
| Queue depth | > 100 jobs | P3 |
| Failed jobs/hour | > 5 | P3 |
| Worker offline | Any worker down | P2 |
| Job processing time | > 5 min | P3 |

### Infrastructure

| Metric | Alert Threshold | Severity |
|--------|----------------|----------|
| CPU usage | > 80% sustained | P3 |
| Memory usage | > 85% | P2 |
| Disk I/O wait | > 20% | P3 |
| Network errors | > 0.1% | P3 |

## Built-in Observability

### Structured Logging

```json
{
  "timestamp": "2025-01-17T10:30:00Z",
  "level": "INFO",
  "request_id": "abc123",
  "correlation_id": "def456",
  "method": "POST",
  "path": "/dataset-workflow/run",
  "status": 200,
  "duration_ms": 2500,
  "organization_id": 2
}
```

### Slow Query Logging

Queries exceeding `SLOW_QUERY_THRESHOLD_MS` (default 500ms) are logged at WARNING level.

### Rate Limit Monitoring

Rate limit hits are logged. Monitor for patterns:
- Single IP hitting limits = normal protection
- Many IPs hitting limits = possible DDoS or misconfiguration

### Sentry Integration

Set `SENTRY_DSN` to enable:
- Exception capture (with PII scrubbing)
- Performance tracing
- Release tracking

### OpenTelemetry Integration

Set `OTEL_EXPORTER_OTLP_ENDPOINT` to enable:
- Distributed tracing
- Span metrics
- Service dependency mapping

## Monitoring Stack (Docker)

The `monitoring/docker-compose.monitoring.yml` provides:
- **Prometheus** — metrics collection
- **Grafana** — dashboards and alerting
- **AlertManager** — alert routing

## Recommended Dashboards

### 1. API Overview
- Request rate (by endpoint)
- Error rate (by status code)
- Response time percentiles
- Active connections

### 2. Database Health
- Connection pool utilization
- Query rate
- Slow query count
- Table sizes
- Lock wait time

### 3. Worker Status
- Queue depth
- Job completion rate
- Job failure rate
- Processing time distribution

### 4. Business Metrics
- Active users/day
- Workflows completed/day
- Datasets uploaded/day
- Reports generated/day

## Log Aggregation

Recommended setup:
- Application logs → JSON format → Log aggregator (ELK/Loki)
- Filter by `request_id` for request tracing
- Filter by `organization_id` for tenant debugging
- Alert on ERROR rate spikes

## Backup Monitoring

Verify daily:
- Backup job ran successfully
- Backup file size is reasonable (not 0 bytes)
- Backup storage has space
- Oldest backup is within retention window
