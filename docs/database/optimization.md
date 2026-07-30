# Database Optimization

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Database Architect

---

## Purpose

Document query optimization and performance tuning strategies.

## Scope

Current optimizations and planned improvements.

## Audience

Developers and database administrators.

---

## 1. Current Optimizations

### Connection Pooling

SQLAlchemy engine uses connection pooling by default:
- Pool size managed by SQLAlchemy `create_engine()`
- Connections reused across requests

### Indexing

See [indexing.md](indexing.md) for complete index documentation.

### Soft Deletes

All major tables use `is_deleted` flag instead of hard deletes, preserving referential integrity and enabling recovery.

### Org-Scoped Queries

All data queries are filtered by `organization_id`, limiting result sets to the user's org.

## 2. Query Patterns

### Efficient Patterns (Used)

```python
# Org-scoped query with filter
query = db.query(Dataset).filter(
    Dataset.organization_id == org_id,
    Dataset.is_deleted == 0
)

# Pagination
query = query.offset((page - 1) * page_size).limit(page_size)
```

### Anti-Patterns to Avoid

```python
# ❌ N+1 query — loading roles one by one
for user in users:
    roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()

# ✅ Batch loading
user_ids = [u.id for u in users]
roles = db.query(UserRole).filter(UserRole.user_id.in_(user_ids)).all()
```

## 3. Known Performance Issues

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Role/permission loaded per request | Extra DB query per request | Future: Cache in Redis |
| No query result caching | Dashboards re-query on every load | Future: Cache dashboard results |
| Audit log table grows unbounded | Slower queries over time | Future: Archive old logs |
| No pagination on some endpoints | Large result sets | Add pagination everywhere |

## 4. Optimization Recommendations

### Short-term

1. Add pagination to all list endpoints
2. Use `joinedload()` for common N+1 patterns
3. Add Redis caching for role/permission lookups
4. Add query timeout limits

### Medium-term

5. Implement read replicas for analytics queries
6. Add materialized views for dashboard aggregations
7. Implement audit log archival (move > 1 year old to cold storage)
8. Add connection pooling (PgBouncer)

### Long-term

9. Database sharding by `organization_id`
10. Columnar storage for analytics tables
11. Full-text search index for audit log search

## Related Documents

- [indexing.md](indexing.md) — Index strategy
- [schema.md](schema.md) — Complete schema
- [../architecture/scalability.md](../architecture/scalability.md) — Scalability strategy
- [../backend/caching.md](../backend/caching.md) — Caching strategy
