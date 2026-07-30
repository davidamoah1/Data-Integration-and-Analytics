# Database Schema

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Database Architect

---

## Purpose

Complete database schema documentation.

## Scope

All tables in the DataFlow PostgreSQL database.

## Audience

Developers, database administrators, and architects.

---

## 1. Schema Management

- **ORM**: SQLAlchemy 2.0 declarative models
- **Migration**: No Alembic — tables auto-created via `Base.metadata.create_all(engine)`
- **Naming**: snake_case table and column names
- **Soft Deletes**: `is_deleted` (Integer 0/1) + `deleted_at` (TIMESTAMP) on most tables
- **Timestamps**: `created_at` and `updated_at` with server defaults

## 2. Authentication Tables

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK, auto-increment | Unique identifier |
| email | String(255) | UNIQUE, NOT NULL | User email |
| password_hash | String(255) | NOT NULL | bcrypt hash |
| full_name | String(255) | NOT NULL | Display name |
| avatar_url | String(500) | Nullable | Profile image URL |
| phone | String(50) | Nullable | Phone number |
| organization_id | BigInteger | Nullable, indexed | Org membership |
| department_id | BigInteger | Nullable, indexed | Department |
| position | String(200) | Nullable | Job title |
| language | String(10) | Default "en" | Preferred language |
| timezone | String(50) | Default "UTC" | User timezone |
| is_active | Integer | NOT NULL, default 1 | Account active |
| is_deleted | Integer | NOT NULL, default 0 | Soft delete |
| deleted_at | TIMESTAMP | Nullable | Deletion timestamp |
| last_login_at | TIMESTAMP | Nullable | Last login |
| email_verified_at | TIMESTAMP | Nullable | Email verification |
| failed_login_count | Integer | default 0 | Failed attempts |
| locked_until | TIMESTAMP | Nullable | Lockout expiry |
| onboarding_completed | Integer | default 0 | Onboarding status |
| onboarding_data | JSON | Nullable | Onboarding preferences |
| created_at | TIMESTAMP | server_default now() | Creation |
| updated_at | TIMESTAMP | onupdate now() | Last update |

### roles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| name | String(50) | UNIQUE, NOT NULL | System name (e.g., `super_admin`) |
| display_name | String(100) | NOT NULL | Human-readable name |
| description | Text | Nullable | Role description |
| is_system | Integer | default 0 | System role (immutable) |
| is_deleted | Integer | default 0 | Soft delete |
| deleted_at | TIMESTAMP | Nullable | Deletion timestamp |

### permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| name | String(100) | UNIQUE, NOT NULL | Permission string (e.g., `users.read`) |
| display_name | String(200) | NOT NULL | Human-readable name |
| module | String(50) | NOT NULL, indexed | Module group |
| description | Text | Nullable | Permission description |

### role_permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| role_id | BigInteger | NOT NULL, indexed | FK to roles |
| permission_id | BigInteger | NOT NULL, indexed | FK to permissions |

### user_roles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | NOT NULL, indexed | FK to users |
| role_id | BigInteger | NOT NULL, indexed | FK to roles |
| assigned_by | BigInteger | Nullable | Who assigned the role |

### sessions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | NOT NULL, indexed | FK to users |
| refresh_token | String(500) | UNIQUE, NOT NULL | Refresh token |
| ip_address | String(45) | Nullable | Login IP |
| user_agent | String(500) | Nullable | Browser |
| device | String(200) | Nullable | Device info |
| expires_at | TIMESTAMP | NOT NULL | Token expiry |
| revoked_at | TIMESTAMP | Nullable | Revocation time |
| is_active | Integer | default 1 | Active session |
| last_activity_at | TIMESTAMP | server_default now() | Last activity |

### password_resets

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | NOT NULL, indexed | FK to users |
| token | String(255) | UNIQUE, NOT NULL | Reset token |
| expires_at | TIMESTAMP | NOT NULL | Token expiry |
| used_at | TIMESTAMP | Nullable | When used |

