# Enterprise Permission Matrix

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Applies to**: DataFlow v2.0.0+

---

## 1. Overview

This document defines the complete permission model for the DataFlow platform. Every role, module, action, and permission string is documented here and must remain synchronized with the source code.

### Permission Naming Convention

All permissions follow the pattern: `module.action`

- `module` — the functional area (e.g., `datasets`, `reports`, `users`)
- `action` — the specific operation (e.g., `create`, `read`, `manage`, `export`)

The special permission `*` grants all permissions and is reserved for `super_admin` only.

---

## 2. Roles

### 2.1 Platform-Level Roles

| Role | System Name | Level | Description | Assignable via Invitation |
|------|-------------|-------|-------------|---------------------------|
| Platform Owner | `super_admin` | 100 | Full system access, all permissions | No |
| Organization Owner | `org_owner` | 100 | Full org access, all permissions except `settings.manage` | No |

### 2.2 Organization-Level Roles

| Role | System Name | Level | Description | Assignable via Invitation |
|------|-------------|-------|-------------|---------------------------|
| Organization Administrator | `org_admin` | 80 | Manage users, data, and settings within org | Yes |
| Department Manager | `dept_manager` | 60 | Manage department operations and view org data | Yes |
| Data Engineer | `data_engineer` | 40 | Build and run ETL pipelines | Yes |
| Data Analyst | `data_analyst` | 40 | Analyze data, create reports and dashboards | Yes |
| Business Analyst | `business_analyst` | 40 | View dashboards and reports | Yes |
| Executive | `executive` | 60 | View high-level analytics and reports | Yes |
| Department Officer | `dept_officer` | 20 | Department-level read-only operations | Yes |
| Auditor | `auditor` | 40 | View audit logs and security events | Yes |
| Researcher | `researcher` | 40 | Upload research datasets, perform statistical analysis | Yes |
| Data Entry Officer | `data_entry_officer` | 20 | Upload documents, use Smart Data Capture | Yes |
| Viewer | `viewer` | 20 | Read-only access to dashboards | Yes |

### 2.3 Special Roles

| Role | System Name | Description |
|------|-------------|-------------|
| Personal Workspace User | `viewer` (no org) | User with personal workspace, no organization membership |

> **Note**: Personal workspace users are assigned the `viewer` role with `organization_id = NULL`. They can upgrade by joining or creating an organization.

---

## 3. Permission Definitions

### 3.1 User Management (`users`)

| Permission | Label | Description |
|------------|-------|-------------|
| `users.create` | Create Users | Create new user accounts within the organization |
| `users.read` | View Users | View user profiles within the organization |
| `users.edit` | Edit Users | Edit user information within the organization |
| `users.delete` | Delete Users | Soft-delete user accounts |
| `users.manage` | Full User Management | Administrative user management (includes create, read, edit, delete) |

### 3.2 Role Management (`roles`)

| Permission | Label | Description |
|------------|-------|-------------|
| `roles.create` | Create Roles | Create custom roles with specific permissions |
| `roles.read` | View Roles | View roles and their permission assignments |
| `roles.manage` | Manage Roles | Full role management (create, update, delete, assign permissions) |

### 3.3 Pipeline Management (`pipelines`)

| Permission | Label | Description |
|------------|-------|-------------|
| `pipelines.create` | Create Pipelines | Create new ETL pipelines |
| `pipelines.execute` | Execute Pipelines | Run ETL pipelines |
| `pipelines.view` | View Pipelines | View pipeline status and configuration |

### 3.4 ETL Operations (`etl`)

| Permission | Label | Description |
|------------|-------|-------------|
| `etl.import` | Import Data | Import data via ETL pipelines |
| `etl.export` | Export Data | Export data from ETL pipelines |

### 3.5 Dashboards (`dashboard`)

| Permission | Label | Description |
|------------|-------|-------------|
| `dashboard.view` | View Dashboards | View dashboards |
| `dashboard.manage` | Manage Dashboards | Create, edit, and delete dashboards |

