# Entity Relationship Diagram

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Database Architect

---

## Purpose

Visual representation of table relationships in the database.

## Scope

Core authentication, organization, and audit tables.

## Audience

Developers and database administrators.

---

## 1. Core Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ UserRole : has
    Role ||--o{ UserRole : assigned_to
    Role ||--o{ RolePermission : has
    Permission ||--o{ RolePermission : belongs_to
    User ||--o{ Session : has
    User ||--o{ LoginHistory : has
    User ||--o{ PasswordReset : has
    User ||--o{ PasswordHistory : has
    User ||--o{ APIToken : has
    User ||--o{ ActivityLog : performs
    User }o--o| Organization : belongs_to
    User }o--o| Department : member_of
    Organization ||--o{ Department : has
    Organization ||--o{ Invitation : sends
    Organization ||--o| Workspace : owns
    Invitation }o--|| Role : assigns
    User ||--o{ AuditLog : triggers

    User {
        bigint id PK
        string email UK
        string password_hash
        string full_name
        bigint organization_id FK
        bigint department_id FK
        int is_active
        int is_deleted
    }

    Role {
        bigint id PK
        string name UK
        string display_name
        int is_system
    }

    Permission {
        bigint id PK
        string name UK
        string module
    }

    UserRole {
        bigint id PK
        bigint user_id FK
        bigint role_id FK
        bigint assigned_by
    }

    RolePermission {
        bigint id PK
        bigint role_id FK
        bigint permission_id FK
    }

    Organization {
        bigint id PK
        string name
        string slug UK
        int is_active
    }

    Department {
        bigint id PK
        bigint organization_id FK
        string name
    }

    Workspace {
        bigint id PK
        bigint organization_id FK
        bigint user_id FK
        string type
    }

    Invitation {
        bigint id PK
        bigint organization_id FK
        string email
        bigint role_id FK
        string token UK
        string status
    }

    Session {
        bigint id PK
        bigint user_id FK
        string refresh_token UK
        timestamp expires_at
    }

    AuditLog {
        bigint id PK
        bigint user_id FK
        bigint organization_id
        string action
        string resource_type
        bigint resource_id
    }
```

## 2. Authentication Entity Relationships

```mermaid
erDiagram
    User ||--o{ Session : has
    User ||--o{ LoginHistory : has
    User ||--o{ PasswordReset : requests
    User ||--o{ PasswordHistory : has
    User ||--o{ APIToken : owns
    User ||--o{ ActivityLog : generates

    PasswordReset {
        bigint id PK
        bigint user_id FK
        string token UK
        timestamp expires_at
        timestamp used_at
    }

    APIToken {
        bigint id PK
        bigint user_id FK
        string name
        string token_hash UK
        string scopes
        timestamp expires_at
    }

    LoginHistory {
        bigint id PK
        bigint user_id FK
        string email
        int success
        string failure_reason
    }

    PasswordHistory {
        bigint id PK
        bigint user_id FK
        string password_hash
    }

    ActivityLog {
        bigint id PK
        bigint user_id FK
        string action
        string resource_type
        bigint resource_id
    }
```

## Related Documents

- [schema.md](schema.md) — Complete schema
- [indexing.md](indexing.md) — Index strategy
- [../governance/organization-model.md](../governance/organization-model.md) — Org model
