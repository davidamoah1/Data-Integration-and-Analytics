# ADR-0018: Production Monitoring Architecture

> **Date**: 2026-08-01  
> **Status**: Accepted  
> **Deciders**: DevOps, Engineering  
> **Supersedes**: None  
> **Superseded by**: None

---

## Context

Phase 17 established comprehensive documentation, but the platform lacked production-grade observability. The existing monitoring consisted of:

- Basic `/health` and `/ready` endpoints
- Simple `RequestLoggingMiddleware` (text logs only)
- Basic `/metrics` endpoint returning raw table counts
- No error tracking (errors logged but not aggregated)
- No distributed tracing
- No performance metrics (durations, percentiles)
- No structured logging for log aggregation
- No alerting or dashboards

For production deployment, we need:
- Real-time error tracking with stack traces and breadcrumbs
- Distributed tracing for request flows across services
- Prometheus-compatible metrics for scraping
- Structured JSON logging for centralized log aggregation
- Grafana dashboards for visualization
- Kubernetes-compatible health probes (liveness vs readiness)

## Decision

Adopt a layered monitoring architecture with three independent, opt-in integrations plus always-on built-in metrics:

### 1. Sentry for Error Tracking (opt-in via `SENTRY_DSN`)

- **SDK**: `sentry-sdk[fastapi]` with auto-instrumentation for FastAPI, SQLAlchemy, Redis, Logging, and Threading
- **Data scrubbing**: `before_send` filter removes `Authorization`, `Cookie`, `X-API-Key` headers and sensitive request body fields
- **Sampling**: Configurable trace and profile sample rates (default 10%)
- **Release tracking**: Version tagged via `SENTRY_RELEASE`
- **No PII sent**: `send_default_pii=False`

### 2. OpenTelemetry for Tracing and Metrics (opt-in via `OTEL_EXPORTER_OTLP_ENDPOINT`)

- **SDK**: `opentelemetry-distro` with auto-instrumentation for FastAPI, SQLAlchemy, Redis, Logging
- **Export**: OTLP/HTTP protocol to a collector endpoint
- **Custom metrics**: 7 application-specific metrics (HTTP requests, DB queries, pipeline runs, errors, sessions)
- **Resource attributes**: Service name, version, deployment environment
- **No-op when unconfigured**: Zero overhead when `OTEL_EXPORTER_OTLP_ENDPOINT` is not set

### 3. Prometheus Metrics (always-on, built-in)

- **No external dependency**: Custom `MetricsRegistry` implementation in `monitoring/prometheus.py` — no `prometheus_client` library required
- **Endpoint**: `GET /metrics` returns Prometheus text exposition format
- **Metrics**: 12 metrics (4 counters, 2 histograms, 6 gauges) covering HTTP, DB, pipeline, errors, sessions, uptime
- **Path normalisation**: Reduces cardinality by replacing IDs with `:id` and long segments with `:param`
- **Thread-safe**: Lock-protected registry

### 4. Structured JSON Logging (opt-in via `LOG_FORMAT=json`)

- **Already existed**: `JSONFormatter` in `etl/logging_config.py` with `request_id` and `correlation_id`
- **Correlation IDs**: `X-Request-ID` (generated) and `X-Correlation-ID` (upstream or generated)
- **Rotating file handler**: 5MB rotation, 5 backups when `LOG_PATH` is set

### 5. Unified MonitoringMiddleware

Replaced `RequestContextMiddleware` + `RequestLoggingMiddleware` with a single `MonitoringMiddleware` that:
- Sets request/correlation IDs
- Records Prometheus metrics (request count, duration)
- Records OpenTelemetry spans
- Captures unhandled exceptions in Sentry
- Adds Sentry breadcrumbs for non-trivial requests
- Sets response headers (`X-Request-ID`, `X-Correlation-ID`)

### 6. Enhanced Health Checks

| Endpoint | Purpose |
|----------|---------|
| `/monitoring/health/live` | Liveness (process alive, no dependency checks) |
| `/monitoring/health/ready` | Readiness (DB + Redis + integration status) |
| `/monitoring/health/detailed` | Full subsystem health with monitoring status |
| `/monitoring/status` | Sentry/OTel/Prometheus enablement status |

### 7. Grafana Dashboard

- Pre-built dashboard JSON in `monitoring/dashboards/grafana-application.json`
- 10 panels: request rate, duration percentiles, error rate, DB queries, sessions, uptime, pipeline runs, pool stats
- Auto-provisioned via Grafana provisioning config

### 8. Docker Compose Monitoring Stack

- `monitoring/docker-compose.monitoring.yml`: Prometheus + Grafana + Node Exporter
- `monitoring/prometheus.yml`: Scrape configuration for API, frontend, and self-monitoring

## Consequences

### Positive

- **Zero-overhead when disabled**: Sentry and OTel are no-ops when DSN/endpoint not set
- **No external dependency for metrics**: Custom Prometheus implementation — no `prometheus_client` needed
- **Unified middleware**: Single middleware replaces two, reducing complexity
- **Kubernetes-ready**: Separate liveness and readiness probes
- **Security-conscious**: Data scrubbing in Sentry, no PII sent, no auth on metrics endpoint

### Negative

- **Additional dependencies**: 8 new packages in requirements.txt (sentry-sdk, opentelemetry-*)
- **Memory overhead**: Metrics registry stores counters/histograms in-process
- **No persistent metrics**: Metrics reset on process restart (acceptable for now; Prometheus scrapes and stores externally)

### Risks

- **Metrics cardinality**: Path normalisation mitigates but does not eliminate high-cardinality label explosion
- **Sentry cost**: Sampling rate controls cost; default 10% is conservative
- **OTel complexity**: Auto-instrumentation may add overhead; can be disabled per integration

## Implementation

### Files Created

| File | Purpose |
|------|---------|
| `monitoring/sentry_integration.py` | Sentry SDK init, capture, context, breadcrumbs |
| `monitoring/otel.py` | OpenTelemetry init, instrumentation, custom metrics |
| `monitoring/prometheus.py` | Prometheus metrics registry (counters, histograms, gauges) |
| `monitoring/middleware.py` | Unified MonitoringMiddleware |
| `monitoring/routes.py` | Monitoring API routes (metrics, health, status) |
| `monitoring/prometheus.yml` | Prometheus scrape configuration |
| `monitoring/docker-compose.monitoring.yml` | Monitoring stack (Prometheus + Grafana) |
| `monitoring/dashboards/grafana-application.json` | Grafana dashboard (10 panels) |
| `monitoring/dashboards/dashboards.yml` | Grafana provisioning config |

### Files Modified

| File | Changes |
|------|---------|
| `api/main.py` | Init Sentry/OTel in lifespan, replace middleware, update /metrics, add monitoring routes, wire pipeline metrics |
| `config.py` | Add monitoring env vars (Sentry, OTel, Prometheus) |
| `requirements.txt` | Add sentry-sdk, opentelemetry-*, redis |
| `docs/deployment/monitoring.md` | Complete rewrite for Phase 18 |

### Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `SENTRY_DSN` | (empty) | No |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | No |
| `SENTRY_PROFILES_SAMPLE_RATE` | `0.1` | No |
| `SENTRY_RELEASE` | `aedip@1.0.0` | No |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | (empty) | No |
| `OTEL_SERVICE_NAME` | `aedip-api` | No |
| `OTEL_SERVICE_VERSION` | `1.0.0` | No |
| `OTEL_METRIC_EXPORT_INTERVAL` | `60000` | No |
| `PROMETHEUS_ENABLED` | `true` | No |
| `MONITORING_ENABLED` | `true` | No |
