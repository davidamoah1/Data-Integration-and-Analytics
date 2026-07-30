# Scalability

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Document the scalability strategy and known bottlenecks.

## Scope

Current scalability characteristics and planned improvements.

## Audience

Architects, DevOps engineers, and CTO.

---

## 1. Current Scalability

### Backend (FastAPI)

- **Async**: FastAPI supports async request handlers
- **Serverless**: Deployable on Vercel serverless functions
- **Stateless**: No in-memory session state — all state in PostgreSQL
- **Connection Pooling**: SQLAlchemy engine with connection pool

### Frontend (Next.js)

- **SSR/SSG**: Next.js supports server-side rendering and static generation
- **Code Splitting**: Automatic route-level code splitting
- **PWA**: Progressive Web App with offline support via Workbox
- **CDN**: Vercel Edge CDN for static assets

### Database (PostgreSQL)

- **Single Instance**: Currently single PostgreSQL instance
- **Indexing**: Indexes on key columns (see [indexing.md](../database/indexing.md))
- **Soft Deletes**: `is_deleted` flag avoids hard deletes

## 2. Known Bottlenecks

| Bottleneck | Impact | Mitigation |
|-----------|--------|------------|
| Single PostgreSQL instance | All queries hit one DB | Future: Read replicas, connection pooling (PgBouncer) |
| No caching layer | Every request queries DB | Future: Redis for session/permission caching |
| Synchronous audit logging | Audit log writes in request path | Future: Async audit log writer |
| No query result pagination on some endpoints | Large datasets slow response | Add pagination to all list endpoints |
| Role/permission loaded per request | DB query on every request | Future: Cache in Redis or include in JWT |

## 3. Scalability Strategy

### Short-term

1. Add Redis for session and permission caching
2. Implement connection pooling (PgBouncer)
3. Add pagination to all list endpoints
4. Optimize N+1 queries in ORM

### Medium-term

5. Add PostgreSQL read replicas for analytics queries
6. Implement async audit log writer (background task)
7. Add CDN for dataset file storage
8. Implement query result caching for dashboards

### Long-term

9. Database sharding by organization_id
10. Event-driven architecture for audit logging
11. Horizontal scaling with sticky sessions
12. Multi-region deployment

## 4. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API response time (p95) | < 200ms | Not measured |
| Dashboard load time | < 2s | Not measured |
| Dataset upload (10MB) | < 5s | Not measured |
| Report generation | < 10s | Not measured |
| Concurrent users | 500 | Not tested |

## Related Documents

- [deployment-architecture.md](deployment-architecture.md) — Deployment topology
- [../database/optimization.md](../database/optimization.md) — Database optimization
- [../backend/caching.md](../backend/caching.md) — Caching strategy
- [../testing/performance-tests.md](../testing/performance-tests.md) — Performance testing
