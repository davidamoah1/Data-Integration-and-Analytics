# ADR-0008: Permission Middleware

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0005, ADR-0006 |

---

## Context

A multi-tenant SaaS platform must enforce authorization on the backend. Frontend-only permission checks are insufficient because:
- API endpoints can be called directly, bypassing the frontend
- Frontend code can be modified by users (browser dev tools)
- Security through obscurity is not security
- Compliance requirements (SOC 2, ISO 27001) mandate server-side access control

The platform needs:
- Backend enforcement of all permissions and org access
- Frontend permission checks for UX (show/hide UI elements)
- Defense-in-depth with multiple layers of authorization

## Decision

We enforce authorization **on the backend** using FastAPI dependencies, with frontend checks as a UX enhancement only.

### Backend Enforcement Layers

1. **Authentication** (`shared/dependencies.py:get_current_user`): Verifies JWT, loads user, checks `is_active`
2. **Permission check** (`shared/dependencies.py:require_permissions()`): Checks user has required permission(s); super_admin bypasses
3. **Role check** (`shared/dependencies.py:require_any_role()`): Checks user has required role(s)
4. **Organization access** (`shared/tenant.py:require_organization_access()`): Ensures user belongs to the target organization
5. **Tenant isolation middleware** (`saas/tenant_middleware.py:TenantIsolationMiddleware`): Logs cross-tenant 403 responses

### Frontend Enforcement (UX Only)

1. **RouteGuard** (`frontend/components/auth/RouteGuard.tsx`): Redirects to `/forbidden` if permission/role check fails
2. **Can component** (`frontend/components/auth/Can.tsx`): Conditionally renders UI based on permissions
3. **Sidebar** (`frontend/components/layout/Sidebar.tsx`): Hides nav items based on `hasPermission()` and `hasRole()`
4. **Settings tabs** (`frontend/app/(app)/settings/page.tsx`): Filters tabs based on permissions

### Authorization Flow

```
HTTP Request
    ↓
HTTPBearer → Extract JWT
    ↓
decode_token → Verify signature + expiry
    ↓
get_current_user → Load user from DB
    ↓                 → Check is_active
    ↓                 → Load roles from DB
    ↓                 → Load permissions from DB
    ↓
require_permissions("users.read")
    ↓
    → Super admin? → Bypass
    → Has permission? → Continue
    → Missing? → 403 Forbidden
    ↓
require_organization_access(org_id)
    ↓
    → Super admin? → Allow any org
    → Own org? → Allow
    → Different org? → 403 Forbidden
    ↓
Route handler → Execute business logic
    ↓
TenantIsolationMiddleware → Log 403s as cross-tenant attempts
```

### Key Code Paths

- `shared/dependencies.py:require_permissions()`: FastAPI dependency factory
- `shared/dependencies.py:get_current_user()`: JWT verification and user loading
- `shared/tenant.py:require_organization_access()`: Org access enforcement
- `shared/tenant.py:get_current_organization_id()`: Extracts user's org_id
- `saas/tenant_middleware.py:TenantIsolationMiddleware`: ASGI middleware for logging

## Alternatives Considered

1. **Frontend-only checks**: Rejected — insecure, API endpoints exposed without authorization.
2. **API gateway authorization**: Centralized auth at gateway level. Considered for future but doesn't handle org-scoped access.
3. **Decorator-based auth**: Python decorators on service methods. Rejected — FastAPI dependencies are more idiomatic and testable.
4. **Middleware-only**: All auth in ASGI middleware. Rejected — too coarse-grained, can't check specific permissions per route.

## Consequences

### Positive
- All authorization enforced server-side — secure by default
- Frontend checks improve UX (hide inaccessible features)
- Defense-in-depth: JWT → permission → org access → middleware logging
- Super admin bypass is explicit and documented
- New routes must declare required permissions via `Depends()`

### Negative
- Every API call hits the database to load roles and permissions
- Permission strings must be kept in sync between frontend and backend
- `require_permissions()` uses OR logic (any one permission suffices)

### Mitigations
- JWT includes roles and permissions claims (reduces some DB queries)
- Permission constants are defined in `frontend/lib/permissions.ts` and `authentication/services.py`
- Future: Add Redis caching for role/permission lookups
- Future: Add AND logic option for sensitive operations

## Implementation Notes

- `require_permissions()` is a dependency factory: `Depends(require_permissions("users.read"))`
- Super admin bypass is checked first: `if "super_admin" in current_user["roles"]: return current_user`
- `require_organization_access()` raises `AuthorizationError` (not `HTTPException`) for non-super-admin cross-org access
- `TenantIsolationMiddleware` skips public paths and exempt prefixes
- User's roles and permissions are loaded fresh from DB on each request (no caching yet)

## Future Considerations

- Add Redis-based permission caching
- Implement AND logic for `require_permissions()` (require ALL listed permissions)
- Add rate limiting per permission level
- Add API key authentication with scoped permissions
- Add policy-based access control (OPA integration)
- Add automated authorization testing (verify every endpoint has correct auth)

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0005: Role-Based Access Control
- ADR-0006: Platform Owner vs Organization Administrator
