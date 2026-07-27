# Organization Management Guide — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-27

---

## 1. Organization Model

The platform is multi-tenant. Each tenant is an `Organization`, which contains:

- Users
- Datasets
- Dashboards
- Reports
- Departments and teams
- Subscriptions and usage limits

```
Platform
 ├── Organization A
 │   ├── Users (organization_admin, analyst, viewer)
 │   ├── Datasets
 │   ├── Dashboards
 │   └── Departments / Teams
 └── Organization B
     └── ...
```

---

## 2. Organization Data Model

Key fields in the `organizations` table:

- `id`
- `name`
- `slug` (unique)
- `description`
- `contact_email`
- `is_active`
- `is_deleted` (soft delete)
- `created_at` / `updated_at`

Related tables:

- `departments`
- `branches`
- `teams`
- `team_members`

---

## 3. User Membership

Every user has an `organization_id`. A user can only belong to one organization at a time. Cross-organization access is denied by default and only allowed for `super_admin`.

---

## 4. API Endpoints

### 4.1 Organizations

| Method | Endpoint | Access |
| :--- | :--- | :--- |
| GET | `/api/organizations` | View own org; super admin sees all |
| POST | `/api/organizations` | `organizations.manage` (super admin) |
| GET | `/api/organizations/{id}` | Member of org or super admin |
| PUT | `/api/organizations/{id}` | `organizations.manage` |
| DELETE | `/api/organizations/{id}` | `organizations.manage` |

### 4.2 Departments

| Method | Endpoint | Access |
| :--- | :--- | :--- |
| GET | `/api/departments?organization_id=` | Within user's org |
| POST | `/api/departments` | `departments.manage` within org |
| GET | `/api/departments/{id}` | Within user's org |
| PUT | `/api/departments/{id}` | `departments.manage` within org |
| DELETE | `/api/departments/{id}` | `departments.manage` within org |

### 4.3 Admin panel

| Method | Endpoint | Access |
| :--- | :--- | :--- |
| GET | `/api/admin/organizations` | `admin.organizations.read` |
| POST | `/api/admin/organizations/{id}/suspend` | `admin.organizations.manage` (super admin) |
| POST | `/api/admin/organizations/{id}/activate` | `admin.organizations.manage` (super admin) |
| GET | `/api/admin/organizations/{id}/usage` | `admin.organizations.read` |
| GET | `/api/admin/users` | `admin.users.read` |
| POST | `/api/admin/users/{id}/disable` | `admin.users.manage` |
| POST | `/api/admin/users/{id}/enable` | `admin.users.manage` |
| POST | `/api/admin/users/{id}/roles` | `admin.users.manage` |
| GET | `/api/admin/metrics` | `admin.metrics.read` |

---

## 5. Tenant Isolation

All repository queries must include `organization_id` filtering. Use the helpers in `shared/tenant.py`:

```python
from shared.tenant import require_organization_access

org_id = require_organization_access(current_user, requested_org_id)
```

Super admins bypass the check. Regular users are limited to their own organization.

---

## 6. Lifecycle Operations

### Suspending an organization

- Sets `is_active = 0`.
- Existing sessions are invalidated on the next request because `get_current_user` checks `is_active`.
- No data is deleted.

### Soft deleting

- Sets `is_deleted = 1` and `deleted_at`.
- Soft-deleted organizations are excluded from queries.

---

## 7. Best Practices

- Always enforce organization scoping in new endpoints.
- Audit organization-level mutations (`admin.organization.suspend`, etc.).
- Use `slug` for URL-friendly identifiers but validate uniqueness.
- Provide organization branding through `platform_org_branding`.
- Monitor usage with `/api/analytics/usage/organizations`.
