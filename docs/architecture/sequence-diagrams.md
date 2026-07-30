# Sequence Diagrams

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Sequence diagrams for key platform flows.

## Scope

Authentication, registration, invitation, ETL, and error handling flows.

## Audience

Developers and architects.

---

## 1. Registration — Create Organization

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database

    U->>A: POST /api/auth/signup (email, password, org_name)
    A->>D: Check existing user (email)
    A->>D: Check existing org (slug)
    A->>D: INSERT organization
    A->>D: INSERT workspace (type=organization)
    A->>D: INSERT user (org_id, is_active=1)
    A->>D: INSERT user_role (org_admin)
    A->>D: INSERT audit_log (organization.created)
    A->>D: INSERT audit_log (user.registered)
    A->>D: INSERT audit_log (role.assigned)
    A->>A: Create access_token + refresh_token
    A->>D: INSERT session
    A->>D: COMMIT
    A-->>U: {access_token, refresh_token, user}
```

## 2. Registration — Join via Invitation

```mermaid
sequenceDiagram
    participant U as Invitee
    participant A as API
    participant D as Database

    U->>A: POST /api/auth/signup-v2 (mode=join_organization, token, email, name, password)
    A->>D: SELECT invitation WHERE token = ?
    A->>A: Check status = pending
    A->>A: Check not expired
    A->>A: Validate email matches invitation
    A->>D: Check no existing user (email)
    A->>D: INSERT user (org_id from invitation)
    A->>D: INSERT user_role (role from invitation)
    A->>D: UPDATE invitation SET status = accepted
    A->>D: INSERT audit_log (user.registered)
    A->>D: INSERT audit_log (invitation.accepted)
    A->>A: Create tokens
    A->>D: INSERT session
    A->>D: COMMIT
    A-->>U: {access_token, refresh_token, user}
```

## 3. Registration — Personal Workspace

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database

    U->>A: POST /api/auth/signup-v2 (mode=personal, email, password, name)
    A->>D: Check existing user (email)
    A->>D: INSERT user (org_id=NULL, is_active=1)
    A->>D: INSERT workspace (type=personal, user_id)
    A->>D: INSERT user_role (viewer)
    A->>D: INSERT audit_log (user.registered, mode=personal)
    A->>A: Create tokens
    A->>D: INSERT session
    A->>D: COMMIT
    A-->>U: {access_token, refresh_token, user}
```

## 4. Token Refresh

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database

    C->>A: POST /api/auth/refresh (refresh_token)
    A->>D: SELECT session WHERE refresh_token = ?
    A->>A: Check not expired
    A->>A: Create new access_token
    A-->>C: {access_token}
```

## 5. Error Handling

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant M as Middleware

    C->>A: API Request
    A->>A: Exception occurs
    A->>M: HTTPException (status, detail)
    M-->>C: {"success": false, "message": detail, "data": null}

    Note over A,M: Unhandled Exception
    A->>M: Exception (unhandled)
    M->>M: Log exception
    M-->>C: {"success": false, "message": "Internal server error", "data": null}
```

## Related Documents

- [data-flow.md](data-flow.md) — Data flow diagrams
- [system-design.md](system-design.md) — System design
- [../backend/authentication.md](../backend/authentication.md) — Authentication details
