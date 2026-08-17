# RBAC and Tenant Isolation

This document describes Dataflow's role-based access control (RBAC) model and
multi-tenant (multi-organization) isolation mechanisms, spanning the
`authentication/` backend module, the `shared/` tenant and dependency
helpers, and the `frontend/lib/permissions.ts` / `frontend/lib/navigation.ts`
authorization layer.

## Role Hierarchy

Roles are stored in the `roles` table (`authentication/models.py::Role`) with
a `level` attribute (`platform`, `organization`, `department`, or `personal`)
that indicates the scope at which a role normally applies. Role assignments
live in `user_roles` (`UserRole`), which additionally supports optional
`scope_type`/`scope_id` for scoping a role to a specific organization,
department, or resource — the same role name can be granted narrowly (e.g. a
`dept_manager` scoped to one department) rather than only globally.

The platform ships 13 built-in roles, defined in
`frontend/lib/permissions.ts::ROLES` (mirrored by seeded rows in the `roles`
table):

| Role | Description (`ROLE_DESCRIPTIONS`) |
|---|---|
| `super_admin` | Full system access with all permissions |
| `org_owner` | Owner of an organization with full org access |
| `org_admin` | Manage users and data within organization |
| `dept_manager` | Manage department operations |
| `data_engineer` | Build and run ETL pipelines |
| `data_analyst` | Analyze data and create reports |
| `business_analyst` | View dashboards and reports |
| `executive` | View high-level analytics and reports |
| `researcher` | Upload research datasets and perform statistical analysis |
| `auditor` | View audit logs and security events |
| `dept_officer` | Department-level operations |
| `data_entry_officer` | Upload documents and use Smart Data Capture |
| `viewer` | Read-only access to dashboards |

`super_admin` is a special case: it bypasses all permission and role checks
throughout the backend (`shared/dependencies.py::require_permissions` and
`require_any_role`) and the frontend (`frontend/lib/navigation.ts::hasPermission`).
It is also the only role permitted to act without being bound to an
organization (see **Tenant Isolation** below).

`frontend/lib/navigation.ts::getPrimaryRole(roles)` resolves a user's primary
role from their assigned role list using a fixed priority order (topped by
`super_admin`, then `org_owner`, etc.), which determines which navigation
profile (`getRoleProfile`) and purpose text (`getNavigationPurpose`) is shown.

## Permission Model

Permissions are fine-grained, module-scoped strings stored in the
`permissions` table (`Permission`: `name`, `display_name`, `module`,
`description`) and linked to roles via `role_permissions`
(`RolePermission`). A user's effective permissions are the union of the
permissions of every role assigned to them
(`UserRoleRepository.get_all_permissions_for_user`, a join across
`user_roles` → `role_permissions` → `permissions`).

`frontend/lib/permissions.ts::PERMISSIONS` enumerates the permission
namespace used across the app, grouped by module in `PERMISSION_GROUPS`
(also used to render the role/permission editor UI):

- **Users**: `users.create`, `users.read`, `users.edit`, `users.delete`, `users.manage`
- **Roles**: `roles.create`, `roles.read`, `roles.manage`
- **Datasets**: `datasets.upload`, `datasets.view`, `datasets.delete`
- **Dashboards**: `dashboard.view`, `dashboard.manage`
- **Reports**: `reports.generate`, `reports.view`, `reports.export`
- **Analytics**: `analytics.view`, `analytics.manage`, `analytics.export`
- **Pipelines**: `pipelines.create`, `pipelines.execute`, `pipelines.view`
- **ETL**: `etl.import`, `etl.export`
- **AI**: `ai.use`
- **ML**: `ml.read`, `ml.write`, `ml.execute`, `ml.delete`
- **Settings**: `settings.manage`
- **Audit**: `audit.view`
- **Organizations**: `organizations.manage`, `departments.manage`
- **Sessions**: `sessions.manage`
- **Profile**: `profile.update`

