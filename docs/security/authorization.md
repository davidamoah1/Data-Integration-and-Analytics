# Authorization Security

> **Version**: 1.0.0  
> **Last Updated**: 2026-08-01  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Document the authorization model, RBAC enforcement, and tenant isolation mechanisms.

## Scope

Role hierarchy, permission model, enforcement layers, organization scoping, and tenant isolation.

## Audience

Security architects, backend developers, and auditors.

---

## 1. RBAC Model

### Role Hierarchy

| Role | Level | Scope | Description |
|------|-------|-------|-------------|
| super_admin | 0 | Platform | Full platform access, bypasses all checks |
| platform_owner | 1 | Platform | Platform management, org oversight |
| org_admin | 2 | Organization | Full org management |
| department_manager | 3 | Department | Department-level management |
| analyst | 4 | Organization | Data analysis, dashboard creation |
| researcher | 5 | Organization | Research workflows, statistical analysis |
| data_entry_officer | 6 | Organization | Data entry, document capture |
| viewer | 7 | Organization | Read-only access to shared resources |
| personal_workspace | 8 | Personal | Personal workspace only |

### Permission Model

Permissions are granular actions (30+) grouped by resource:

| Resource | Permissions |
|----------|------------|
| users | `users:read`, `users:write`, `users:delete`, `users:invite` |
| organizations | `orgs:read`, `orgs:write`, `orgs:delete` |
| datasets | `datasets:read`, `datasets:write`, `datasets:delete` |
| dashboards | `dashboards:read`, `dashboards:write`, `dashboards:delete` |
| reports | `reports:read`, `reports:write`, `reports:delete` |
| pipelines | `pipelines:read`, `pipelines:write`, `pipelines:delete`, `pipelines:execute` |
| ai | `ai:read`, `ai:write` |
| capture | `capture:read`, `capture:write` |
| audit | `audit:read` |
| system | `system:admin`, `system:config` |

### Role-Permission Mapping

Roles are assigned permissions through the `role_permissions` join table. The complete mapping is defined at seed time in `authentication/services.py` and can be modified by super_admin users.

## 2. Enforcement Layers

### Layer 1: Route-Level Permission Check

Every API route specifies required permissions via `require_permissions()`:

```python
@router.post("/datasets")
@require_permissions("datasets:write")
async def create_dataset(...):
    ...
```

### Layer 2: Organization Access Check

Organization-specific routes verify the user belongs to the organization:

```python
@router.get("/organizations/{org_id}/users")
@require_permissions("users:read")
@require_organization_access()
async def list_org_users(org_id: int, ...):
    ...
```

### Layer 3: Query-Level Tenant Filter

All database queries are automatically scoped by `organization_id`:

```python
# TenantFilter applies org_id filter automatically
query = session.query(Dataset).filter(Dataset.organization_id == current_org_id)
```

### Layer 4: Super Admin Bypass

Super admin bypasses all checks but every action is audit-logged:

```python
if user.is_super_admin:
    log_audit(action="super_admin_bypass", resource=resource, user_id=user.id)
```

## 3. Tenant Isolation

### Data Isolation

| Mechanism | Implementation |
|-----------|---------------|
| Org-scoped queries | `organization_id` filter on all tenant tables |
| User listing | Non-super-admin users only see their org's users |
| Cross-tenant logging | All cross-tenant access attempts logged to `security_logs` |
| API route scoping | `require_organization_access()` on org-specific endpoints |

### Tenant Filter

The `TenantFilter` utility automatically applies organization scoping to SQLAlchemy queries. It is applied in the service layer before any query is executed.

### Cross-Tenant Access Attempts

When a user attempts to access another organization's resources:
1. The request is denied with a 403 Forbidden
2. The attempt is logged to `security_logs` with severity `warning`
3. Repeated attempts may trigger account review

## 4. Permission Middleware

The `require_permissions()` decorator:

1. Extracts the JWT from the Authorization header
2. Loads the user and their roles
3. Collects all permissions from the user's roles
4. Checks if the required permission is in the set
5. If not: returns 403 Forbidden with audit log entry

## 5. Platform Role Protection

Platform-level roles (`super_admin`, `platform_owner`) cannot be:
- Assigned by organization administrators
- Requested during invitation
- Self-assigned through any API endpoint

Only existing super_admin users can assign platform roles.

## 6. Audit Logging

All authorization decisions are logged:

| Event | Log Table | Details |
|-------|-----------|---------|
| Permission granted | `audit_logs` | User, permission, resource |
| Permission denied | `security_logs` | User, attempted permission, resource |
| Super admin bypass | `audit_logs` | User, bypassed check, resource |
| Cross-tenant attempt | `security_logs` | User, target org, severity |

## Related Documents

- [overview.md](overview.md) — Security architecture overview
- [authentication.md](authentication.md) — Authentication details
- [../governance/authorization.md](../governance/authorization.md) — Authorization enforcement
- [../governance/permission-matrix.md](../governance/permission-matrix.md) — Complete permission matrix
- [../governance/roles.md](../governance/roles.md) — Role definitions
