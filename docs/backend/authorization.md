# Authorization

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

RBAC enforcement on the backend.

## Scope

Permission checking, org access, and super admin bypass.

## Audience

Backend developers and security architects.

---

## 1. Enforcement Mechanism

### require_permissions()

FastAPI dependency factory that checks if the current user has any of the required permissions:

```python
from shared.dependencies import require_permissions

@router.get("/users", dependencies=[Depends(require_permissions("users.read"))])
```

- Uses OR logic: user needs at least ONE of the listed permissions
- Super admin bypasses all checks
- Returns 403 Forbidden if permission missing

### require_any_role()

Checks if user has any of the specified roles:

```python
@router.get("/admin-portal", dependencies=[Depends(require_any_role("super_admin"))])
```

### require_organization_access()

Enforces that the user belongs to the target organization:

```python
from shared.tenant import require_organization_access

require_organization_access(current_user, org_id, db)
```

- Super admin can access any org
- Non-super-admin: 403 if `user.organization_id != org_id`

## 2. Super Admin Bypass

```python
# In require_permissions()
if "super_admin" in current_user["roles"]:
    return current_user  # Bypass all permission checks
```

This is intentional and audit-logged. Super admin has the `*` wildcard permission.

## 3. Key Files

| File | Purpose |
|------|---------|
| `shared/dependencies.py` | `require_permissions()`, `require_any_role()`, `get_current_user()` |
| `shared/tenant.py` | `require_organization_access()`, `is_super_admin()`, `get_current_organization_id()` |
| `platform_features/tenant.py` | `TenantContext`, `TenantFilter` |
| `platform_features/rbac.py` | `RoleHierarchy`, `PermissionMatrix` |

## Related Documents

- [authentication.md](authentication.md) — Authentication
- [../governance/authorization.md](../governance/authorization.md) — Authorization model
- [../governance/permission-matrix.md](../governance/permission-matrix.md) — Permission matrix
- [../governance/api-authorization-matrix.md](../governance/api-authorization-matrix.md) — API auth matrix