### Authentication (JWT + Sessions)

`authentication/routes.py` issues short-lived **JWT access tokens** and
longer-lived **refresh tokens** on `POST /login`, `POST /register`
(auto-login), and `POST /refresh` (`shared/security.py::create_access_token` /
`create_refresh_token`). The access token embeds `email`, `roles`,
`permissions`, and `org_id` as claims so downstream services can authorize
without an extra DB round trip, though `get_current_user` re-resolves roles
and permissions from the database on every request for freshness.

Refresh tokens are persisted server-side in the `sessions` table
(`authentication/models.py::Session`: `user_id`, `refresh_token`,
`ip_address`, `user_agent`, `device`, `expires_at`, `revoked_at`,
`is_active`, `last_activity_at`), enabling `POST /logout` to revoke a single
session and supporting session management/listing (`sessions.manage`
permission). MFA support is layered on via `authentication/mfa_service.py`
and `mfa_models.py`; SSO via `sso_service.py`/`sso_models.py`.

### Enforcement

`shared/dependencies.py::get_current_user` is the core FastAPI dependency:
it decodes the bearer JWT (`shared/security.py::decode_token`), verifies the
token type is `"access"`, loads the user, and re-fetches their `roles` and
`permissions` (`UserRoleRepository`) to return a dict:
`{id, email, roles, permissions, organization_id}`.

Two dependency factories build on top of it:
- `require_permissions(*perms)` — requires the user to hold **at least one**
  of the listed permissions (`super_admin` bypasses the check). Used as a
  route dependency, e.g. `Depends(require_permissions("users.read"))`.
- `require_any_role(*roles)` — requires the user to hold **at least one** of
  the listed roles (`super_admin` bypasses the check).

## Tenant Isolation Mechanism

Multi-tenancy is enforced centrally in `shared/tenant.py` rather than being
left to individual routes to re-implement:

- `get_current_organization_id(current_user, db=None)` — returns the
  authenticated user's `organization_id`. If the user is a `super_admin`
  with no assigned organization, it falls back to a reserved `"system"`
  organization (looked up by slug) when a DB session is provided; otherwise
  it raises `403 Forbidden`.
- `is_super_admin(current_user)` — checks whether `"super_admin"` is present
  in the user's role set.
- `require_organization_access(current_user, organization_id=None, db=None)`
  — authorizes cross-organization access. Super admins may access any
  organization (or their own/`"system"` by default); every other user may
  only access their own `organization_id` — any mismatch raises
  `AuthorizationError`.
- `require_super_admin(current_user)` — raises `AuthorizationError` unless
  the user is a super admin.
- `apply_organization_filter(query, model, organization_id)` — appends a
  `model.organization_id == organization_id` predicate to a SQLAlchemy
  `Select`, used by repository/service code that builds custom queries.
- `get_tenant_context(current_user, db)` — a FastAPI dependency that bundles
  `user`, `user_id`, `organization_id`, `is_super_admin`, and `db` into a
  single object for route handlers (`tenant["organization_id"]`).
- `tenant_scoped_dependency()` — factory returning a dependency that resolves
  directly to the caller's `organization_id`.

### `TenantQueryManager`

For routes/services that need to read and write organization-owned rows,
`TenantQueryManager(db, organization_id, allow_cross_org=False)` provides a
safe, reusable query surface that automatically applies an
`organization_id` filter (when the model has that column):
- `list(model_cls, **filters)` — list rows scoped to the organization
- `get(model_cls, resource_id)` — fetch a row by id, scoped to the
  organization (returns `None` for rows belonging to another org, preventing
  ID-guessing attacks)
- `get_or_404(model_cls, resource_id)` — same as `get`, raising
  `NotFoundError` instead of returning `None`
- `create(model_cls, **data)` — creates a row, auto-injecting
  `organization_id` if the model supports it and it wasn't already supplied

