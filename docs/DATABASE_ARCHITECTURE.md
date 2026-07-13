# Enterprise MySQL Database Architecture Specification

**Status:** Specification — Awaiting Approval  
**Date:** 2026-07-11  
**Author:** Principal Database Architect  
**Database:** MySQL 8.0+ (Hostinger)  
**Engine:** InnoDB  
**Charset:** utf8mb4 / utf8mb4_unicode_ci  

---

## Table of Contents

1. [Current Schema Assessment](#1-current-schema-assessment)
2. [Naming Conventions](#2-naming-conventions)
3. [Domain Structure](#3-domain-structure)
4. [Existing Tables — Keep / Improve / Extend](#4-existing-tables--keep--improve--extend)
5. [Authentication Domain](#5-authentication-domain)
6. [Organization Domain](#6-organization-domain)
7. [ETL Domain](#7-etl-domain)
8. [Dataset Domain](#8-dataset-domain)
9. [Analytics Domain](#9-analytics-domain)
10. [Reporting Domain](#10-reporting-domain)
11. [AI Domain](#11-ai-domain)
12. [Notification Domain](#12-notification-domain)
13. [Audit Domain](#13-audit-domain)
14. [Settings Domain](#14-settings-domain)
15. [Department Domain](#15-department-domain)
16. [Data Warehouse Domain](#16-data-warehouse-domain)
17. [Entity Relationship Diagram (ERD)](#17-entity-relationship-diagram-erd)
18. [Index Strategy](#18-index-strategy)
19. [Migration Strategy](#19-migration-strategy)
20. [File-by-File Migration Plan](#20-file-by-file-migration-plan)
21. [Data Dictionary](#21-data-dictionary)

---

## 1. Current Schema Assessment

### Existing Tables

| Table | Columns | Purpose | Rows | Status |
|-------|---------|---------|------|--------|
| `sales` | 15 cols (id, order_id, order_date, ship_date, customer_name, segment, region, category, sub_category, product_name, sales, quantity, discount, profit, created_at, updated_at) | Sales fact data from ETL pipeline | ~5,009 | **Keep — extend** |
| `pipeline_runs` | 10 cols (id, run_id, started_at, completed_at, status, rows_extracted, rows_transformed, rows_loaded, duplicates_removed, error_message) | ETL pipeline execution metadata | varies | **Keep — extend** |

### Current Issues

| Issue | Impact | Fix |
|-------|--------|-----|
| `sales` has denormalized customer/product data | Data redundancy, update anomalies | Add dimension tables (future), keep `sales` as fact table |
| No user/auth tables | No authentication support | Add Authentication domain |
| No audit trail | No compliance tracking | Add Audit domain |
| No foreign keys | No referential integrity | Add FKs in new tables, leave `sales` as-is for backward compat |
| `pipeline_runs` lacks triggered_by | Can't track who/what started the pipeline | Add `triggered_by` column via migration |
| No soft delete | Data permanently lost on delete | Add `is_deleted` + `deleted_at` to new tables |
| No organization/department scoping | Single-tenant only | Add Organization domain with optional FKs |

### Design Principles

- **Never drop or alter** `sales` or `pipeline_runs` in ways that break existing code
- **All new tables** use InnoDB, utf8mb4, proper FKs, timestamps, soft delete
- **Migrations only** — no direct schema changes to production
- **Backward compatible** — existing queries against `sales` and `pipeline_runs` must continue to work
- **Additive changes** — new columns to existing tables are nullable with defaults

---

## 2. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | `snake_case`, plural | `users`, `etl_jobs`, `audit_logs` |
| Columns | `snake_case` | `created_at`, `organization_id` |
| Primary keys | `id` (BIGINT UNSIGNED AUTO_INCREMENT) | `id` |
| Foreign keys | `{table_singular}_id` | `user_id`, `organization_id` |
| Indexes | `idx_{table}_{columns}` | `idx_users_email` |
| Unique constraints | `uq_{table}_{columns}` | `uq_users_email` |
| Foreign key constraints | `fk_{from}_{to}` | `fk_users_organization` |
| Timestamps | `created_at`, `updated_at` (TIMESTAMP, server_default) | All tables |
| Soft delete | `is_deleted` (TINYINT(1) DEFAULT 0), `deleted_at` (TIMESTAMP NULL) | All new tables |
| Boolean | `is_{property}` (TINYINT(1)) | `is_active`, `is_deleted` |
| Enums | VARCHAR(50) with CHECK constraint or app-level validation | `status`, `role` |

---

## 3. Domain Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Enterprise Database                        │
├─────────────┬──────────────┬──────────────┬──────────────────┤
│  Auth        │  Organization │  ETL         │  Dataset         │
│  Domain      │  Domain       │  Domain      │  Domain          │
├─────────────┼──────────────┼──────────────┼──────────────────┤
│  Analytics   │  Reporting    │  AI          │  Notification    │
│  Domain      │  Domain       │  Domain      │  Domain          │
├─────────────┼──────────────┼──────────────┼──────────────────┤
│  Audit       │  Settings     │  Department  │  Data Warehouse  │
│  Domain      │  Domain       │  Domain      │  Domain          │
└─────────────┴──────────────┴──────────────┴──────────────────┘
```

### Domain Summary

| Domain | Tables | Purpose |
|--------|--------|---------|
| Authentication | 9 | Users, roles, permissions, sessions, tokens |
| Organization | 5 | Organizations, branches, departments, teams |
| ETL | 11 | Data sources, connectors, jobs, logs, schedules |
| Dataset | 6 | Datasets, versions, columns, metadata |
| Analytics | 7 | Dashboards, widgets, charts, KPIs, saved filters |
| Reporting | 5 | Reports, templates, generated reports, exports |
| AI | 6 | Requests, predictions, insights, forecast models |
| Notification | 5 | Notifications, templates, preferences, queues |
| Audit | 4 | Audit logs, system logs, security logs, user activity |
| Settings | 4 | System settings, org settings, user prefs, feature flags |
| Department | 3+ | Department types with extensible related tables |
| Data Warehouse | 8 | Fact tables, dimension tables, aggregates, snapshots |
| **Existing** | 2 | `sales`, `pipeline_runs` (kept, extended) |
| **Total** | **~75** | |

---

## 4. Existing Tables — Keep / Improve / Extend

### `sales` — KEEP + EXTEND

**Current columns (unchanged):**
```sql
id              INT AUTO_INCREMENT PRIMARY KEY
order_id        VARCHAR(50) UNIQUE NOT NULL
order_date      DATE
ship_date       DATE
customer_name   VARCHAR(255)
segment         VARCHAR(100)
region          VARCHAR(100)
category        VARCHAR(100)
sub_category    VARCHAR(100)
product_name    VARCHAR(500)
sales           FLOAT NOT NULL DEFAULT 0
quantity        INT NOT NULL DEFAULT 0
discount        FLOAT NOT NULL DEFAULT 0
profit          FLOAT NOT NULL DEFAULT 0
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

**New columns (added via migration, all nullable for backward compat):**
```sql
ALTER TABLE sales
  ADD COLUMN organization_id  BIGINT UNSIGNED NULL,
  ADD COLUMN department_id     BIGINT UNSIGNED NULL,
  ADD COLUMN data_source_id   BIGINT UNSIGNED NULL,
  ADD COLUMN is_deleted       TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN deleted_at        TIMESTAMP NULL,
  ADD INDEX idx_sales_org_dept (organization_id, department_id),
  ADD INDEX idx_sales_data_source (data_source_id),
  ADD INDEX idx_sales_is_deleted (is_deleted);
```

**Existing indexes (kept):**
- `idx_order_id` (unique)
- `idx_order_date`
- `idx_customer_name`
- `idx_region`
- `idx_category`
- `idx_region_category` (composite)
- `idx_order_date_region` (composite)

### `pipeline_runs` — KEEP + EXTEND

**Current columns (unchanged):**
```sql
id                INT AUTO_INCREMENT PRIMARY KEY
run_id            VARCHAR(50) UNIQUE NOT NULL
started_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
completed_at      TIMESTAMP NULL
status            VARCHAR(20) NOT NULL DEFAULT 'running'
rows_extracted    INT DEFAULT 0
rows_transformed  INT DEFAULT 0
rows_loaded       INT DEFAULT 0
duplicates_removed INT DEFAULT 0
error_message     VARCHAR(1000)
```

**New columns (added via migration):**
```sql
ALTER TABLE pipeline_runs
  ADD COLUMN triggered_by      BIGINT UNSIGNED NULL COMMENT 'FK to users.id',
  ADD COLUMN trigger_source    VARCHAR(20) NULL DEFAULT 'manual' COMMENT 'manual|scheduler|api',
  ADD COLUMN etl_job_id        BIGINT UNSIGNED NULL COMMENT 'FK to etl_jobs.id',
  ADD COLUMN duration_seconds  INT NULL,
  ADD INDEX idx_pipeline_runs_triggered_by (triggered_by),
  ADD INDEX idx_pipeline_runs_etl_job_id (etl_job_id);
```

---

## 5. Authentication Domain

### `users`
```sql
CREATE TABLE users (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email           VARCHAR(255) NOT NULL,
  password_hash   VARCHAR(255) NOT NULL,
  full_name       VARCHAR(255) NOT NULL,
  avatar_url      VARCHAR(500) NULL,
  organization_id BIGINT UNSIGNED NULL,
  department_id   BIGINT UNSIGNED NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  last_login_at   TIMESTAMP NULL,
  email_verified_at TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_organization (organization_id),
  KEY idx_users_department (department_id),
  KEY idx_users_is_active (is_active),
  KEY idx_users_is_deleted (is_deleted),
  CONSTRAINT fk_users_organization FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_users_department FOREIGN KEY (department_id)
    REFERENCES departments (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `roles`
```sql
CREATE TABLE roles (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(50) NOT NULL COMMENT 'admin|analyst|viewer|etl_operator',
  display_name  VARCHAR(100) NOT NULL,
  description   TEXT NULL,
  is_system     TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'System roles cannot be deleted',
  is_deleted    TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at    TIMESTAMP NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_roles_name (name),
  KEY idx_roles_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `permissions`
```sql
CREATE TABLE permissions (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL COMMENT 'e.g. etl.trigger, analytics.view',
  display_name  VARCHAR(200) NOT NULL,
  module        VARCHAR(50) NOT NULL COMMENT 'etl|analytics|reports|users|settings',
  description   TEXT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_permissions_name (name),
  KEY idx_permissions_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `role_permissions`
```sql
CREATE TABLE role_permissions (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id       BIGINT UNSIGNED NOT NULL,
  permission_id BIGINT UNSIGNED NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_role_permissions (role_id, permission_id),
  KEY idx_role_permissions_permission (permission_id),
  CONSTRAINT fk_rp_role FOREIGN KEY (role_id)
    REFERENCES roles (id) ON DELETE CASCADE,
  CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id)
    REFERENCES permissions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `user_roles`
```sql
CREATE TABLE user_roles (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL,
  role_id       BIGINT UNSIGNED NOT NULL,
  assigned_by   BIGINT UNSIGNED NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_user_roles (user_id, role_id),
  KEY idx_user_roles_role (role_id),
  KEY idx_user_roles_assigned_by (assigned_by),
  CONSTRAINT fk_ur_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_role FOREIGN KEY (role_id)
    REFERENCES roles (id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_assigned_by FOREIGN KEY (assigned_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `sessions`
```sql
CREATE TABLE sessions (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  refresh_token   VARCHAR(500) NOT NULL,
  ip_address      VARCHAR(45) NULL,
  user_agent      VARCHAR(500) NULL,
  expires_at      TIMESTAMP NOT NULL,
  revoked_at      TIMESTAMP NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_sessions_token (refresh_token),
  KEY idx_sessions_user (user_id),
  KEY idx_sessions_expires (expires_at),
  KEY idx_sessions_active (is_active),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `password_resets`
```sql
CREATE TABLE password_resets (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL,
  token         VARCHAR(255) NOT NULL,
  expires_at    TIMESTAMP NOT NULL,
  used_at       TIMESTAMP NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_password_resets_token (token),
  KEY idx_password_resets_user (user_id),
  KEY idx_password_resets_expires (expires_at),
  CONSTRAINT fk_pr_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `api_tokens`
```sql
CREATE TABLE api_tokens (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL,
  name          VARCHAR(100) NOT NULL COMMENT 'User-defined label for this token',
  token_hash    VARCHAR(255) NOT NULL,
  scopes        VARCHAR(500) NULL COMMENT 'Comma-separated permission names',
  expires_at    TIMESTAMP NULL,
  last_used_at  TIMESTAMP NULL,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted    TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at    TIMESTAMP NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_api_tokens_hash (token_hash),
  KEY idx_api_tokens_user (user_id),
  KEY idx_api_tokens_active (is_active),
  CONSTRAINT fk_at_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `login_history`
```sql
CREATE TABLE login_history (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NULL COMMENT 'NULL for failed login attempts',
  email         VARCHAR(255) NOT NULL,
  ip_address    VARCHAR(45) NULL,
  user_agent    VARCHAR(500) NULL,
  success       TINYINT(1) NOT NULL DEFAULT 0,
  failure_reason VARCHAR(200) NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_login_history_user (user_id),
  KEY idx_login_history_email (email),
  KEY idx_login_history_created (created_at),
  KEY idx_login_history_ip (ip_address),
  CONSTRAINT fk_lh_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `activity_logs`
```sql
CREATE TABLE activity_logs (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NULL,
  action        VARCHAR(100) NOT NULL COMMENT 'e.g. login, view_dashboard, trigger_pipeline',
  resource_type VARCHAR(50) NULL,
  resource_id   BIGINT UNSIGNED NULL,
  ip_address    VARCHAR(45) NULL,
  user_agent    VARCHAR(500) NULL,
  metadata      JSON NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_activity_logs_user (user_id),
  KEY idx_activity_logs_action (action),
  KEY idx_activity_logs_resource (resource_type, resource_id),
  KEY idx_activity_logs_created (created_at),
  CONSTRAINT fk_al_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 6. Organization Domain

### `organizations`
```sql
CREATE TABLE organizations (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(255) NOT NULL,
  slug          VARCHAR(100) NOT NULL,
  description   TEXT NULL,
  logo_url      VARCHAR(500) NULL,
  contact_email VARCHAR(255) NULL,
  contact_phone VARCHAR(50) NULL,
  address       TEXT NULL,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted    TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at    TIMESTAMP NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_organizations_slug (slug),
  KEY idx_organizations_active (is_active),
  KEY idx_organizations_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `branches`
```sql
CREATE TABLE branches (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NOT NULL,
  name            VARCHAR(255) NOT NULL,
  code            VARCHAR(50) NULL,
  address         TEXT NULL,
  contact_email   VARCHAR(255) NULL,
  contact_phone   VARCHAR(50) NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_branches_organization (organization_id),
  KEY idx_branches_active (is_active),
  CONSTRAINT fk_branches_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `departments`
```sql
CREATE TABLE departments (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NOT NULL,
  branch_id       BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  code            VARCHAR(50) NULL,
  description     TEXT NULL,
  head_user_id    BIGINT UNSIGNED NULL COMMENT 'Department head',
  parent_id       BIGINT UNSIGNED NULL COMMENT 'Parent department for hierarchy',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_departments_organization (organization_id),
  KEY idx_departments_branch (branch_id),
  KEY idx_departments_parent (parent_id),
  KEY idx_departments_head (head_user_id),
  CONSTRAINT fk_dept_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE CASCADE,
  CONSTRAINT fk_dept_branch FOREIGN KEY (branch_id)
    REFERENCES branches (id) ON DELETE SET NULL,
  CONSTRAINT fk_dept_parent FOREIGN KEY (parent_id)
    REFERENCES departments (id) ON DELETE SET NULL,
  CONSTRAINT fk_dept_head FOREIGN KEY (head_user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `teams`
```sql
CREATE TABLE teams (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  department_id   BIGINT UNSIGNED NOT NULL,
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  lead_user_id    BIGINT UNSIGNED NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_teams_department (department_id),
  KEY idx_teams_lead (lead_user_id),
  CONSTRAINT fk_teams_dept FOREIGN KEY (department_id)
    REFERENCES departments (id) ON DELETE CASCADE,
  CONSTRAINT fk_teams_lead FOREIGN KEY (lead_user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `organization_settings`
```sql
CREATE TABLE organization_settings (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NOT NULL,
  setting_key     VARCHAR(100) NOT NULL,
  setting_value    TEXT NULL,
  data_type       VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT 'string|int|float|boolean|json',
  description     VARCHAR(500) NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_org_settings (organization_id, setting_key),
  KEY idx_org_settings_key (setting_key),
  CONSTRAINT fk_os_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 7. ETL Domain

### `data_sources`
```sql
CREATE TABLE data_sources (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  source_type     VARCHAR(50) NOT NULL COMMENT 'csv|excel|api|database|ftp|json',
  connection_config JSON NULL COMMENT 'Encrypted connection parameters',
  file_path       VARCHAR(1000) NULL,
  api_endpoint    VARCHAR(1000) NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_data_sources_org (organization_id),
  KEY idx_data_sources_type (source_type),
  KEY idx_data_sources_active (is_active),
  CONSTRAINT fk_ds_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `connectors`
```sql
CREATE TABLE connectors (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  data_source_id  BIGINT UNSIGNED NOT NULL,
  name            VARCHAR(255) NOT NULL,
  connector_type  VARCHAR(50) NOT NULL COMMENT 'file_reader|api_client|db_reader|ftp_client',
  config          JSON NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_connectors_source (data_source_id),
  CONSTRAINT fk_conn_source FOREIGN KEY (data_source_id)
    REFERENCES data_sources (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `etl_jobs`
```sql
CREATE TABLE etl_jobs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  data_source_id  BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  job_type        VARCHAR(50) NOT NULL DEFAULT 'full_load' COMMENT 'full_load|incremental|upsert',
  status          VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft|active|paused|archived',
  config          JSON NULL COMMENT 'Job configuration (batch_size, retry_count, etc.)',
  created_by      BIGINT UNSIGNED NULL,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_etl_jobs_org (organization_id),
  KEY idx_etl_jobs_source (data_source_id),
  KEY idx_etl_jobs_status (status),
  KEY idx_etl_jobs_created_by (created_by),
  CONSTRAINT fk_ej_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_ej_source FOREIGN KEY (data_source_id)
    REFERENCES data_sources (id) ON DELETE SET NULL,
  CONSTRAINT fk_ej_created_by FOREIGN KEY (created_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `etl_logs`
```sql
CREATE TABLE etl_logs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NULL,
  pipeline_run_id VARCHAR(50) NULL COMMENT 'FK to pipeline_runs.run_id',
  log_level       VARCHAR(20) NOT NULL DEFAULT 'INFO' COMMENT 'DEBUG|INFO|WARNING|ERROR',
  message         TEXT NOT NULL,
  step_name       VARCHAR(100) NULL COMMENT 'extract|transform|load',
  row_count       INT NULL,
  duration_ms     INT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_etl_logs_job (etl_job_id),
  KEY idx_etl_logs_run (pipeline_run_id),
  KEY idx_etl_logs_level (log_level),
  KEY idx_etl_logs_created (created_at),
  CONSTRAINT fk_el_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `etl_schedules`
```sql
CREATE TABLE etl_schedules (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NOT NULL,
  cron_expression VARCHAR(100) NOT NULL COMMENT 'e.g. 0 8 * * * for daily at 08:00',
  timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  last_run_at     TIMESTAMP NULL,
  next_run_at     TIMESTAMP NULL,
  created_by      BIGINT UNSIGNED NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_etl_schedules_job (etl_job_id),
  KEY idx_etl_schedules_active (is_active),
  KEY idx_etl_schedules_next_run (next_run_at),
  CONSTRAINT fk_es_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE CASCADE,
  CONSTRAINT fk_es_created_by FOREIGN KEY (created_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `transformations`
```sql
CREATE TABLE transformations (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NOT NULL,
  name            VARCHAR(255) NOT NULL,
  step_order      INT NOT NULL DEFAULT 0,
  transform_type  VARCHAR(50) NOT NULL COMMENT 'rename|drop|cast|deduplicate|validate|custom',
  config          JSON NULL COMMENT 'Transformation parameters',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_transformations_job (etl_job_id),
  KEY idx_transformations_order (step_order),
  CONSTRAINT fk_tr_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `validation_rules`
```sql
CREATE TABLE validation_rules (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NOT NULL,
  column_name     VARCHAR(100) NOT NULL,
  rule_type       VARCHAR(50) NOT NULL COMMENT 'not_null|min_value|max_value|regex|range|unique',
  rule_config     JSON NULL,
  severity        VARCHAR(20) NOT NULL DEFAULT 'warning' COMMENT 'warning|error',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_validation_rules_job (etl_job_id),
  KEY idx_validation_rules_column (column_name),
  CONSTRAINT fk_vr_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `pipeline_steps`
```sql
CREATE TABLE pipeline_steps (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  pipeline_run_id VARCHAR(50) NOT NULL COMMENT 'FK to pipeline_runs.run_id',
  step_name       VARCHAR(100) NOT NULL COMMENT 'extract|transform|load|validate',
  step_order      INT NOT NULL,
  status          VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending|running|completed|failed',
  started_at      TIMESTAMP NULL,
  completed_at    TIMESTAMP NULL,
  duration_ms     INT NULL,
  rows_processed  INT NULL,
  error_message   TEXT NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_pipeline_steps_run (pipeline_run_id),
  KEY idx_pipeline_steps_status (status),
  KEY idx_pipeline_steps_order (step_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `pipeline_history`
```sql
CREATE TABLE pipeline_history (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NULL,
  pipeline_run_id VARCHAR(50) NOT NULL,
  previous_status VARCHAR(20) NULL,
  new_status      VARCHAR(20) NOT NULL,
  changed_by      VARCHAR(50) NULL COMMENT 'user_id or system',
  change_reason   VARCHAR(500) NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_pipeline_history_job (etl_job_id),
  KEY idx_pipeline_history_run (pipeline_run_id),
  KEY idx_pipeline_history_created (created_at),
  CONSTRAINT fk_ph_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `job_status`
```sql
CREATE TABLE job_status (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  etl_job_id      BIGINT UNSIGNED NOT NULL,
  pipeline_run_id VARCHAR(50) NULL,
  status          VARCHAR(20) NOT NULL COMMENT 'queued|running|completed|failed|skipped',
  started_at      TIMESTAMP NULL,
  completed_at    TIMESTAMP NULL,
  duration_seconds INT NULL,
  rows_extracted  INT DEFAULT 0,
  rows_transformed INT DEFAULT 0,
  rows_loaded     INT DEFAULT 0,
  duplicates_removed INT DEFAULT 0,
  error_message   TEXT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_job_status_job (etl_job_id),
  KEY idx_job_status_run (pipeline_run_id),
  KEY idx_job_status_status (status),
  CONSTRAINT fk_js_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 8. Dataset Domain

### `datasets`
```sql
CREATE TABLE datasets (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  etl_job_id      BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  source_table    VARCHAR(100) NULL COMMENT 'e.g. sales',
  row_count       BIGINT NULL,
  column_count    INT NULL,
  size_bytes      BIGINT NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_datasets_org (organization_id),
  KEY idx_datasets_job (etl_job_id),
  KEY idx_datasets_active (is_active),
  CONSTRAINT fk_ds_dataset_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_ds_dataset_job FOREIGN KEY (etl_job_id)
    REFERENCES etl_jobs (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dataset_versions`
```sql
CREATE TABLE dataset_versions (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id      BIGINT UNSIGNED NOT NULL,
  version_number  INT NOT NULL,
  version_label   VARCHAR(100) NULL,
  row_count       BIGINT NULL,
  checksum        VARCHAR(64) NULL COMMENT 'SHA-256 of dataset content',
  created_by      BIGINT UNSIGNED NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dataset_versions (dataset_id, version_number),
  KEY idx_dataset_versions_dataset (dataset_id),
  CONSTRAINT fk_dv_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets (id) ON DELETE CASCADE,
  CONSTRAINT fk_dv_created_by FOREIGN KEY (created_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dataset_columns`
```sql
CREATE TABLE dataset_columns (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id      BIGINT UNSIGNED NOT NULL,
  column_name     VARCHAR(100) NOT NULL,
  display_name    VARCHAR(200) NULL,
  data_type       VARCHAR(50) NOT NULL COMMENT 'string|integer|float|date|boolean|json',
  is_nullable     TINYINT(1) NOT NULL DEFAULT 1,
  is_unique       TINYINT(1) NOT NULL DEFAULT 0,
  is_primary_key  TINYINT(1) NOT NULL DEFAULT 0,
  min_value       VARCHAR(100) NULL,
  max_value       VARCHAR(100) NULL,
  null_count      BIGINT NULL,
  unique_count    BIGINT NULL,
  sample_values   JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dataset_columns_dataset (dataset_id),
  KEY idx_dataset_columns_name (column_name),
  CONSTRAINT fk_dc_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dataset_tags`
```sql
CREATE TABLE dataset_tags (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id      BIGINT UNSIGNED NOT NULL,
  tag             VARCHAR(100) NOT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dataset_tags (dataset_id, tag),
  KEY idx_dataset_tags_tag (tag),
  CONSTRAINT fk_dt_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dataset_metadata`
```sql
CREATE TABLE dataset_metadata (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id      BIGINT UNSIGNED NOT NULL,
  meta_key        VARCHAR(100) NOT NULL,
  meta_value      TEXT NULL,
  data_type       VARCHAR(20) NOT NULL DEFAULT 'string',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dataset_metadata (dataset_id, meta_key),
  KEY idx_dataset_metadata_key (meta_key),
  CONSTRAINT fk_dm_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dataset_access`
```sql
CREATE TABLE dataset_access (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dataset_id      BIGINT UNSIGNED NOT NULL,
  user_id         BIGINT UNSIGNED NULL,
  role_id         BIGINT UNSIGNED NULL,
  access_level    VARCHAR(20) NOT NULL DEFAULT 'read' COMMENT 'read|write|admin',
  granted_by      BIGINT UNSIGNED NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_dataset_access_dataset (dataset_id),
  KEY idx_dataset_access_user (user_id),
  KEY idx_dataset_access_role (role_id),
  CONSTRAINT fk_da_dataset FOREIGN KEY (dataset_id)
    REFERENCES datasets (id) ON DELETE CASCADE,
  CONSTRAINT fk_da_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_da_role FOREIGN KEY (role_id)
    REFERENCES roles (id) ON DELETE CASCADE,
  CONSTRAINT fk_da_granted_by FOREIGN KEY (granted_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 9. Analytics Domain

### `dashboards`
```sql
CREATE TABLE dashboards (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  user_id         BIGINT UNSIGNED NULL COMMENT 'Dashboard owner',
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  layout_config   JSON NULL COMMENT 'Grid layout of widgets',
  is_default      TINYINT(1) NOT NULL DEFAULT 0,
  is_shared       TINYINT(1) NOT NULL DEFAULT 0,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dashboards_org (organization_id),
  KEY idx_dashboards_user (user_id),
  KEY idx_dashboards_shared (is_shared),
  CONSTRAINT fk_dash_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_dash_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dashboard_widgets`
```sql
CREATE TABLE dashboard_widgets (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  dashboard_id    BIGINT UNSIGNED NOT NULL,
  widget_type     VARCHAR(50) NOT NULL COMMENT 'kpi_card|chart|table|map|filter',
  title           VARCHAR(255) NOT NULL,
  data_source     VARCHAR(100) NULL COMMENT 'Which API endpoint feeds this widget',
  query_config    JSON NULL COMMENT 'Filters, group_by, aggregations',
  display_config  JSON NULL COMMENT 'Colors, sizes, chart options',
  position_x      INT NOT NULL DEFAULT 0,
  position_y      INT NOT NULL DEFAULT 0,
  width           INT NOT NULL DEFAULT 1,
  height          INT NOT NULL DEFAULT 1,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_widgets_dashboard (dashboard_id),
  KEY idx_widgets_type (widget_type),
  CONSTRAINT fk_dw_dashboard FOREIGN KEY (dashboard_id)
    REFERENCES dashboards (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `charts`
```sql
CREATE TABLE charts (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  chart_type      VARCHAR(50) NOT NULL COMMENT 'area|bar|pie|scatter|heatmap|line|donut',
  data_config     JSON NULL COMMENT 'x_axis, y_axis, group_by, filters',
  display_config  JSON NULL COMMENT 'colors, labels, legend, animation',
  is_shared       TINYINT(1) NOT NULL DEFAULT 0,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_charts_org (organization_id),
  KEY idx_charts_type (chart_type),
  CONSTRAINT fk_charts_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `chart_settings`
```sql
CREATE TABLE chart_settings (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  chart_id        BIGINT UNSIGNED NOT NULL,
  setting_key     VARCHAR(100) NOT NULL,
  setting_value   TEXT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_chart_settings (chart_id, setting_key),
  KEY idx_chart_settings_key (setting_key),
  CONSTRAINT fk_cs_chart FOREIGN KEY (chart_id)
    REFERENCES charts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `saved_filters`
```sql
CREATE TABLE saved_filters (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  name            VARCHAR(255) NOT NULL,
  filter_config   JSON NOT NULL COMMENT 'region, category, date_range, etc.',
  is_shared       TINYINT(1) NOT NULL DEFAULT 0,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_saved_filters_user (user_id),
  KEY idx_saved_filters_shared (is_shared),
  CONSTRAINT fk_sf_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `kpis`
```sql
CREATE TABLE kpis (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  display_name    VARCHAR(255) NOT NULL,
  kpi_type        VARCHAR(50) NOT NULL COMMENT 'sum|avg|count|distinct_count|ratio',
  target_value    DECIMAL(20,4) NULL,
  query_config    JSON NULL COMMENT 'SQL or aggregation config',
  unit            VARCHAR(20) NULL COMMENT '$, %, count',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_kpis_org (organization_id),
  KEY idx_kpis_active (is_active),
  CONSTRAINT fk_kpis_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `analytics_history`
```sql
CREATE TABLE analytics_history (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  kpi_id          BIGINT UNSIGNED NULL,
  user_id         BIGINT UNSIGNED NULL,
  period_start    DATE NOT NULL,
  period_end      DATE NOT NULL,
  value           DECIMAL(20,4) NOT NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_analytics_history_kpi (kpi_id),
  KEY idx_analytics_history_user (user_id),
  KEY idx_analytics_history_period (period_start, period_end),
  CONSTRAINT fk_ah_kpi FOREIGN KEY (kpi_id)
    REFERENCES kpis (id) ON DELETE SET NULL,
  CONSTRAINT fk_ah_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 10. Reporting Domain

### `reports`
```sql
CREATE TABLE reports (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  user_id         BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  report_type     VARCHAR(50) NOT NULL COMMENT 'sales_summary|profit_analysis|custom',
  parameters      JSON NULL COMMENT 'Filters, date range, group_by',
  status          VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft|active|archived',
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_reports_org (organization_id),
  KEY idx_reports_user (user_id),
  KEY idx_reports_status (status),
  CONSTRAINT fk_reports_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_reports_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `report_templates`
```sql
CREATE TABLE report_templates (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(255) NOT NULL,
  description     TEXT NULL,
  template_type   VARCHAR(50) NOT NULL COMMENT 'pdf|excel|csv|html',
  template_config JSON NULL COMMENT 'Layout, sections, styling',
  is_system       TINYINT(1) NOT NULL DEFAULT 0,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_report_templates_type (template_type),
  KEY idx_report_templates_system (is_system)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `generated_reports`
```sql
CREATE TABLE generated_reports (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  report_id       BIGINT UNSIGNED NOT NULL,
  template_id     BIGINT UNSIGNED NULL,
  file_path       VARCHAR(1000) NOT NULL,
  file_format     VARCHAR(20) NOT NULL COMMENT 'pdf|xlsx|csv',
  file_size_bytes BIGINT NULL,
  parameters_used JSON NULL,
  generated_by    BIGINT UNSIGNED NULL,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_generated_reports_report (report_id),
  KEY idx_generated_reports_template (template_id),
  KEY idx_generated_reports_user (generated_by),
  CONSTRAINT fk_gr_report FOREIGN KEY (report_id)
    REFERENCES reports (id) ON DELETE CASCADE,
  CONSTRAINT fk_gr_template FOREIGN KEY (template_id)
    REFERENCES report_templates (id) ON DELETE SET NULL,
  CONSTRAINT fk_gr_user FOREIGN KEY (generated_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `scheduled_reports`
```sql
CREATE TABLE scheduled_reports (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  report_id       BIGINT UNSIGNED NOT NULL,
  template_id     BIGINT UNSIGNED NULL,
  cron_expression VARCHAR(100) NOT NULL,
  timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',
  recipients      JSON NULL COMMENT 'List of user IDs or emails',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  last_run_at     TIMESTAMP NULL,
  next_run_at     TIMESTAMP NULL,
  created_by      BIGINT UNSIGNED NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_scheduled_reports_report (report_id),
  KEY idx_scheduled_reports_active (is_active),
  KEY idx_scheduled_reports_next_run (next_run_at),
  CONSTRAINT fk_sr_report FOREIGN KEY (report_id)
    REFERENCES reports (id) ON DELETE CASCADE,
  CONSTRAINT fk_sr_template FOREIGN KEY (template_id)
    REFERENCES report_templates (id) ON DELETE SET NULL,
  CONSTRAINT fk_sr_created_by FOREIGN KEY (created_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `exports`
```sql
CREATE TABLE exports (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  export_type     VARCHAR(50) NOT NULL COMMENT 'csv|xlsx|json|pdf',
  source_type     VARCHAR(50) NOT NULL COMMENT 'sales|report|dashboard|query_result',
  source_id       BIGINT UNSIGNED NULL,
  file_path       VARCHAR(1000) NOT NULL,
  file_size_bytes BIGINT NULL,
  row_count       INT NULL,
  filters_used    JSON NULL,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_exports_user (user_id),
  KEY idx_exports_type (export_type),
  KEY idx_exports_source (source_type, source_id),
  CONSTRAINT fk_exports_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 11. AI Domain

### `ai_requests`
```sql
CREATE TABLE ai_requests (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NULL,
  organization_id BIGINT UNSIGNED NULL,
  request_type    VARCHAR(50) NOT NULL COMMENT 'forecast|anomaly_detection|insight|recommendation',
  input_data      JSON NULL,
  model_name      VARCHAR(100) NULL,
  status          VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending|processing|completed|failed',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_ai_requests_user (user_id),
  KEY idx_ai_requests_org (organization_id),
  KEY idx_ai_requests_type (request_type),
  KEY idx_ai_requests_status (status),
  CONSTRAINT fk_ar_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT fk_ar_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `ai_responses`
```sql
CREATE TABLE ai_responses (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ai_request_id   BIGINT UNSIGNED NOT NULL,
  output_data     JSON NULL,
  confidence_score DECIMAL(5,4) NULL,
  model_version   VARCHAR(50) NULL,
  processing_time_ms INT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_ai_responses_request (ai_request_id),
  CONSTRAINT fk_aresp_request FOREIGN KEY (ai_request_id)
    REFERENCES ai_requests (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `predictions`
```sql
CREATE TABLE predictions (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  prediction_type VARCHAR(50) NOT NULL COMMENT 'sales_forecast|profit_forecast|demand_forecast',
  target_date     DATE NOT NULL,
  predicted_value DECIMAL(20,4) NOT NULL,
  lower_bound     DECIMAL(20,4) NULL,
  upper_bound     DECIMAL(20,4) NULL,
  confidence      DECIMAL(5,4) NULL,
  model_name      VARCHAR(100) NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_predictions_org (organization_id),
  KEY idx_predictions_type (prediction_type),
  KEY idx_predictions_date (target_date),
  CONSTRAINT fk_pred_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `insights`
```sql
CREATE TABLE insights (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  insight_type    VARCHAR(50) NOT NULL COMMENT 'trend|anomaly|opportunity|risk',
  title           VARCHAR(255) NOT NULL,
  description     TEXT NOT NULL,
  severity        VARCHAR(20) NOT NULL DEFAULT 'info' COMMENT 'info|warning|critical',
  metadata        JSON NULL,
  is_acknowledged TINYINT(1) NOT NULL DEFAULT 0,
  acknowledged_by BIGINT UNSIGNED NULL,
  acknowledged_at TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_insights_org (organization_id),
  KEY idx_insights_type (insight_type),
  KEY idx_insights_severity (severity),
  CONSTRAINT fk_insights_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_insights_ack_by FOREIGN KEY (acknowledged_by)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `recommendations`
```sql
CREATE TABLE recommendations (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  insight_id      BIGINT UNSIGNED NULL,
  title           VARCHAR(255) NOT NULL,
  description     TEXT NOT NULL,
  action_config   JSON NULL COMMENT 'Suggested action parameters',
  priority        VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT 'low|medium|high',
  status          VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending|accepted|rejected|implemented',
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_recommendations_org (organization_id),
  KEY idx_recommendations_insight (insight_id),
  KEY idx_recommendations_priority (priority),
  KEY idx_recommendations_status (status),
  CONSTRAINT fk_rec_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL,
  CONSTRAINT fk_rec_insight FOREIGN KEY (insight_id)
    REFERENCES insights (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `forecast_models`
```sql
CREATE TABLE forecast_models (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NULL,
  name            VARCHAR(255) NOT NULL,
  model_type      VARCHAR(50) NOT NULL COMMENT 'arima|prophet|lstm|linear_regression',
  target_metric   VARCHAR(100) NOT NULL COMMENT 'sales|profit|quantity',
  training_config JSON NULL,
  model_params    JSON NULL COMMENT 'Learned parameters',
  accuracy_score  DECIMAL(5,4) NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  trained_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_forecast_models_org (organization_id),
  KEY idx_forecast_models_type (model_type),
  KEY idx_forecast_models_active (is_active),
  CONSTRAINT fk_fm_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 12. Notification Domain

### `notifications`
```sql
CREATE TABLE notifications (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  organization_id BIGINT UNSIGNED NULL,
  notification_type VARCHAR(50) NOT NULL COMMENT 'etl_complete|etl_failed|report_ready|system|alert',
  title           VARCHAR(255) NOT NULL,
  message         TEXT NOT NULL,
  metadata        JSON NULL,
  is_read         TINYINT(1) NOT NULL DEFAULT 0,
  read_at         TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_notifications_user (user_id),
  KEY idx_notifications_org (organization_id),
  KEY idx_notifications_type (notification_type),
  KEY idx_notifications_unread (is_read),
  KEY idx_notifications_created (created_at),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_notif_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `notification_templates`
```sql
CREATE TABLE notification_templates (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  notification_type VARCHAR(50) NOT NULL,
  subject_template VARCHAR(500) NOT NULL,
  body_template   TEXT NOT NULL,
  channel         VARCHAR(20) NOT NULL DEFAULT 'in_app' COMMENT 'in_app|email|sms',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_notif_templates (name, channel),
  KEY idx_notif_templates_type (notification_type),
  KEY idx_notif_templates_channel (channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `notification_preferences`
```sql
CREATE TABLE notification_preferences (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  notification_type VARCHAR(50) NOT NULL,
  in_app_enabled  TINYINT(1) NOT NULL DEFAULT 1,
  email_enabled   TINYINT(1) NOT NULL DEFAULT 0,
  sms_enabled     TINYINT(1) NOT NULL DEFAULT 0,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_notif_prefs (user_id, notification_type),
  KEY idx_notif_prefs_user (user_id),
  CONSTRAINT fk_np_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `email_queue`
```sql
CREATE TABLE email_queue (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  notification_id BIGINT UNSIGNED NULL,
  to_email        VARCHAR(255) NOT NULL,
  from_email      VARCHAR(255) NOT NULL DEFAULT 'noreply@dataflow.com',
  subject         VARCHAR(500) NOT NULL,
  body_html       TEXT NULL,
  body_text       TEXT NULL,
  status          VARCHAR(20) NOT NULL DEFAULT 'queued' COMMENT 'queued|sending|sent|failed',
  attempts        INT NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMP NULL,
  sent_at         TIMESTAMP NULL,
  error_message   TEXT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_email_queue_status (status),
  KEY idx_email_queue_notification (notification_id),
  KEY idx_email_queue_created (created_at),
  CONSTRAINT fk_eq_notification FOREIGN KEY (notification_id)
    REFERENCES notifications (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `sms_queue`
```sql
CREATE TABLE sms_queue (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  notification_id BIGINT UNSIGNED NULL,
  to_phone        VARCHAR(50) NOT NULL,
  message         VARCHAR(500) NOT NULL,
  status          VARCHAR(20) NOT NULL DEFAULT 'queued' COMMENT 'queued|sending|sent|failed',
  attempts        INT NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMP NULL,
  sent_at         TIMESTAMP NULL,
  error_message   TEXT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_sms_queue_status (status),
  KEY idx_sms_queue_notification (notification_id),
  CONSTRAINT fk_sq_notification FOREIGN KEY (notification_id)
    REFERENCES notifications (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 13. Audit Domain

### `audit_logs`
```sql
CREATE TABLE audit_logs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NULL,
  organization_id BIGINT UNSIGNED NULL,
  action          VARCHAR(100) NOT NULL COMMENT 'create|update|delete|login|logout|export|trigger',
  resource_type   VARCHAR(50) NOT NULL COMMENT 'user|report|etl_job|dataset|setting',
  resource_id     BIGINT UNSIGNED NULL,
  old_values      JSON NULL,
  new_values      JSON NULL,
  ip_address      VARCHAR(45) NULL,
  user_agent      VARCHAR(500) NULL,
  request_id      VARCHAR(100) NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_audit_logs_user (user_id),
  KEY idx_audit_logs_org (organization_id),
  KEY idx_audit_logs_action (action),
  KEY idx_audit_logs_resource (resource_type, resource_id),
  KEY idx_audit_logs_created (created_at),
  CONSTRAINT fk_al_audit_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT fk_al_audit_org FOREIGN KEY (organization_id)
    REFERENCES organizations (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `system_logs`
```sql
CREATE TABLE system_logs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  log_level       VARCHAR(20) NOT NULL COMMENT 'DEBUG|INFO|WARNING|ERROR|CRITICAL',
  logger_name     VARCHAR(200) NULL,
  message         TEXT NOT NULL,
  module          VARCHAR(200) NULL,
  function        VARCHAR(200) NULL,
  line_number     INT NULL,
  stack_trace     TEXT NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_system_logs_level (log_level),
  KEY idx_system_logs_module (module),
  KEY idx_system_logs_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `security_logs`
```sql
CREATE TABLE security_logs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NULL,
  event_type      VARCHAR(50) NOT NULL COMMENT 'login_success|login_failed|token_refresh|permission_denied|password_change|token_revoked',
  ip_address      VARCHAR(45) NULL,
  user_agent      VARCHAR(500) NULL,
  resource        VARCHAR(200) NULL,
  details         JSON NULL,
  severity        VARCHAR(20) NOT NULL DEFAULT 'info' COMMENT 'info|warning|critical',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_security_logs_user (user_id),
  KEY idx_security_logs_event (event_type),
  KEY idx_security_logs_severity (severity),
  KEY idx_security_logs_created (created_at),
  CONSTRAINT fk_sl_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `user_activity`
```sql
CREATE TABLE user_activity (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  activity_type   VARCHAR(50) NOT NULL COMMENT 'page_view|click|search|export|filter_apply',
  resource_type   VARCHAR(50) NULL,
  resource_id     BIGINT UNSIGNED NULL,
  session_id      VARCHAR(100) NULL,
  ip_address      VARCHAR(45) NULL,
  metadata        JSON NULL,
  duration_seconds INT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_activity_user (user_id),
  KEY idx_user_activity_type (activity_type),
  KEY idx_user_activity_resource (resource_type, resource_id),
  KEY idx_user_activity_created (created_at),
  CONSTRAINT fk_ua_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 14. Settings Domain

### `system_settings`
```sql
CREATE TABLE system_settings (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  setting_key     VARCHAR(100) NOT NULL,
  setting_value   TEXT NULL,
  data_type       VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT 'string|int|float|boolean|json',
  category        VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT 'general|etl|api|dashboard|security',
  description     VARCHAR(500) NULL,
  is_public       TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Visible to non-admin users',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_system_settings (setting_key),
  KEY idx_system_settings_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `user_preferences`
```sql
CREATE TABLE user_preferences (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  preference_key  VARCHAR(100) NOT NULL,
  preference_value TEXT NULL,
  data_type       VARCHAR(20) NOT NULL DEFAULT 'string',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_user_preferences (user_id, preference_key),
  KEY idx_user_preferences_key (preference_key),
  CONSTRAINT fk_up_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `feature_flags`
```sql
CREATE TABLE feature_flags (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  description     VARCHAR(500) NULL,
  is_enabled      TINYINT(1) NOT NULL DEFAULT 0,
  rollout_percentage TINYINT NOT NULL DEFAULT 0 COMMENT '0-100, 0=off, 100=full rollout',
  target_users    JSON NULL COMMENT 'List of user IDs for targeted rollout',
  target_organizations JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_feature_flags (name),
  KEY idx_feature_flags_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 15. Department Domain

### `department_types`
```sql
CREATE TABLE department_types (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(100) NOT NULL COMMENT 'Health|Education|Agriculture|Finance|Transport|Environment|Energy|Statistics|NGOs|Research',
  code            VARCHAR(20) NOT NULL,
  description     TEXT NULL,
  icon            VARCHAR(100) NULL,
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  is_deleted      TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at      TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_department_types_code (code),
  KEY idx_department_types_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `department_configs`
```sql
CREATE TABLE department_configs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  department_id   BIGINT UNSIGNED NOT NULL,
  department_type_id BIGINT UNSIGNED NOT NULL,
  config_key      VARCHAR(100) NOT NULL,
  config_value    TEXT NULL,
  data_type       VARCHAR(20) NOT NULL DEFAULT 'string',
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dept_configs (department_id, config_key),
  KEY idx_dept_configs_type (department_type_id),
  CONSTRAINT fk_dc_dept FOREIGN KEY (department_id)
    REFERENCES departments (id) ON DELETE CASCADE,
  CONSTRAINT fk_dc_type FOREIGN KEY (department_type_id)
    REFERENCES department_types (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `department_metrics`
```sql
CREATE TABLE department_metrics (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  department_id   BIGINT UNSIGNED NOT NULL,
  metric_name     VARCHAR(100) NOT NULL,
  metric_value    DECIMAL(20,4) NOT NULL,
  metric_unit     VARCHAR(20) NULL,
  period_start    DATE NOT NULL,
  period_end      DATE NOT NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_dept_metrics_dept (department_id),
  KEY idx_dept_metrics_name (metric_name),
  KEY idx_dept_metrics_period (period_start, period_end),
  CONSTRAINT fk_dm_dept FOREIGN KEY (department_id)
    REFERENCES departments (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Extensibility Pattern

New departments (Health, Education, Agriculture, etc.) extend the platform through `department_configs` and `department_metrics` — **no core schema changes needed**. Each department type defines its own config keys and metrics via application code, not database changes.

---

## 16. Data Warehouse Domain

### `fact_sales`
```sql
CREATE TABLE fact_sales (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  sales_id        INT NOT NULL COMMENT 'FK to sales.id (operational)',
  order_date_key  INT NOT NULL COMMENT 'FK to dim_date.id',
  customer_key    BIGINT UNSIGNED NULL COMMENT 'FK to dim_customer.id',
  product_key     BIGINT UNSIGNED NULL COMMENT 'FK to dim_product.id',
  region_key      BIGINT UNSIGNED NULL COMMENT 'FK to dim_region.id',
  category_key    BIGINT UNSIGNED NULL COMMENT 'FK to dim_category.id',
  organization_id BIGINT UNSIGNED NULL,
  sales_amount    DECIMAL(15,4) NOT NULL,
  quantity        INT NOT NULL,
  discount_amount DECIMAL(15,4) NOT NULL DEFAULT 0,
  profit_amount   DECIMAL(15,4) NOT NULL DEFAULT 0,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_fact_sales_date (order_date_key),
  KEY idx_fact_sales_customer (customer_key),
  KEY idx_fact_sales_product (product_key),
  KEY idx_fact_sales_region (region_key),
  KEY idx_fact_sales_category (category_key),
  KEY idx_fact_sales_org (organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dim_date`
```sql
CREATE TABLE dim_date (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'YYYYMMDD format',
  full_date       DATE NOT NULL,
  day             TINYINT NOT NULL,
  day_name        VARCHAR(20) NOT NULL,
  day_of_week     TINYINT NOT NULL,
  day_of_year     SMALLINT NOT NULL,
  week            TINYINT NOT NULL,
  week_name       VARCHAR(20) NOT NULL,
  month           TINYINT NOT NULL,
  month_name      VARCHAR(20) NOT NULL,
  quarter         TINYINT NOT NULL,
  year            SMALLINT NOT NULL,
  is_weekend      TINYINT(1) NOT NULL DEFAULT 0,
  is_holiday      TINYINT(1) NOT NULL DEFAULT 0,
  UNIQUE KEY uq_dim_date (full_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dim_customer`
```sql
CREATE TABLE dim_customer (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  customer_name   VARCHAR(255) NOT NULL,
  segment         VARCHAR(100) NULL,
  organization_id BIGINT UNSIGNED NULL,
  is_current      TINYINT(1) NOT NULL DEFAULT 1,
  valid_from      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  valid_to        TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dim_customer_name (customer_name),
  KEY idx_dim_customer_segment (segment),
  KEY idx_dim_customer_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dim_product`
```sql
CREATE TABLE dim_product (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_name    VARCHAR(500) NOT NULL,
  category        VARCHAR(100) NULL,
  sub_category    VARCHAR(100) NULL,
  is_current      TINYINT(1) NOT NULL DEFAULT 1,
  valid_from      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  valid_to        TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dim_product_name (product_name),
  KEY idx_dim_product_category (category),
  KEY idx_dim_product_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dim_region`
```sql
CREATE TABLE dim_region (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  region_name     VARCHAR(100) NOT NULL,
  country         VARCHAR(100) NULL DEFAULT 'United States',
  is_current      TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dim_region (region_name, country),
  KEY idx_dim_region_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `dim_category`
```sql
CREATE TABLE dim_category (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  category_name   VARCHAR(100) NOT NULL,
  sub_category    VARCHAR(100) NULL,
  is_current      TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_dim_category (category_name, sub_category),
  KEY idx_dim_category_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `agg_sales_monthly`
```sql
CREATE TABLE agg_sales_monthly (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  year            SMALLINT NOT NULL,
  month           TINYINT NOT NULL,
  region          VARCHAR(100) NULL,
  category        VARCHAR(100) NULL,
  total_sales     DECIMAL(15,4) NOT NULL DEFAULT 0,
  total_profit    DECIMAL(15,4) NOT NULL DEFAULT 0,
  total_quantity  INT NOT NULL DEFAULT 0,
  order_count     INT NOT NULL DEFAULT 0,
  avg_order_value DECIMAL(15,4) NULL,
  organization_id BIGINT UNSIGNED NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_agg_sales_monthly (year, month, region, category),
  KEY idx_agg_monthly_year (year),
  KEY idx_agg_monthly_region (region),
  KEY idx_agg_monthly_category (category),
  KEY idx_agg_monthly_org (organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### `data_snapshots`
```sql
CREATE TABLE data_snapshots (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  snapshot_type   VARCHAR(50) NOT NULL COMMENT 'daily|weekly|monthly|custom',
  source_table    VARCHAR(100) NOT NULL,
  snapshot_date   DATE NOT NULL,
  row_count       BIGINT NOT NULL,
  checksum        VARCHAR(64) NULL,
  metadata        JSON NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_snapshots_type (snapshot_type),
  KEY idx_snapshots_source (source_table),
  KEY idx_snapshots_date (snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 17. Entity Relationship Diagram (ERD)

### High-Level Domain Relationships

```
                    ┌──────────────┐
                    │ organizations │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐   ┌────────────┐   ┌────────────┐
    │ branches │   │ departments│   │   users     │
    └────┬─────┘   └─────┬──────┘   └─────┬──────┘
         │               │                │
         │          ┌────┴────┐           │
         │          │ teams   │           │
         │          └─────────┘           │
         │                                  │
    ┌────┴──────────────────────────────────┴────┐
    │              Authentication                │
    │  users → user_roles → roles               │
    │  roles → role_permissions → permissions    │
    │  users → sessions                          │
    │  users → api_tokens                        │
    │  users → password_resets                   │
    │  users → login_history                     │
    │  users → activity_logs                     │
    └────────────────────────────────────────────┘

    ┌────────────────────────────────────────────┐
    │              ETL Domain                     │
    │                                             │
    │  data_sources → connectors                  │
    │  data_sources → etl_jobs                    │
    │  etl_jobs → transformations                 │
    │  etl_jobs → validation_rules                │
    │  etl_jobs → etl_schedules                   │
    │  etl_jobs → etl_logs                        │
    │  etl_jobs → job_status                      │
    │  pipeline_runs → pipeline_steps             │
    │  pipeline_runs → pipeline_history           │
    │  etl_jobs → datasets                        │
    └────────────────────────────────────────────┘

    ┌────────────────────────────────────────────┐
    │           Analytics Domain                  │
    │                                             │
    │  dashboards → dashboard_widgets             │
    │  charts → chart_settings                    │
    │  users → saved_filters                      │
    │  kpis → analytics_history                   │
    └────────────────────────────────────────────┘

    ┌────────────────────────────────────────────┐
    │          Data Warehouse                     │
    │                                             │
    │  fact_sales → dim_date                      │
    │  fact_sales → dim_customer                  │
    │  fact_sales → dim_product                   │
    │  fact_sales → dim_region                    │
    │  fact_sales → dim_category                  │
    │  agg_sales_monthly (standalone aggregate)   │
    │  data_snapshots (standalone)                │
    └────────────────────────────────────────────┘

    ┌────────────────────────────────────────────┐
    │     Audit / Settings / Notifications        │
    │                                             │
    │  users → audit_logs                         │
    │  users → user_activity                      │
    │  users → notifications                      │
    │  users → user_preferences                   │
    │  system_settings (standalone)               │
    │  feature_flags (standalone)                 │
    └────────────────────────────────────────────┘
```

### Key Relationships (FK Summary)

| From | To | On Delete |
|------|-----|----------|
| users.organization_id | organizations.id | SET NULL |
| users.department_id | departments.id | SET NULL |
| user_roles.user_id | users.id | CASCADE |
| user_roles.role_id | roles.id | CASCADE |
| role_permissions.role_id | roles.id | CASCADE |
| role_permissions.permission_id | permissions.id | CASCADE |
| sessions.user_id | users.id | CASCADE |
| api_tokens.user_id | users.id | CASCADE |
| branches.organization_id | organizations.id | CASCADE |
| departments.organization_id | organizations.id | CASCADE |
| departments.branch_id | branches.id | SET NULL |
| departments.parent_id | departments.id | SET NULL |
| teams.department_id | departments.id | CASCADE |
| etl_jobs.data_source_id | data_sources.id | SET NULL |
| connectors.data_source_id | data_sources.id | CASCADE |
| transformations.etl_job_id | etl_jobs.id | CASCADE |
| validation_rules.etl_job_id | etl_jobs.id | CASCADE |
| etl_schedules.etl_job_id | etl_jobs.id | CASCADE |
| dashboard_widgets.dashboard_id | dashboards.id | CASCADE |
| generated_reports.report_id | reports.id | CASCADE |
| scheduled_reports.report_id | reports.id | CASCADE |
| notifications.user_id | users.id | CASCADE |
| audit_logs.user_id | users.id | SET NULL |
| user_activity.user_id | users.id | CASCADE |

---

## 18. Index Strategy

### Index Categories

| Category | Purpose | Examples |
|----------|---------|---------|
| **Primary Key** | Unique row identification | `id` on every table |
| **Unique** | Prevent duplicates | `uq_users_email`, `uq_roles_name` |
| **Foreign Key** | Join performance | `idx_users_organization`, `idx_sessions_user` |
| **Search** | WHERE clause optimization | `idx_audit_logs_action`, `idx_system_logs_level` |
| **Filter** | Common dashboard filters | `idx_sales_is_deleted`, `idx_etl_jobs_status` |
| **Sort** | ORDER BY optimization | `idx_audit_logs_created`, `idx_pipeline_runs_started_at` |
| **Composite** | Multi-column queries | `idx_region_category`, `idx_agg_monthly_year_month` |

### Critical Indexes for Performance

| Table | Index | Columns | Use Case |
|-------|-------|---------|----------|
| `sales` | `idx_order_date` | `order_date` | Date range filtering |
| `sales` | `idx_region_category` | `region, category` | Dashboard filters |
| `sales` | `idx_order_date_region` | `order_date, region` | Regional time analysis |
| `pipeline_runs` | `idx_pipeline_started` | `started_at` | Recent runs query |
| `audit_logs` | `idx_audit_created` | `created_at` | Time-based audit queries |
| `audit_logs` | `idx_audit_resource` | `resource_type, resource_id` | Resource audit trail |
| `etl_logs` | `idx_etl_logs_created` | `created_at` | Log time queries |
| `fact_sales` | `idx_fact_sales_date` | `order_date_key` | Warehouse date queries |
| `agg_sales_monthly` | `uq_agg_sales_monthly` | `year, month, region, category` | Aggregate lookups |
| `notifications` | `idx_notifications_unread` | `is_read` | Unread notification count |
| `sessions` | `idx_sessions_expires` | `expires_at` | Session cleanup |
| `login_history` | `idx_login_history_created` | `created_at` | Security monitoring |

---

## 19. Migration Strategy

### Principles

- **Alembic** for all schema changes
- **Additive first** — new columns are nullable with defaults
- **Never drop** existing columns or tables in initial migrations
- **Backward compatible** — existing code must work during and after migration
- **Seed data** inserted in separate migration after table creation
- **Test on SQLite first**, then run on MySQL production

### Migration Order

| # | Name | Description | Risk |
|---|------|-------------|------|
| 001 | `extend_sales_table` | Add nullable org_id, dept_id, data_source_id, is_deleted, deleted_at | Low |
| 002 | `extend_pipeline_runs` | Add triggered_by, trigger_source, etl_job_id, duration_seconds | Low |
| 003 | `create_auth_tables` | users, roles, permissions, role_permissions, user_roles | Low |
| 004 | `create_session_tables` | sessions, password_resets, api_tokens, login_history, activity_logs | Low |
| 005 | `create_org_tables` | organizations, branches, departments, teams, organization_settings | Low |
| 006 | `create_etl_domain` | data_sources, connectors, etl_jobs, etl_logs, etl_schedules, transformations, validation_rules, pipeline_steps, pipeline_history, job_status | Low |
| 007 | `create_dataset_domain` | datasets, dataset_versions, dataset_columns, dataset_tags, dataset_metadata, dataset_access | Low |
| 008 | `create_analytics_domain` | dashboards, dashboard_widgets, charts, chart_settings, saved_filters, kpis, analytics_history | Low |
| 009 | `create_reporting_domain` | reports, report_templates, generated_reports, scheduled_reports, exports | Low |
| 010 | `create_ai_domain` | ai_requests, ai_responses, predictions, insights, recommendations, forecast_models | Low |
| 011 | `create_notification_domain` | notifications, notification_templates, notification_preferences, email_queue, sms_queue | Low |
| 012 | `create_audit_domain` | audit_logs, system_logs, security_logs, user_activity | Low |
| 013 | `create_settings_domain` | system_settings, user_preferences, feature_flags | Low |
| 014 | `create_department_domain` | department_types, department_configs, department_metrics | Low |
| 015 | `create_warehouse_domain` | fact_sales, dim_date, dim_customer, dim_product, dim_region, dim_category, agg_sales_monthly, data_snapshots | Low |
| 016 | `seed_default_data` | Default roles, permissions, system settings, department types | Low |

### Migration Execution Plan

```
Phase 1: Migrations 001-002 (extend existing tables)
  → No downtime, additive columns only
  → Existing code unaffected

Phase 2: Migrations 003-004 (auth + sessions)
  → New tables, no impact on existing
  → Wire auth module to use new tables

Phase 3: Migration 005 (organizations)
  → New tables, no impact on existing
  → Optional org_id now available on sales/users

Phase 4: Migrations 006-007 (ETL + dataset domains)
  → New tables for ETL management
  → pipeline_runs can now reference etl_jobs

Phase 5: Migrations 008-010 (analytics, reporting, AI)
  → New tables for dashboard/report/AI features
  → No impact on existing

Phase 6: Migrations 011-013 (notifications, audit, settings)
  → New tables for cross-cutting concerns
  → Audit middleware can start logging

Phase 7: Migration 014 (departments)
  → New tables for department extensibility

Phase 8: Migration 015 (warehouse)
  → New tables for analytics warehouse
  → Populated by scheduled ETL jobs, not real-time

Phase 9: Migration 016 (seed data)
  → Insert default roles, permissions, settings
```

---

## 20. File-by-File Migration Plan

### New Files to Create

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Alembic environment script |
| `alembic/script.py.mako` | Migration template |
| `alembic/versions/001_extend_sales_table.py` | Add columns to sales |
| `alembic/versions/002_extend_pipeline_runs.py` | Add columns to pipeline_runs |
| `alembic/versions/003_create_auth_tables.py` | Auth domain tables |
| `alembic/versions/004_create_session_tables.py` | Session/token tables |
| `alembic/versions/005_create_org_tables.py` | Organization domain |
| `alembic/versions/006_create_etl_domain.py` | ETL domain tables |
| `alembic/versions/007_create_dataset_domain.py` | Dataset domain |
| `alembic/versions/008_create_analytics_domain.py` | Analytics domain |
| `alembic/versions/009_create_reporting_domain.py` | Reporting domain |
| `alembic/versions/010_create_ai_domain.py` | AI domain |
| `alembic/versions/011_create_notification_domain.py` | Notification domain |
| `alembic/versions/012_create_audit_domain.py` | Audit domain |
| `alembic/versions/013_create_settings_domain.py` | Settings domain |
| `alembic/versions/014_create_department_domain.py` | Department domain |
| `alembic/versions/015_create_warehouse_domain.py` | Warehouse domain |
| `alembic/versions/016_seed_default_data.py` | Seed data |
| `database/models/__init__.py` | Model package init |
| `database/models/auth.py` | User, Role, Permission ORM |
| `database/models/organization.py` | Org, Branch, Dept, Team ORM |
| `database/models/etl.py` | ETL domain ORM |
| `database/models/dataset.py` | Dataset domain ORM |
| `database/models/analytics.py` | Analytics domain ORM |
| `database/models/reporting.py` | Reporting domain ORM |
| `database/models/ai.py` | AI domain ORM |
| `database/models/notification.py` | Notification domain ORM |
| `database/models/audit.py` | Audit domain ORM |
| `database/models/settings.py` | Settings domain ORM |
| `database/models/department.py` | Department domain ORM |
| `database/models/warehouse.py` | Warehouse domain ORM |
| `database/models/sales.py` | SalesRecord ORM (moved from db_setup.py) |
| `database/models/pipeline.py` | PipelineRun ORM (moved from db_setup.py) |

### Files to Modify

| File | Change | Risk |
|------|--------|------|
| `database/db_setup.py` | Import all model modules so `Base.metadata.create_all` creates all tables | Low |
| `database/repositories.py` | No change needed — existing queries still work | None |
| `etl/load.py` | No change needed — inserts into `sales` still work | None |
| `config.py` | Add `ALEMBIC` config if needed | Low |
| `requirements.txt` | Add `alembic` dependency | Low |

### Files to Keep Unchanged

| File | Notes |
|------|-------|
| `etl/extract.py` | No DB interaction |
| `etl/transform.py` | No DB interaction |
| `services/etl_service.py` | Uses pipeline_runs — still works with new nullable columns |
| `services/dashboard_data_service.py` | Queries sales — still works |
| `api/main.py` | Uses repositories — still works |
| `api/schemas.py` | Pydantic schemas — no change |
| `api/auth.py` | API key auth — will be replaced later by JWT |
| `dashboard/app.py` | Streamlit — still works |
| `scheduler/scheduler.py` | APScheduler — still works |
| `monitoring/health_check.py` | Health checks — still works |

---

## 21. Data Dictionary

### Naming Convention Summary

| Prefix/Suffix | Meaning | Example |
|---------------|---------|---------|
| `id` | Primary key | `users.id` |
| `*_id` | Foreign key | `user_id`, `organization_id` |
| `*_at` | Timestamp | `created_at`, `deleted_at` |
| `is_*` | Boolean flag | `is_active`, `is_deleted` |
| `*_key` | Surrogate/business key | `setting_key`, `meta_key` |
| `*_value` | Value field | `setting_value`, `metric_value` |
| `*_config` | JSON configuration | `query_config`, `display_config` |
| `*_count` | Integer count | `row_count`, `column_count` |
| `*_name` | Human-readable name | `full_name`, `display_name` |

### Common Columns (All New Tables)

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `id` | BIGINT UNSIGNED | AUTO_INCREMENT | Primary key |
| `created_at` | TIMESTAMP | CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | CURRENT_TIMESTAMP ON UPDATE | Last modification time |
| `is_deleted` | TINYINT(1) | 0 | Soft delete flag |
| `deleted_at` | TIMESTAMP | NULL | When soft-deleted |

### Domain Table Count Summary

| Domain | Tables | New Columns on Existing |
|--------|--------|------------------------|
| Authentication | 9 | 0 |
| Organization | 5 | 0 |
| ETL | 11 | 4 on `pipeline_runs` |
| Dataset | 6 | 0 |
| Analytics | 7 | 0 |
| Reporting | 5 | 0 |
| AI | 6 | 0 |
| Notification | 5 | 0 |
| Audit | 4 | 0 |
| Settings | 3 | 0 |
| Department | 3 | 0 |
| Data Warehouse | 8 | 0 |
| **Existing (extended)** | 2 | 5 on `sales` |
| **Total** | **~74** | **9** |

---

## Approval

This document is a **specification only**. No SQL has been executed. No migrations have been created. Implementation will begin only after explicit approval.

**To approve and proceed with implementation, confirm:**
1. The domain structure is acceptable
2. The table list is complete
3. The migration order is correct
4. The existing table extensions are acceptable
