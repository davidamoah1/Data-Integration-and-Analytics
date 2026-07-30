# Component Diagram

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Visual representation of all major platform components and their relationships.

## Scope

All subsystems, external integrations, and data stores.

## Audience

Developers, architects, and new team members.

---

## 1. Full System Component Diagram

```mermaid
graph TB
    subgraph Client Layer
        Browser[Web Browser]
        APIClient[API Client / SDK]
    end

    subgraph Frontend
        NextJS[Next.js 14 App]
        AuthStore[Zustand Auth Store]
        RouteGuard[RouteGuard]
        Can[Can Component]
        Sidebar[Sidebar Nav]
        Theme[ThemeProvider]
    end

    subgraph Backend API
        FastAPI[FastAPI Server]
        AuthRouter[Auth Router]
        UserRouter[User Router]
        RoleRouter[Role Router]
        OrgRouter[Org Router]
        InvitationRouter[Invitation Router]
        AuditRouter[Audit Router]
        ETLRouter[ETL Router]
        AIRouter[AI Router]
        AnalyticsRouter[Analytics Router]
        MLRouter[ML Router]
        CaptureRouter[Capture Router]
        StudiosRouter[Studios Router]
        SaaSRouter[SaaS Router]
        ConnectorRouter[Connector Router]
        WorkflowRouter[Workflow Router]
    end

    subgraph Middleware
        CORS[CORS Middleware]
        RateLimit[Rate Limit Middleware]
        TenantIsolation[Tenant Isolation Middleware]
        SecurityHeaders[Security Headers Middleware]
        RequestLog[Request Logging Middleware]
        GZip[GZip Middleware]
        RequestContext[Request Context Middleware]
        RequestSize[Request Size Limit]
    end

    subgraph Services
        AuthService[Auth Service]
        UserService[User Service]
        RoleService[Role Service]
        InvitationService[Invitation Service]
        RegistrationService[Registration Service]
        ETLService[ETL Service]
        BackupService[Backup Service]
        ReportScheduler[Report Scheduler]
    end

    subgraph Data Layer
        PostgreSQL[(PostgreSQL)]
        Repositories[Repositories]
        ORM[SQLAlchemy ORM]
    end

    subgraph Security
        JWT[JWT Token Manager]
        PasswordHash[Password Hashing bcrypt]
        TenantContext[Tenant Context]
        TenantFilter[Tenant Filter]
        RBAC[RBAC Permission Check]
    end

    Browser --> NextJS
    APIClient --> FastAPI
    NextJS --> AuthStore
    NextJS --> RouteGuard
    NextJS --> Can
    NextJS --> Sidebar
    NextJS --> Theme

    FastAPI --> CORS
    CORS --> RateLimit
    RateLimit --> TenantIsolation
    TenantIsolation --> SecurityHeaders
    SecurityHeaders --> RequestLog
    RequestLog --> GZip
    GZip --> RequestContext
    RequestContext --> RequestSize

    FastAPI --> AuthRouter
    FastAPI --> UserRouter
    FastAPI --> RoleRouter
    FastAPI --> OrgRouter
    FastAPI --> InvitationRouter
    FastAPI --> AuditRouter
    FastAPI --> ETLRouter
    FastAPI --> AIRouter
    FastAPI --> AnalyticsRouter
    FastAPI --> MLRouter
    FastAPI --> CaptureRouter
    FastAPI --> StudiosRouter
    FastAPI --> SaaSRouter
    FastAPI --> ConnectorRouter
    FastAPI --> WorkflowRouter

    AuthRouter --> AuthService
    UserRouter --> UserService
    RoleRouter --> RoleService
    InvitationRouter --> InvitationService
    InvitationRouter --> RegistrationService
    ETLRouter --> ETLService

    AuthService --> JWT
    AuthService --> PasswordHash
    AuthService --> RBAC
    UserService --> RBAC
    OrgRouter --> TenantContext
    OrgRouter --> TenantFilter

    AuthService --> Repositories
    UserService --> Repositories
    RoleService --> Repositories
    InvitationService --> Repositories
    ETLService --> Repositories
    Repositories --> ORM
    ORM --> PostgreSQL

    ReportScheduler --> PostgreSQL
    BackupService --> PostgreSQL
```

## 2. Authentication & Authorization Component Diagram

```mermaid
graph LR
    Request[HTTP Request + JWT] --> GetCurrentUser[get_current_user]
    GetCurrentUser --> DecodeJWT[Decode JWT]
    DecodeJWT --> LoadUser[Load User from DB]
    LoadUser --> LoadRoles[Load Roles]
    LoadRoles --> LoadPermissions[Load Permissions]
    LoadPermissions --> RequirePerms[require_permissions]
    RequirePerms --> CheckSuperAdmin{Is Super Admin?}
    CheckSuperAdmin -->|Yes| Bypass[Bypass all checks]
    CheckSuperAdmin -->|No| CheckPerm{Has Permission?}
    CheckPerm -->|Yes| Continue[Continue to route]
    CheckPerm -->|No| Forbidden403[403 Forbidden]
    Bypass --> Continue
    Continue --> RequireOrgAccess[require_organization_access]
    RequireOrgAccess --> CheckOrg{Same Org?}
    CheckOrg -->|Yes| RouteHandler[Route Handler]
    CheckOrg -->|No| Forbidden403
```

## 3. Multi-Tenant Component Diagram

```mermaid
graph TB
    subgraph Platform Level
        SuperAdmin[Super Admin]
        AdminPortal[Admin Portal]
        AllOrgs[All Organizations]
    end

    subgraph Organization A
        OrgAdminA[Org Admin A]
        UsersA[Users in Org A]
        DataA[Data in Org A]
        DeptA1[Department 1]
        DeptA2[Department 2]
    end

    subgraph Organization B
        OrgAdminB[Org Admin B]
        UsersB[Users in Org B]
        DataB[Data in Org B]
        DeptB1[Department 1]
    end

    subgraph Personal Workspaces
        PersonalUser1[Personal User 1]
        PersonalUser2[Personal User 2]
        PersonalData1[Personal Data 1]
        PersonalData2[Personal Data 2]
    end

    SuperAdmin --> AllOrgs
    SuperAdmin --> AdminPortal
    AllOrgs --> OrgAdminA
    AllOrgs --> OrgAdminB
    OrgAdminA --> UsersA
    OrgAdminA --> DataA
    UsersA --> DeptA1
    UsersA --> DeptA2
    OrgAdminB --> UsersB
    OrgAdminB --> DataB
    UsersB --> DeptB1
    PersonalUser1 --> PersonalData1
    PersonalUser2 --> PersonalData2

    style SuperAdmin fill:#f96,stroke:#333
    style OrgAdminA fill:#6f9,stroke:#333
    style OrgAdminB fill:#6f9,stroke:#333
    style PersonalUser1 fill:#69f,stroke:#333
    style PersonalUser2 fill:#69f,stroke:#333
```

## Related Documents

- [system-design.md](system-design.md) — Detailed system design
- [overview.md](overview.md) — Architecture overview
- [data-flow.md](data-flow.md) — Data flow through the platform
- [sequence-diagrams.md](sequence-diagrams.md) — Sequence diagrams for key flows