### 3.6 Reports (`reports`)

| Permission | Label | Description |
|------------|-------|-------------|
| `reports.generate` | Generate Reports | Generate new reports from data |
| `reports.export` | Export Reports | Export report files (PDF, CSV, Excel) |
| `reports.view` | View Reports | View existing reports |

### 3.7 Datasets (`datasets`)

| Permission | Label | Description |
|------------|-------|-------------|
| `datasets.upload` | Upload Datasets | Upload new datasets |
| `datasets.delete` | Delete Datasets | Delete datasets |
| `datasets.view` | View Datasets | View datasets and their metadata |

### 3.8 Analytics (`analytics`)

| Permission | Label | Description |
|------------|-------|-------------|
| `analytics.view` | View Analytics | View analytics dashboards and KPIs |
| `analytics.manage` | Manage Analytics | Create and manage dashboards and KPIs |
| `analytics.export` | Export Analytics | Export dashboards and analytics data |

### 3.9 AI Features (`ai`)

| Permission | Label | Description |
|------------|-------|-------------|
| `ai.use` | Use AI Features | Access AI predictions, insights, and conversational analytics |

### 3.10 Machine Learning (`ml`)

| Permission | Label | Description |
|------------|-------|-------------|
| `ml.read` | View ML Models | View machine learning models and dashboards |
| `ml.write` | Create ML Models | Create and edit machine learning models |
| `ml.execute` | Execute ML Training | Train, predict, and run ML jobs |
| `ml.delete` | Delete ML Models | Archive or delete ML models |

### 3.11 Settings (`settings`)

| Permission | Label | Description |
|------------|-------|-------------|
| `settings.manage` | Manage Settings | Manage system-level settings (platform-level only) |

### 3.12 Audit (`audit`)

| Permission | Label | Description |
|------------|-------|-------------|
| `audit.view` | View Audit Logs | View audit logs and security events |

### 3.13 Notifications (`notifications`)

| Permission | Label | Description |
|------------|-------|-------------|
| `notifications.manage` | Manage Notifications | Manage notification settings |

### 3.14 Organization (`organizations`)

| Permission | Label | Description |
|------------|-------|-------------|
| `organizations.manage` | Manage Organizations | Manage organization settings and configuration |
| `departments.manage` | Manage Departments | Create and manage departments within the organization |

### 3.15 Sessions (`sessions`)

| Permission | Label | Description |
|------------|-------|-------------|
| `sessions.manage` | Manage Sessions | Revoke user sessions and manage active sessions |

### 3.16 Profile (`profile`)

| Permission | Label | Description |
|------------|-------|-------------|
| `profile.update` | Update Profile | Update own profile information |

---

## 4. Role-Permission Mapping

### 4.1 Platform Owner (`super_admin`)

| Module | Permissions |
|--------|-------------|
| All modules | `*` (all permissions) |

### 4.2 Organization Owner (`org_owner`)

| Module | Permissions |
|--------|-------------|
| All modules | All permissions except `settings.manage` |

### 4.3 Organization Administrator (`org_admin`)

| Module | Permissions |
|--------|-------------|
| Users | `users.create`, `users.read`, `users.edit`, `users.delete`, `users.manage` |
| Roles | `roles.read` |
| Pipelines | `pipelines.create`, `pipelines.execute`, `pipelines.view` |
| ETL | `etl.import`, `etl.export` |
| Dashboards | `dashboard.view`, `dashboard.manage` |
| Reports | `reports.generate`, `reports.export`, `reports.view` |
| Datasets | `datasets.upload`, `datasets.view` |
| Analytics | `analytics.view` |
| Notifications | `notifications.manage` |
| Departments | `departments.manage` |
| Sessions | `sessions.manage` |
| Profile | `profile.update` |
| Audit | `audit.view` |
| ML | `ml.read`, `ml.write`, `ml.execute`, `ml.delete` |

