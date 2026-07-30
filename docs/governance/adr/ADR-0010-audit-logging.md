# ADR-0010: Audit Logging

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0005, ADR-0008 |

---

## Context

Enterprise platforms require comprehensive audit logging for:
- Security investigations
- Compliance (SOC 2, ISO 27001, GDPR)
- User activity tracking
- Change history
- Incident response

Without audit logging, there is no accountability for who did what and when.

## Decision

We implemented **comprehensive audit logging** for all critical platform actions.

### Log Types

1. **AuditLog** (`audit/models.py:AuditLog`): Records who, what, when, where, and what changed
2. **SecurityLog** (`audit/models.py:SecurityLog`): Records security events (login, logout, access denied)
3. **UserActivity** (`audit/models.py:UserActivity`): Records user activity for analytics
4. **SystemLog** (`audit/models.py:SystemLog`): Records system-level events and errors

### AuditLog Fields

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | BigInteger | Who performed the action |
| `organization_id` | BigInteger | Which org was affected |
| `action` | String(100) | What happened (e.g., `user.created`) |
| `resource_type` | String(50) | Type of resource (e.g., `user`, `organization`) |
| `resource_id` | BigInteger | ID of affected resource |
| `old_values` | JSON | Previous state (for updates) |
| `new_values` | JSON | New state (for creates/updates) |
| `ip_address` | String(45) | Request IP address |
| `user_agent` | String(500) | Browser/client identifier |
| `request_id` | String(100) | Correlation ID for tracing |
| `created_at` | TIMESTAMP | When the event occurred |

### Audited Actions

| Action | Trigger | Location |
|--------|---------|----------|
| `user.registered` | New user signup | `authentication/routes.py`, `organizations/invitation_service.py` |
| `user.created` | Admin creates user | `authentication/services.py:UserService.create_user()` |
| `user.updated` | User profile updated | `authentication/services.py:UserService.update_user()` |
| `user.deleted` | User soft-deleted | `authentication/services.py:UserService.delete_user()` |
| `role.assigned` | Roles assigned to user | `authentication/services.py:UserService.assign_roles()` |
| `organization.created` | New org created | `authentication/routes.py`, `organizations/invitation_service.py` |
| `organization.updated` | Org settings changed | `organizations/services.py:update_organization()` |
| `organization.deleted` | Org soft-deleted | `organizations/services.py:delete_organization()` |
| `invitation.sent` | Invitation created | `organizations/invitation_service.py:create_invitation()` |
| `invitation.accepted` | Invitation accepted | `organizations/invitation_service.py:accept_invitation()` |

### Implementation

1. **AuditLog model** (`audit/models.py`): SQLAlchemy model with JSON columns for old/new values
2. **Direct insertion**: Audit log entries are created via `db.add(AuditLog(...))` in service methods
3. **Org-scoped**: All audit logs include `organization_id` for tenant-scoped queries
4. **Audit log viewing**: `/api/audit/logs` endpoint with `audit.view` permission, org-scoped
5. **Frontend**: `/audit` page with search and filtering

### Key Code Paths

```python
# Creating an audit log entry
db.add(AuditLog(
    user_id=current_user["id"],
    organization_id=org_id,
    action="organization.updated",
    resource_type="organization",
    resource_id=org_id,
    new_values=request.model_dump(exclude_none=True),
))

# Querying audit logs (org-scoped)
@router.get("/api/audit/logs")
async def list_audit_logs(
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    if is_super_admin(current_user):
        # See all logs
    else:
        org_id = get_current_organization_id(current_user, db)
        # Filter by org_id
```

## Alternatives Considered

1. **External logging service** (e.g., Datadog, Splunk): Good for system logs but rejected for audit logs due to compliance requirements (audit logs must be in the primary database for data integrity).
2. **Event sourcing**: All state changes as events. Considered for future but too complex for initial implementation.
3. **Append-only audit table**: Separate database for audit logs. Considered for future but adds operational complexity.

## Consequences

### Positive
- Complete audit trail of all critical actions
- Org-scoped audit log viewing
- JSON columns capture before/after state
- Searchable and filterable via API and frontend
- Supports compliance requirements

### Negative
- Audit log table grows continuously (no automatic archival yet)
- No IP address and user agent capture in current implementation (fields exist but not populated)
- No automatic log rotation or archival

### Mitigations
- Indexes on `organization_id`, `action`, and `created_at` for query performance
- Future: Add background job to archive old logs
- Future: Populate `ip_address` and `user_agent` from request context

## Implementation Notes

- `AuditLog` has indexes: `idx_audit_org_created` on `(organization_id, created_at)`
- `SecurityLog` has indexes: `idx_security_org_created` on `(organization_id, created_at)`
- `UserActivity` has indexes: `idx_activity_user_created` on `(user_id, created_at)`
- Audit logs are created synchronously within the same transaction as the action
- The `auditor` role has `audit.view` permission for read-only audit access

## Future Considerations

- Populate `ip_address`, `user_agent`, and `request_id` from request context
- Add automatic log archival (move logs older than 1 year to cold storage)
- Add audit log export (CSV, PDF) for compliance reports
- Add real-time audit log streaming (WebSocket)
- Add anomaly detection on audit logs (unusual access patterns)
- Add tamper-proof logging (cryptographic chaining of log entries)
- Integrate with SIEM systems

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0005: Role-Based Access Control
- ADR-0008: Permission Middleware