### api_tokens

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | NOT NULL, indexed | FK to users |
| name | String(100) | NOT NULL | Token name |
| token_hash | String(255) | UNIQUE, NOT NULL | Hashed token |
| scopes | String(500) | Nullable | Permission scopes |
| expires_at | TIMESTAMP | Nullable | Token expiry |
| last_used_at | TIMESTAMP | Nullable | Last usage |
| is_active | Integer | default 1 | Active status |

### login_history

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | Nullable, indexed | FK to users |
| email | String(255) | NOT NULL | Login email |
| ip_address | String(45) | Nullable | Login IP |
| user_agent | String(500) | Nullable | Browser |
| success | Integer | default 0 | 1=success, 0=failure |
| failure_reason | String(200) | Nullable | Failure reason |

### activity_logs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | Nullable, indexed | FK to users |
| action | String(100) | NOT NULL, indexed | Action type |
| resource_type | String(50) | Nullable | Resource type |
| resource_id | BigInteger | Nullable | Resource ID |
| ip_address | String(45) | Nullable | Request IP |
| user_agent | String(500) | Nullable | Browser |
| extra_data | JSON | Nullable | Additional data |

### password_history

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInteger | PK | Unique identifier |
| user_id | BigInteger | NOT NULL, indexed | FK to users |
| password_hash | String(255) | NOT NULL | Previous hash |

## 3. Organization Tables

### organizations

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| name | String(255) | Org name |
| slug | String(100) UNIQUE | URL-safe slug |
| description | Text | Org description |
| is_active | Integer | Active status |
| is_deleted | Integer | Soft delete |
| created_at | TIMESTAMP | Creation |
| updated_at | TIMESTAMP | Last update |

### departments

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| organization_id | BigInteger FK | Parent org |
| name | String(255) | Department name |
| description | Text | Department description |
| is_active | Integer | Active status |
| is_deleted | Integer | Soft delete |

### workspaces

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| organization_id | BigInteger | Nullable (null for personal) |
| user_id | BigInteger | Nullable (null for org) |
| name | String(255) | Workspace name |
| type | String(50) | "organization" or "personal" |
| is_active | Integer | Active status |
| is_deleted | Integer | Soft delete |

### invitations

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| organization_id | BigInteger FK | Target org |
| email | String(255) | Invitee email |
| role_id | BigInteger FK | Role to assign |
| token | String(255) UNIQUE | Invitation token |
| status | String(20) | pending/accepted/expired/revoked |
| expires_at | TIMESTAMP | 7-day expiry |
| created_by | BigInteger | Inviter user ID |

## 4. Audit Tables

### audit_logs

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| user_id | BigInteger | Who performed action |
| organization_id | BigInteger | Affected org |
| action | String(100) | Action type |
| resource_type | String(50) | Resource type |
| resource_id | BigInteger | Resource ID |
| old_values | JSON | Previous state |
| new_values | JSON | New state |
| ip_address | String(45) | Request IP |
| user_agent | String(500) | Browser |
| request_id | String(100) | Correlation ID |
| created_at | TIMESTAMP | When |

### security_logs

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | Unique identifier |
| user_id | BigInteger | User involved |
| organization_id | BigInteger | Affected org |
| event_type | String(100) | Event type |
| severity | String(20) | info/warning/critical |
| description | Text | Event description |
| ip_address | String(45) | Request IP |
| created_at | TIMESTAMP | When |

## 5. Other Tables

The platform also includes tables for:
- `analytics` — dashboards, KPIs, widgets
- `etl` — pipelines, runs, transformations
- `ai` — conversations, predictions, reports
- `ml` — models, training jobs, predictions
- `capture` — documents, extracted data, confidence scores
- `notifications` — user notifications
- `scheduler` — scheduled jobs
- `connectors` — external data source configs
- `ecosystem` — plugins, webhooks, marketplace items
- `saas` — tenant management, plans, feature flags
- `studios` — industry-specific configurations
- `validation` — data validation rules
- `workflows` — ETL workflow definitions

## Related Documents

- [entity-relationship.md](entity-relationship.md) — ER diagram
- [migrations.md](migrations.md) — Migration strategy
- [indexing.md](indexing.md) — Index strategy
- [../governance/organization-model.md](../governance/organization-model.md) — Org model