### 4.4 Department Manager (`dept_manager`)

| Module | Permissions |
|--------|-------------|
| Users | `users.read` |
| Pipelines | `pipelines.view` |
| ETL | `etl.import`, `etl.export` |
| Dashboards | `dashboard.view` |
| Reports | `reports.view`, `reports.generate`, `reports.export` |
| Datasets | `datasets.view` |
| Analytics | `analytics.view` |
| Profile | `profile.update` |
| ML | `ml.read`, `ml.execute` |

### 4.5 Data Engineer (`data_engineer`)

| Module | Permissions |
|--------|-------------|
| Pipelines | `pipelines.create`, `pipelines.execute`, `pipelines.view` |
| ETL | `etl.import`, `etl.export` |
| Datasets | `datasets.upload`, `datasets.view` |
| Dashboards | `dashboard.view` |
| Profile | `profile.update` |
| ML | `ml.read`, `ml.execute` |

### 4.6 Data Analyst (`data_analyst`)

| Module | Permissions |
|--------|-------------|
| Dashboards | `dashboard.view` |
| Reports | `reports.generate`, `reports.view` |
| Datasets | `datasets.view` |
| Analytics | `analytics.view` |
| ETL | `etl.export` |
| Profile | `profile.update` |
| ML | `ml.read`, `ml.execute` |

### 4.7 Business Analyst (`business_analyst`)

| Module | Permissions |
|--------|-------------|
| Dashboards | `dashboard.view` |
| Reports | `reports.view` |
| Datasets | `datasets.view` |
| Analytics | `analytics.view` |
| Profile | `profile.update` |

### 4.8 Executive (`executive`)

| Module | Permissions |
|--------|-------------|
| Dashboards | `dashboard.view` |
| Reports | `reports.view` |
| Analytics | `analytics.view` |
| Profile | `profile.update` |

### 4.9 Department Officer (`dept_officer`)

| Module | Permissions |
|--------|-------------|
| Dashboards | `dashboard.view` |
| Reports | `reports.view` |
| Datasets | `datasets.view` |
| Profile | `profile.update` |

### 4.10 Auditor (`auditor`)

| Module | Permissions |
|--------|-------------|
| Audit | `audit.view` |
| Users | `users.read` |
| Profile | `profile.update` |

### 4.11 Researcher (`researcher`)

| Module | Permissions |
|--------|-------------|
| Datasets | `datasets.upload`, `datasets.view` |
| Dashboards | `dashboard.view` |
| Analytics | `analytics.view` |
| Reports | `reports.generate`, `reports.view`, `reports.export` |
| ETL | `etl.export` |
| Profile | `profile.update` |
| ML | `ml.read`, `ml.execute` |

### 4.12 Data Entry Officer (`data_entry_officer`)

| Module | Permissions |
|--------|-------------|
| Datasets | `datasets.upload`, `datasets.view` |
| Profile | `profile.update` |

### 4.13 Viewer (`viewer`)

| Module | Permissions |
|--------|-------------|
| Dashboards | `dashboard.view` |
| Profile | `profile.update` |

---

## 5. Module-Permission Mapping

