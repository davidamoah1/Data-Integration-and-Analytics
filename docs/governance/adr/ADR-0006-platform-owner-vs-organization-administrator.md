# ADR-0006: Platform Owner vs Organization Administrator

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0005, ADR-0008 |

---

## Context

A multi-tenant SaaS platform requires a clear separation between platform-level administration and organization-level administration. Without this separation:
- Organization admins could access other organizations' data (cross-tenant breach)
- Platform owners could be confused with org admins (privilege ambiguity)
- Security boundaries become unclear

The platform needs two distinct administrative tiers:
1. **Platform Owner** — manages the entire platform, all organizations, and system settings
2. **Organization Administrator** — manages only their own organization, its users, and its data

## Decision

We separated platform and organization administration into distinct roles with different permission scopes and access boundaries.

### Role Definitions

| Role | System Name | Scope | Key Permissions |
|------|-------------|-------|----------------|
| Platform Owner | `super_admin` | All organizations | `*` (all permissions), `settings.manage` |
| Organization Owner | `org_owner` | Single organization | All except `settings.manage` |
| Organization Administrator | `org_admin` | Single organization | Users, data, analytics, ML — no `settings.manage`, no `roles.manage` |

### Separation Principles

1. **`super_admin` bypasses all org checks**: Can access any organization's data
2. **`org_admin` is org-scoped**: Can only access data within `organization_id`
3. **`settings.manage` is platform-only**: Only `super_admin` has this permission
4. **Platform-level roles cannot be invited**: `super_admin` and `org_owner` are not assignable via invitation
5. **Role assignment restriction**: Non-super-admins cannot assign `super_admin` or `org_owner` roles
6. **Admin Portal is super_admin-only**: The `/admin-portal` route requires `super_admin` role

### Implementation

- `shared/tenant.py:is_super_admin()`: Checks for `super_admin` in user roles
- `shared/dependencies.py:require_permissions()`: Super admin bypasses all permission checks
- `shared/tenant.py:require_organization_access()`: Super admin can access any org; others restricted to own
- `authentication/routes.py:list_users()`: Super admin sees all users; others see only own org
- `organizations/services.py:list_organizations()`: Super admin sees all orgs; others see only own
- `frontend/components/layout/Sidebar.tsx`: Admin Portal visible only to `super_admin` role

### Key Code Paths

```python
# Super admin bypass in require_permissions
if "super_admin" in current_user["roles"]:
    return current_user  # Bypass all checks

# Org-scoped user listing
if is_super_admin(current_user):
    result = service.list_users(page, page_size)
else:
    org_id = get_current_organization_id(current_user, db)
    result = service.list_users_by_org(org_id, page, page_size)

# Org access enforcement
require_organization_access(current_user, org_id, db)  # 403 if cross-org
```

## Alternatives Considered

1. **Single admin role**: One `admin` role for both platform and org. Rejected — no way to distinguish scope, security risk.
2. **Scope-based permissions**: Permissions include scope (e.g., `users.read.platform`, `users.read.org`). Rejected — too complex for current scale.
3. **Role inheritance**: `org_admin` inherits from `super_admin` with restrictions. Rejected — inheritance is top-down, not restrictive.

## Consequences

### Positive
- Clear security boundary between platform and org administration
- Org admins cannot access other orgs' data
- Platform owner has full access for support and management
- `settings.manage` is exclusively platform-level
- Admin Portal is hidden from org admins

### Negative
- Platform owner must be careful not to accidentally modify org data
- No intermediate role between platform and org (e.g., "support engineer" with limited platform access)
- Super admin bypass means all permission checks are skipped — high trust requirement

### Mitigations
- All super admin actions are audit-logged
- `TenantIsolationMiddleware` logs cross-tenant access attempts
- Admin Portal shows tenant list with explicit suspend/activate actions (no silent data modification)
- Future: Add "Support Engineer" role with limited platform access

## Implementation Notes

- `super_admin` is seeded during database initialization in `seed_default_data()`
- The first super admin user is created with a configurable email from environment variables
- `org_owner` is a system role but not auto-assigned — it's available for manual assignment
- The `require_super_admin()` helper in `shared/tenant.py` provides explicit super admin checks

## Future Considerations

- Add "Platform Administrator" role (level 90) with limited platform access (no settings.manage)
- Add "Support Engineer" role with read-only access to all orgs for support purposes
- Implement scoped tokens (platform-level vs org-level API keys)
- Add MFA requirement for super_admin role (ADR-0012)
- Add break-glass procedure for emergency super admin access

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0005: Role-Based Access Control
- ADR-0008: Permission Middleware
