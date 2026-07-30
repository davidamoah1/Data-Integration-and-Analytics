# ADR-0001: Enterprise Multi-Tenant Architecture

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0005, ADR-0006, ADR-0008, ADR-0009 |

---

## Context

DataFlow is a SaaS platform serving multiple organizations that need strict data isolation. Each organization's data — datasets, dashboards, reports, users, audit logs — must be completely inaccessible to other organizations. The platform also needs a platform-level administrator (super admin) who can access all organizations.

The architecture must support:
- Complete data isolation between organizations
- A platform owner who can manage all organizations
- Organization administrators who can only manage their own organization
- Future expansion to support SSO, SCIM, and white-label deployments

## Decision

We adopted a **shared-database, tenant-scoped** multi-tenant architecture using `organization_id` as the tenant discriminator on all data tables.

### Implementation

1. **TenantContext** (`platform_features/tenant.py`): Carries `organization_id`, `user_id`, `roles`, and `is_super_admin` for the current request.
2. **TenantFilter** (`platform_features/tenant.py`): Static methods to apply `organization_id` filters to SQLAlchemy queries. Super admins bypass filtering.
3. **TenantIsolationMiddleware** (`saas/tenant_middleware.py`): Defense-in-depth layer that logs cross-tenant access attempts (403 responses).
4. **require_organization_access** (`shared/tenant.py`): FastAPI dependency that enforces org-scoped access on route handlers.
5. **Organization model** (`organizations/models.py`): Each organization has a unique `slug`, `name`, and `is_active` flag.

### Data Scoping

- All data tables include an `organization_id` column (nullable for personal workspaces).
- Non-super-admin queries are automatically filtered by `organization_id`.
- Super admins bypass org filtering to access all tenants.

## Alternatives Considered

1. **Database-per-tenant**: Each organization gets its own database. Rejected due to operational complexity, connection pool limits, and migration overhead at scale.
2. **Schema-per-tenant**: Each organization gets its own PostgreSQL schema. Rejected due to migration complexity and connection pool constraints.
3. **Row-level security (RLS)**: PostgreSQL RLS policies. Considered as future enhancement but rejected for initial implementation due to complexity of debugging and testing.

## Consequences

### Positive
- Simple to implement and maintain
- Single database connection pool
- Easy to query across tenants for platform analytics
- Migrations apply to all tenants simultaneously

### Negative
- Risk of cross-tenant data leakage if org filter is forgotten on new queries
- Need for disciplined application of `require_organization_access` on every route
- No physical isolation between tenants

### Mitigations
- `TenantIsolationMiddleware` logs cross-tenant access attempts
- `require_organization_access` is enforced on all org-scoped routes
- Code review checklist requires org filter verification on new queries

## Implementation Notes

- `TenantContext` is constructed from JWT claims on each request
- `TenantFilter.apply_org_filter()` must be called on all org-scoped queries
- Super admin bypass is intentional and documented in `require_permissions()`
- The `apply_organization_filter()` helper in `shared/tenant.py` provides a convenience wrapper

## Future Considerations

- Add PostgreSQL Row-Level Security (RLS) as a defense-in-depth layer
- Implement workspace-level scoping within organizations
- Consider tenant-specific encryption keys for sensitive data
- Add automated tests that verify org isolation on every API endpoint

## Related ADRs

- ADR-0005: Role-Based Access Control
- ADR-0006: Platform Owner vs Organization Administrator
- ADR-0008: Permission Middleware
- ADR-0009: Workspace Model