| Module | Available Actions | Permission Strings |
|--------|-------------------|-------------------|
| Landing Page | Read (public) | None required |
| Authentication | Login, Logout, Refresh | None required |
| Registration | Signup (public), Accept Invitation (public) | None required |
| Organizations | Create, Read, Update, Delete, Manage | `organizations.manage` |
| Workspaces | Create (auto on signup), Read | None (implicit) |
| Departments | Create, Read, Update, Delete, Manage | `departments.manage` |
| Users | Create, Read, Update, Delete, Manage, Assign Roles | `users.*` |
| Roles | Create, Read, Update, Delete, Manage | `roles.*` |
| Permissions | Read (via role management) | `roles.read`, `roles.manage` |
| Analytics Studio | View, Manage, Export | `analytics.view`, `analytics.manage`, `analytics.export` |
| Dashboards | View, Manage | `dashboard.view`, `dashboard.manage` |
| Reports | Generate, View, Export | `reports.generate`, `reports.view`, `reports.export` |
| Dataset Management | Upload, View, Delete | `datasets.upload`, `datasets.view`, `datasets.delete` |
| Data Integration (ETL) | Import, Export | `etl.import`, `etl.export` |
| Pipelines | Create, Execute, View | `pipelines.create`, `pipelines.execute`, `pipelines.view` |
| Smart Data Capture | Upload, Use | `datasets.upload` |
| AI Assistant | Use | `ai.use` |
| Machine Learning | Read, Write, Execute, Delete | `ml.read`, `ml.write`, `ml.execute`, `ml.delete` |
| Studios | View (via dashboard) | `dashboard.view` |
| Templates | View, Use | `dashboard.view` |
| Notifications | View, Manage | `notifications.manage` |
| Settings | View, Manage | `settings.manage` (platform), `profile.update` (personal) |
| Audit Logs | View | `audit.view` |
| Sessions | Manage, Revoke | `sessions.manage` |
| Billing (placeholder) | View | None (placeholder page) |
| API Keys (future) | — | Not yet implemented |
| Integrations / Connectors | View, Configure | None (placeholder pages) |
| Webhooks | View, Configure | None (placeholder pages) |
| Marketplace | View | None (placeholder page) |
| Scheduler | View, Schedule | None (placeholder page) |
| Help Center | Read (public) | None required |
| Documentation | Read (public) | None required |

---

## 6. Permission Inheritance Rules

1. **`super_admin`** inherits all permissions via the `*` wildcard.
2. **`org_owner`** inherits all permissions except `settings.manage`.
3. **`users.manage`** is a superset of `users.create`, `users.read`, `users.edit`, and `users.delete`.
4. **`roles.manage`** is a superset of `roles.create` and `roles.read`.
5. All other permissions require explicit assignment via role-permission mapping.
6. Custom roles can be created with any subset of permissions (requires `roles.manage`).
7. System roles (`is_system = 1`) cannot be deleted but can have their permissions updated.

---

## 7. Restriction Rules

1. **Organization scoping**: Non-super-admin users can only access resources within their `organization_id`.
2. **Platform-level roles** (`super_admin`, `org_owner`) cannot be assigned via invitation.
3. **Role assignment**: Non-super-admin users cannot assign `super_admin` or `org_owner` roles.
4. **Cross-tenant access**: All API routes enforce `require_organization_access` for org-scoped resources.
5. **User listing**: Non-super-admin users see only users within their organization.
6. **Organization management**: Update and delete operations require `require_organization_access` in addition to `organizations.manage` permission.
7. **System role protection**: System roles cannot be soft-deleted.
8. **Invitation role restriction**: Invitations cannot specify `super_admin` or `org_owner` roles.

---

## 8. Future Extension Points

The permission model is designed to support future expansion without redesign:

1. **New modules**: Add new permission strings following `module.action` convention.
2. **New roles**: Create custom roles via the RoleService API or database seeding.
3. **Fine-grained permissions**: Current permissions can be split (e.g., `datasets.upload.csv`, `datasets.upload.excel`) without breaking existing role mappings.
4. **Attribute-based access control (ABAC)**: The `TenantContext` already carries org_id, user_id, and roles — can be extended with attributes for ABAC.
5. **Workspace-level permissions**: The Workspace model supports per-workspace scoping when implemented.

---

## Cross-References

- **Machine-readable definitions**: See `permission-matrix.json`
- **API authorization mapping**: See `api-authorization-matrix.md`
- **Frontend navigation rules**: See `frontend-navigation-matrix.md`
- **RBAC implementation**: `platform_features/rbac.py`, `shared/dependencies.py`
- **Role seeding**: `authentication/services.py:seed_default_data()`
- **Frontend permissions**: `frontend/lib/permissions.ts`