Together, these guarantee that customer-owned resources (datasets,
dashboards, reports, pipelines, etc.) can never be read or mutated across
organization boundaries by a non-super-admin user, and that every access
path funnels through the same, auditable helper layer instead of ad-hoc
`WHERE` clauses scattered across route handlers.

### Resource-level access

Beyond org-level isolation, `authentication/models.py::Resource` supports
finer-grained, per-resource access control: each tracked resource
(`resource_type` + `resource_id`) can be scoped to an `organization_id` and
`department_id`, has an `owner_id`, and carries an `access_level`
(`private`, `department`, `organization`, `public`) plus an `is_public` flag
— enabling resource sharing within a department or organization without
granting blanket organization-wide access.

## Navigation Access Control

`frontend/lib/navigation.ts` drives which sidebar items a user sees, based on
their roles and permissions — the client never renders (and the user is
never routed to) a screen for a capability they cannot use.

- `ALL_NAV_ITEMS` defines every possible navigation entry, each optionally
  tagged with a `permission` (e.g. `datasets: { ..., permission:
  'datasets.view' }`), a single required `role` (e.g. `adminPortal: { ...,
  role: 'super_admin' }`), a `roles` allow-list, or an `excludeRoles`
  deny-list.
- `getRoleProfile(role)` returns a `RoleProfile` (a `purpose` string plus
  grouped `NavGroup`s) per primary role, falling back to `DEFAULT_PROFILE`.
- `getPrimaryRole(roles)` picks the single highest-priority role from a
  user's role list (super_admin > org_owner > ... > viewer) to select which
  profile/layout to render.
- `buildNavigation(ctx: NavContext)` — given `{ roles, permissions,
  featureFlags }` — filters the selected profile's groups/items through:
  - `hasPermission(item.permission)` — true if no permission is required, the
    user is `super_admin`, or the user's permission list includes it
  - `passesRoleFilter(item)` — enforces `role`/`roles`/`excludeRoles`
  - a feature-flag filter for flag-gated items
  - then sorts remaining items by `order`
- `getNavigationPurpose(roles)` — returns the human-readable purpose string
  for the user's primary role (shown as sidebar/dashboard context).

This mirrors the backend model exactly: the same permission strings
(`datasets.view`, `reports.view`, `dashboard.manage`, `audit.view`,
`settings.manage`, etc.) and the same `super_admin` bypass rule are used on
both sides, so navigation visibility and API authorization stay consistent.

## API Access Patterns

Typical patterns used across backend routes:

1. **Authenticate**: `current_user: dict = Depends(get_current_user)` on
   every protected route.
2. **Authorize by permission**: add
   `dependencies=[Depends(require_permissions("reports.generate"))]` (or
   check permissions inline) when an endpoint requires a specific capability.
3. **Authorize by role**: use `Depends(require_any_role("org_admin",
   "org_owner"))` for admin-only endpoints, or `require_super_admin
   (current_user)` for platform-only endpoints (e.g. cross-organization
   administration).
4. **Resolve tenant**: call `get_current_organization_id(current_user, db)`
   (or take an `org_id` from a request path/body and validate it with
   `require_organization_access`) to determine which organization's data the
   request may touch.
5. **Scope all queries**: use `TenantQueryManager(db, org_id)` or
   `apply_organization_filter(query, Model, org_id)` for any read/write
   against organization-owned tables, ensuring no cross-tenant leakage even
   if a client supplies another organization's resource id.
6. **Audit**: mutating actions (e.g. presentation generation in
   `services/dataset_workflow_routes.py`) call `log_audit_event(...)` with
   the acting `user_id`, `organization_id`, `resource_type`/`resource_id`,
   and a diff of `old_values`/`new_values`, feeding the `audit.view`-gated
   audit log.

This layered approach — JWT authentication, role/permission checks, and
organization-scoped query helpers — is applied consistently from the
dataset workflow and report/presentation engine (see
`REPORT_AND_PRESENTATION_ENGINE.md`) through to administrative and platform
routes.
