# Database Indexing

> **Version**: 2.0.0  
> **Last Updated**: 2026-08-01  
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

## 4. Production Indexes (Migration 0016)

Migration `0016_prod_indexes` adds 56 production-grade indexes across all major tables. The migration uses conditional creation (`_safe_create_index()`) that checks table and column existence before creating each index.

### Production Index Categories

| Category | Tables | Index Count | Purpose |
|----------|--------|-------------|---------|
| Tenant scoping | users, datasets, dashboards, reports, pipelines | 12 | `organization_id` filters |
| Time-based queries | audit_logs, activity_logs, pipeline_runs, sales | 15 | Date range + sorting |
| Composite lookups | audit_logs, pipeline_runs, sales | 18 | Multi-column query patterns |
| Status filters | pipeline_runs, jobs, sessions | 7 | Status-based filtering |
| Soft delete | All major tables | 4 | `is_deleted` exclusion |

### Key Composite Indexes

| Table | Index | Columns | Use Case |
|-------|-------|---------|----------|
| `sales` | `idx_sales_region_date` | `(region, order_date)` | Regional sales over time |
| `sales` | `idx_sales_category_date` | `(category, order_date)` | Category trends |
| `sales` | `idx_sales_customer_date` | `(customer_id, order_date)` | Customer purchase history |
| `pipeline_runs` | `idx_pipeline_status_started` | `(status, started_at)` | Pipeline status by time |
| `audit_logs` | `idx_audit_org_created` | `(organization_id, created_at)` | Org-scoped audit trail |
| `audit_logs` | `idx_audit_user_action` | `(user_id, action)` | User activity by action |
| `audit_logs` | `idx_audit_resource` | `(resource_type, resource_id)` | Resource change history |

### Conditional Index Creation

The migration uses helper functions to safely create indexes:

```python
def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()

def _column_exists(inspector, table_name, column_name):
    if not _table_exists(inspector, table_name):
        return False
    return column_name in [c['name'] for c in inspector.get_columns(table_name)]

def _safe_create_index(op, index_name, table_name, columns):
    # Only create if table and all columns exist
    ...
```

This ensures the migration is safe to run in any environment, regardless of which tables have been created.

## 5. IndexManager

The `IndexManager` class in `performance/db_optimization.py` provides runtime index management:

- `ensure_critical_indexes()`: Verifies and creates critical indexes
- `get_missing_indexes()`: Returns list of missing critical indexes
- `get_index_usage_stats()`: Returns index usage statistics (MySQL only)

### Critical Indexes

The `CRITICAL_INDEXES` list defines the minimum required indexes for production:
- `idx_sales_order_date` on `sales(order_date)`
- `idx_sales_region` on `sales(region)`
- `idx_pipeline_status_started` on `pipeline_runs(status, started_at)`
- `idx_audit_org_created` on `audit_logs(organization_id, created_at)`

## 6. Future Index Additions

- Add partial indexes for `is_deleted = 0` filter (MySQL 8.0+ supports functional indexes)
- Add full-text search indexes for report and dashboard names
- Consider covering indexes for high-frequency query patterns
- Monitor index usage and remove unused indexes

## Related Documents

- [schema.md](schema.md) — Complete schema
- [optimization.md](optimization.md) — Query optimization
- [entity-relationship.md](entity-relationship.md) — ER diagram
