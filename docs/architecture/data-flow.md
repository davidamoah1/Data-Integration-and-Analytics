# Data Flow

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Document how data flows through the platform from upload to report.

## Scope

All major data flows: dataset upload, ETL pipeline, dashboard generation, report generation, document capture.

## Audience

Developers, data engineers, and architects.

---

## 1. Dataset Upload Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Select file + upload
    F->>A: POST /api/datasets (JWT + file)
    A->>A: require_permissions("datasets.upload")
    A->>A: require_organization_access
    A->>A: Validate file format
    A->>D: INSERT dataset (org_id)
    A->>A: Parse file (CSV/Excel)
    A->>D: INSERT dataset rows
    A->>D: INSERT audit_log
    A-->>F: 201 Created
    F-->>U: Dataset uploaded
```

## 2. ETL Pipeline Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant E as ETL Service
    participant D as Database

    U->>A: POST /api/workflows/{id}/execute
    A->>A: require_permissions("pipelines.execute")
    A->>A: _ensure_org_access(workflow)
    A->>E: Execute pipeline
    E->>D: Read source data
    E->>E: Transform (clean, aggregate, join)
    E->>D: Write to target table
    E->>D: INSERT pipeline_run (status)
    E-->>A: Execution complete
    A-->>U: 200 OK with run status
```

## 3. Dashboard Generation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Open dashboard
    F->>A: GET /api/dashboards/{id}
    A->>A: require_permissions("dashboard.view")
    A->>A: require_organization_access
    A->>D: SELECT dashboard (org_id filter)
    A->>D: SELECT widgets + data sources
    D-->>A: Dashboard config + data
    A-->>F: Dashboard JSON
    F->>F: Render charts (client-side)
    F-->>U: Interactive dashboard
```

## 4. Report Generation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Click "Generate Report"
    F->>A: POST /api/reports
    A->>A: require_permissions("reports.generate")
    A->>A: require_organization_access
    A->>D: SELECT data sources (org-scoped)
    A->>A: Compile report data
    A->>D: INSERT report record
    A->>D: INSERT audit_log
    A-->>F: 201 Created
    F-->>U: Report ready

    U->>F: Click "Export"
    F->>A: GET /api/reports/{id}/export?format=pdf
    A->>A: require_permissions("reports.export")
    A->>A: Generate PDF/CSV/Excel
    A-->>F: File download
    F-->>U: Downloaded file
```

## 5. Document Capture Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant C as Capture Service
    participant D as Database

    U->>F: Upload document (PDF/image)
    F->>A: POST /api/capture/upload
    A->>A: require_permissions("datasets.upload")
    A->>C: Process document (OCR)
    C->>C: Extract text + fields
    C->>C: Confidence scoring
    C-->>A: Extracted data
    A->>D: INSERT captured dataset (org_id)
    A-->>F: Extracted data + confidence
    F-->>U: Review extracted data
    U->>F: Correct low-confidence fields
    F->>A: PUT /api/capture/{id}
    A->>D: UPDATE captured data
    A-->>F: 200 OK
    F-->>U: Data submitted
```

## 6. Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database

    C->>A: POST /api/auth/login (email, password)
    A->>D: SELECT user WHERE email = ?
    A->>A: Verify password (bcrypt)
    A->>A: Check is_active + lockout
    A->>D: SELECT roles + permissions
    A->>A: Create access_token (JWT with roles, perms, org_id)
    A->>A: Create refresh_token
    A->>D: INSERT session (refresh_token)
    A->>D: INSERT login_history
    A-->>C: {access_token, refresh_token, user}

    Note over C,A: Subsequent requests
    C->>A: GET /api/anything (Authorization: Bearer <token>)
    A->>A: Decode JWT → get_current_user
    A->>A: require_permissions → require_org_access
    A-->>C: Response
```

## 7. Invitation Flow

```mermaid
sequenceDiagram
    participant Admin as Org Admin
    participant Invitee as Invitee
    participant A as API
    participant D as Database

    Admin->>A: POST /api/invitations (email, role_name)
    A->>A: require_permissions("users.manage")
    A->>A: Validate role (not super_admin/org_owner)
    A->>D: INSERT invitation (token, email, role_id, expiry 7d)
    A->>D: INSERT audit_log
    A-->>Admin: Invitation created

    Invitee->>A: GET /api/invitations/info/{token}
    A->>D: SELECT invitation WHERE token = ?
    A->>A: Check status (pending) + expiry
    A-->>Invitee: Invitation details

    Invitee->>A: POST /api/invitations/accept (token, email, name, password)
    A->>A: Validate email matches invitation
    A->>A: Check no existing user with email
    A->>D: INSERT user (org_id from invitation)
    A->>D: INSERT user_role (role from invitation)
    A->>D: UPDATE invitation SET status = 'accepted'
    A->>D: INSERT audit_log
    A-->>Invitee: {access_token, refresh_token, user}
```

## Related Documents

- [sequence-diagrams.md](sequence-diagrams.md) — More sequence diagrams
- [system-design.md](system-design.md) — System design details
- [../workflows/](../workflows/) — Workflow documentation
