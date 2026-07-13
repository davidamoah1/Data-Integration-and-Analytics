# RBAC Permission Matrix

## Roles × Permissions

| Permission | super_admin | org_owner | org_admin | dept_manager | data_engineer | data_analyst | business_analyst | executive | dept_officer | auditor | viewer |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **User Management** | | | | | | | | | | | |
| users.create | ✓ | ✓ | ✓ | | | | | | | | |
| users.read | ✓ | ✓ | ✓ | ✓ | | | | | | ✓ | |
| users.update | ✓ | ✓ | ✓ | ✓ | | | | | | | |
| users.delete | ✓ | ✓ | ✓ | | | | | | | | |
| users.assign_roles | ✓ | ✓ | ✓ | | | | | | | | |
| **Role Management** | | | | | | | | | | | |
| roles.create | ✓ | | | | | | | | | | |
| roles.read | ✓ | ✓ | ✓ | | | | | | | ✓ | |
| roles.update | ✓ | | | | | | | | | | |
| roles.delete | ✓ | | | | | | | | | | |
| **Organization** | | | | | | | | | | | |
| organizations.create | ✓ | | | | | | | | | | |
| organizations.read | ✓ | ✓ | ✓ | ✓ | | | | ✓ | | ✓ | |
| organizations.update | ✓ | ✓ | ✓ | | | | | | | | |
| organizations.delete | ✓ | | | | | | | | | | |
| **Departments** | | | | | | | | | | | |
| departments.create | ✓ | ✓ | ✓ | | | | | | | | |
| departments.read | ✓ | ✓ | ✓ | ✓ | | | | ✓ | ✓ | ✓ | |
| departments.update | ✓ | ✓ | ✓ | ✓ | | | | | | | |
| departments.delete | ✓ | ✓ | ✓ | | | | | | | | |
| **Pipelines** | | | | | | | | | | | |
| pipelines.execute | ✓ | | | | ✓ | | | | | | |
| pipelines.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | | ✓ | |
| pipelines.manage | ✓ | ✓ | ✓ | | ✓ | | | | | | |
| **Datasets** | | | | | | | | | | | |
| datasets.create | ✓ | | | | ✓ | | | | | | |
| datasets.read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| datasets.update | ✓ | | | | ✓ | | | | | | |
| datasets.delete | ✓ | | | | ✓ | | | | | | |
| **Analytics** | | | | | | | | | | | |
| analytics.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| analytics.export | ✓ | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | |
| **Reports** | | | | | | | | | | | |
| reports.create | ✓ | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | |
| reports.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| reports.delete | ✓ | ✓ | ✓ | | | | | | | | |
| **Dashboard** | | | | | | | | | | | |
| dashboard.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Audit** | | | | | | | | | | | |
| audit.view | ✓ | | | | | | | ✓ | | ✓ | |
| audit.export | ✓ | | | | | | | | | ✓ | |
| **AI** | | | | | | | | | | | |
| ai.request | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | | |
| ai.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | | | |
| **Settings** | | | | | | | | | | | |
| settings.view | ✓ | ✓ | ✓ | | | | | | | | |
| settings.update | ✓ | ✓ | ✓ | | | | | | | | |
| **Notifications** | | | | | | | | | | | |
| notifications.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| notifications.manage | ✓ | ✓ | ✓ | | | | | | | | |

## Permission Modules

### users.* — User Management
- `users.create` — Create new user accounts
- `users.read` — View user profiles and listings
- `users.update` — Update user information
- `users.delete` — Soft-delete user accounts
- `users.assign_roles` — Assign/revoke roles to/from users

### roles.* — Role Management
- `roles.create` — Create custom roles
- `roles.read` — View roles and their permissions
- `roles.update` — Modify role permissions
- `roles.delete` — Delete non-system roles

### organizations.* — Organization Management
- `organizations.create` — Create new organizations
- `organizations.read` — View organization details
- `organizations.update` — Update organization settings
- `organizations.delete` — Delete organizations

### departments.* — Department Management
- `departments.create` — Create departments within an organization
- `departments.read` — View department listings
- `departments.update` — Update department information
- `departments.delete` — Delete departments

### pipelines.* — ETL Pipeline Management
- `pipelines.execute` — Trigger pipeline runs
- `pipelines.view` — View pipeline status and history
- `pipelines.manage` — Configure pipeline settings

### datasets.* — Dataset Management
- `datasets.create` — Upload/create datasets
- `datasets.read` — View dataset contents
- `datasets.update` — Modify datasets
- `datasets.delete` — Delete datasets

### analytics.* — Analytics
- `analytics.view` — View analytics dashboards
- `analytics.export` — Export analytics data

### reports.* — Reporting
- `reports.create` — Create and schedule reports
- `reports.view` — View generated reports
- `reports.delete` — Delete reports

### dashboard.* — Dashboard
- `dashboard.view` — Access the main dashboard

### audit.* — Audit Logging
- `audit.view` — View audit logs
- `audit.export` — Export audit logs

### ai.* — AI Features
- `ai.request` — Make AI predictions/requests
- `ai.view` — View AI model results

### settings.* — System Settings
- `settings.view` — View system settings
- `settings.update` — Modify system settings

### notifications.* — Notifications
- `notifications.view` — View notifications
- `notifications.manage` — Manage notification preferences

## Enforcement

Permissions are enforced via FastAPI dependencies:

```python
# Single permission
@router.get("/users", dependencies=[Depends(require_permissions("users.read"))])

# Multiple permissions (user needs at least one)
@router.post("/users", dependencies=[Depends(require_permissions("users.create", "users.update"))])

# Role-based check
@router.delete("/roles/{id}", dependencies=[Depends(require_any_role("super_admin"))])
```

The `super_admin` role bypasses all permission checks.
