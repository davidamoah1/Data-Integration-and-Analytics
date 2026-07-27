# RBAC Guide — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-27

---

## 1. Role Model

DataFlow uses a two-level role model:

### 1.1 Platform roles

| Role | Scope | Description |
| :--- | :--- | :--- |
| `super_admin` | Platform-wide | Full system access; can manage organizations, users, and global configuration |

### 1.2 Organization roles

| Role | Typical permissions |
| :--- | :--- |
| `organization_admin` | `users.manage`, `datasets.*`, `dashboards.*`, `organizations.read`, `admin.*` |
| `analyst` | `datasets.read`, `datasets.write`, `dashboards.read`, `dashboards.write`, `ai.*`, `reports.*` |
| `viewer` | `datasets.read`, `dashboards.read`, `reports.read` |

---

## 2. Permission Naming Convention

Permissions follow the pattern:

```
<resource>.<action>
```

Examples:

- `users.read`
- `users.manage`
- `organizations.manage`
- `datasets.read`
- `datasets.write`
- `dashboards.read`
- `dashboards.write`
- `ai.interact`
- `reports.export`
- `validation.approve`
- `admin.users.manage`
- `admin.metrics.read`

---

## 3. Checking Permissions

### 3.1 In FastAPI routes

```python
from shared.dependencies import require_permissions

@router.post("/datasets")
async def create_dataset(
    current_user: dict = Depends(require_permissions("datasets.write")),
):
    ...
```

The user only needs **one** of the listed permissions.

### 3.2 In services

```python
from shared.tenant import is_super_admin

if not is_super_admin(current_user):
    require_organization_access(current_user, resource.organization_id)
```

---
## 4. Default Roles

During startup, `seed_default_data()` creates the default roles and permissions. You can extend these by:

1. Adding new rows to the `permissions` table.
2. Mapping them to roles in `role_permissions`.
3. Assigning roles to users in `user_roles`.

---

## 5. Organization Scoping

A user belongs to exactly one organization (`users.organization_id`). Resources must include an `organization_id` and queries must filter by it. The helper functions in `shared/tenant.py` centralize this logic.

---

## 6. Best Practices

- Never check only the role string; prefer permission checks.
- Always combine permission checks with organization scoping.
- Log permission changes and role assignments to `audit_logs`.
- Review role assignments quarterly, especially for `super_admin`.
