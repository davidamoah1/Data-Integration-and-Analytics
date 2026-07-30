# Database Indexing

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Database Architect

---

## Purpose

Document the index strategy for performance optimization.

## Scope

All indexed columns and their rationale.

## Audience

Developers and database administrators.

---

## 1. Index Strategy

Indexes are defined at the SQLAlchemy model level using `index=True` on columns and explicit `Index` definitions.

## 2. Indexed Columns

### users

| Column | Index Type | Rationale |
|--------|------------|----------|
| `id` | Primary Key | Default PK index |
| `email` | Unique | Login lookup |
| `organization_id` | B-Tree | Org-scoped user queries |
| `department_id` | B-Tree | Department-scoped queries |

### roles

| Column | Index Type | Rationale |
|--------|------------|----------|
| `id` | Primary Key | Default PK index |
| `name` | Unique | Role name lookup |

### permissions

| Column | Index Type | Rationale |
|--------|------------|----------|
| `id` | Primary Key | Default PK index |
| `name` | Unique | Permission name lookup |
| `module` | B-Tree | Module-grouped queries |

### role_permissions

| Column | Index Type | Rationale |
|--------|------------|----------|
| `role_id` | B-Tree | Role-permission lookup |
| `permission_id` | B-Tree | Permission-role lookup |

### user_roles

| Column | Index Type | Rationale |
|--------|------------|----------|
| `user_id` | B-Tree | User-role lookup |
| `role_id` | B-Tree | Role-user lookup |

### sessions

| Column | Index Type | Rationale |
|--------|------------|----------|
| `user_id` | B-Tree | User session lookup |
| `refresh_token` | Unique | Token validation |

### audit_logs

| Index Name | Columns | Rationale |
|------------|---------|----------|
| `idx_audit_org_created` | `(organization_id, created_at)` | Org-scoped time queries |
| `idx_audit_user_action` | `(user_id, action)` | User activity queries |
| `idx_audit_resource` | `(resource_type, resource_id)` | Resource history |

### activity_logs

| Column | Index Type | Rationale |
|--------|------------|----------|
| `user_id` | B-Tree | User activity lookup |
| `action` | B-Tree | Action type filter |

### invitations

| Column | Index Type | Rationale |
|--------|------------|----------|
| `token` | Unique | Token lookup on acceptance |

## 3. Composite Indexes

| Table | Index | Columns | Use Case |
|-------|-------|---------|----------|
| `audit_logs` | `idx_audit_org_created` | `(organization_id, created_at)` | List audit logs by org, sorted by date |
| `audit_logs` | `idx_audit_user_action` | `(user_id, action)` | User activity by action type |
| `audit_logs` | `idx_audit_resource` | `(resource_type, resource_id)` | Resource change history |

## 4. Future Index Additions

- Add composite index on `user_roles(user_id, role_id)` for faster role lookups
- Add index on `audit_logs.created_at` for time-range queries
- Add index on `sessions.expires_at` for session cleanup queries
- Consider partial indexes for `is_deleted = 0` filter

## Related Documents

- [schema.md](schema.md) — Complete schema
- [optimization.md](optimization.md) — Query optimization
- [entity-relationship.md](entity-relationship.md) — ER diagram
