# Performance Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Planned  
> **Owner**: QA Lead

---

## Purpose

Performance testing approach and targets.

## Scope

API response times, load testing, and bottleneck identification.

## Audience

QA engineers and DevOps engineers.

---

> **⚠️ Planned**: Performance tests are not yet implemented.

## 1. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API p50 response time | < 100ms | Per endpoint |
| API p95 response time | < 200ms | Per endpoint |
| API p99 response time | < 500ms | Per endpoint |
| Dashboard load time | < 2s | Full page load |
| Dataset upload (10MB) | < 5s | Upload + parse |
| Report generation | < 10s | Generate + store |
| Concurrent users | 500 | No errors |
| Database query time | < 50ms | Average query |

## 2. Planned Tools

| Tool | Purpose |
|------|---------|
| locust | Python load testing |
| k6 | JavaScript load testing |
| Artillery | API load testing |
| Lighthouse | Frontend performance |

## 3. Test Scenarios

| Scenario | Load | Duration | Success Criteria |
|----------|------|----------|-----------------|
| Login | 100 RPS | 5 min | < 200ms p95 |
| List users | 50 RPS | 5 min | < 200ms p95 |
| Upload dataset | 10 RPS | 5 min | < 5s p95 |
| Dashboard view | 100 RPS | 5 min | < 2s p95 |
| Mixed workload | 200 RPS | 10 min | < 500ms p95 |

## Related Documents

- [strategy.md](strategy.md) — Testing strategy
- [../architecture/scalability.md](../architecture/scalability.md) — Scalability
- [../database/optimization.md](../database/optimization.md) — DB optimization
