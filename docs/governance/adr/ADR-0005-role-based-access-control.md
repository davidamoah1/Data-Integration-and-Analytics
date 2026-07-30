# ADR-0005: Role-Based Access Control

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0006, ADR-0008 |

---

## Context

The platform needs a permission system that:
- Controls access to modules and actions at a granular level
- Supports multiple roles per user
- Is centralized and consistent between frontend and backend
- Supports both system (immutable) and custom (user-created) roles
- Scales to new modules and permissions without redesign

## Decision

We implemented **Role-Based Access Control (RBAC)** with a centralized permission model.

### Model

```
User → UserRole → Role → RolePermission → Permission
```

- **Users** have one or more **Roles** (many-to-many via `user_roles` table)
- **Roles** have one or more **Permissions** (many-to-many via `role_permissions` table)
- **Permissions** are defined as `module.action` strings (e.g., `datasets.upload`)

### Implementation

1. **Database models** (`authentication/models.py`): `Role`, `Permission`, `RolePermission`, `UserRole`
2. **Repositories** (`authentication/repositories.py`): `RoleRepository`, `PermissionRepository`, `RolePermissionRepository`, `UserRoleRepository`
3. **RBAC utilities** (`platform_features/rbac.py`): `RoleHierarchy`, `PermissionMatrix`, `ROLE_HIERARCHY`, `PERMISSION_MATRIX`
4. **Backend enforcement** (`shared/dependencies.py`): `require_permissions()`, `require_any_role()` FastAPI dependencies
5. **Frontend enforcement** (`frontend/lib/permissions.ts`): `PERMISSIONS`, `ROLES` constants; `hasPermission()`, `hasRole()` in auth store
6. **Role hierarchy** (`platform_features/rbac.py:RoleHierarchy`): Numeric levels (20-100) for role comparison and management

### System Roles

13 system roles are seeded during database initialization (`seed_default_data()`):
- `super_admin` (level 100) — all permissions via `*` wildcard
- `org_owner` (level 100) — all except `settings.manage`
- `org_admin` (level 80) — users, data, analytics, ML
- `dept_manager` (level 60) — department operations
- `data_engineer` (level 40) — ETL pipelines
- `data_analyst` (level 40) — analysis and reports
- `business_analyst` (level 40) — dashboards and reports
- `executive` (level 60) — high-level analytics
- `dept_officer` (level 20) — read-only department
- `auditor` (level 40) — audit logs
- `viewer` (level 20) — dashboards only
- `researcher` (level 40) — research datasets
- `data_entry_officer` (level 20) — Smart Data Capture

### Permission Checking

```python
# Backend: require_permissions dependency
@router.get("/users", dependencies=[Depends(require_permissions("users.read"))])

# Backend: super_admin bypass
if "super_admin" in current_user["roles"]:
    return current_user  # Bypass all permission checks

# Frontend: hasPermission / hasRole
{hasPermission("datasets.view") && <DatasetLink />}
{hasRole("super_admin") && <AdminPortalLink />}
```

## Alternatives Considered

1. **Attribute-Based Access Control (ABAC)**: More flexible but significantly more complex. Deferred to future — current RBAC model has extension points for ABAC.
2. **Access Control Lists (ACLs)**: Per-resource permissions. Rejected — too granular and hard to manage at scale.
3. **Flat role model**: No hierarchy. Rejected — hierarchy enables `can_manage()` checks for privilege escalation prevention.

## Consequences

### Positive
- Centralized, consistent permission model
- Frontend and backend use same permission strings
- System roles are immutable (cannot be deleted)
- Custom roles can be created with any permission subset
- Role hierarchy prevents privilege escalation
- Super admin bypass simplifies platform-wide access
- Easy to add new permissions (just add to `permissions_def`)

### Negative
- Permission changes require database update (seed or migration)
- No per-resource permissions (e.g., "user A can edit dataset X but not dataset Y")
- `users.manage` is a superset but not automatically expanded in `require_permissions()`

### Mitigations
- `RoleHierarchy.can_manage()` prevents lower roles from managing higher roles
- Platform-level roles (`super_admin`, `org_owner`) cannot be assigned via invitation
- `assign_roles` route blocks platform-level roles for non-super-admins
- Permission matrix is documented in `permission-matrix.md` and `permission-matrix.json`

## Implementation Notes

- Permissions are seeded in `authentication/services.py:seed_default_data()`
- `RolePermissionRepository.get_permissions_for_role()` returns permission names for a role
- `UserRoleRepository.get_all_permissions_for_user()` returns all permissions across all roles
- JWT tokens include `roles` and `permissions` claims for frontend use
- `require_permissions()` uses OR logic (user needs at least ONE of the required permissions)

## Future Considerations

- Add AND logic option to `require_permissions()` for sensitive operations
- Implement ABAC for per-resource permissions (e.g., dataset-level sharing)
- Add permission caching to reduce database queries
- Support role inheritance (custom roles extending system roles)
- Add permission audit report (who has access to what)

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0006: Platform Owner vs Organization Administrator
- ADR-0008: Permission Middleware
