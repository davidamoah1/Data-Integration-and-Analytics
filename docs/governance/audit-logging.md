# Audit Logging

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Security Architect

---

## Purpose

Document the audit logging model, audited actions, and log structure.

## Scope

All audit log types, fields, and audited actions.

## Audience

Security architects, auditors, and compliance officers.

---

## 1. Log Types

| Model | Table | Purpose |
|-------|-------|---------|
| `AuditLog` | `audit_logs` | Records who, what, when, where, and what changed |
| `SecurityLog` | `security_logs` | Records security events (login, logout, access denied) |
| `SystemLog` | `system_logs` | Records system-level events and errors |
| `UserActivity` | `user_activities` | Records user activity for analytics |

## 2. AuditLog Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigInteger PK | Unique identifier |
| `user_id` | BigInteger | Who performed the action |
| `organization_id` | BigInteger | Which org was affected |
| `action` | String(100) | What happened (e.g., `user.created`) |
| `resource_type` | String(50) | Type of resource |
| `resource_id` | BigInteger | ID of affected resource |
| `old_values` | JSON | Previous state (for updates) |
| `new_values` | JSON | New state (for creates/updates) |
| `ip_address` | String(45) | Request IP address |
| `user_agent` | String(500) | Browser/client identifier |
| `request_id` | String(100) | Correlation ID |
| `created_at` | TIMESTAMP | When the event occurred |

## 3. Audited Actions

| Action | Trigger | Location |
|--------|---------|----------|
| `user.registered` | New user signup | `authentication/routes.py`, `organizations/invitation_service.py` |
| `user.created` | Admin creates user | `authentication/services.py` |
| `user.updated` | User profile updated | `authentication/services.py` |
| `user.deleted` | User soft-deleted | `authentication/services.py` |
| `role.assigned` | Roles assigned | `authentication/services.py` |
| `organization.created` | New org | `authentication/routes.py`, `organizations/invitation_service.py` |
| `organization.updated` | Org settings changed | `organizations/services.py` |
| `organization.deleted` | Org soft-deleted | `organizations/services.py` |
| `invitation.sent` | Invitation created | `organizations/invitation_service.py` |
| `invitation.accepted` | Invitation accepted | `organizations/invitation_service.py` |

## 4. Audit Log Access

- **Permission**: `audit.view` required
- **Scope**: Org-scoped (non-super-admin sees only own org's logs)
- **Super Admin**: Can see all audit logs across all orgs
- **Frontend**: `/audit` page with search and filtering

## 5. Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_audit_org_created` | `(organization_id, created_at)` | Org-scoped time queries |
| `idx_audit_user_action` | `(user_id, action)` | User activity queries |
| `idx_audit_resource` | `(resource_type, resource_id)` | Resource history queries |

## Related Documents

- [security-model.md](security-model.md) — Security architecture
- [compliance-notes.md](compliance-notes.md) — Compliance readiness
- [../architecture/adr/README.md](../architecture/adr/README.md) — ADR-0010 (Audit Logging)
- [../backend/logging.md](../backend/logging.md) — Application logging
