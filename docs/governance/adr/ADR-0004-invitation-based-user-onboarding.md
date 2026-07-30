# ADR-0004: Invitation-Based User Onboarding

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0005, ADR-0006 |

---

## Context

Organizations need control over who joins their tenant. Unrestricted registration would allow anyone to create an account and access an organization's data, which is unacceptable for enterprise customers with sensitive data and compliance requirements.

The platform needs three registration modes:
1. **Create Organization** — A user creates a new org and becomes its administrator
2. **Join Organization** — A user accepts an invitation from an existing org admin
3. **Personal Workspace** — A user creates a personal account with no org affiliation

## Decision

Organization membership requires **invitation by an existing organization administrator**. Users cannot self-join an organization.

### Implementation

1. **Invitation model** (`organizations/workspace_models.py:Invitation`): Stores organization_id, email, role_id, token, status, and expiry.
2. **InvitationService** (`organizations/invitation_service.py`): Handles creation, acceptance, listing, and revocation of invitations.
3. **Invitation routes** (`organizations/invitation_routes.py`): REST API for invitation management.
4. **Token-based acceptance**: Each invitation has a unique, random token. The invited user must provide the same email as the invitation.
5. **Role restriction**: Invitations cannot assign `super_admin` or `org_owner` roles.
6. **7-day expiry**: Invitations expire after 7 days. Expired invitations are auto-marked on access attempt.
7. **Duplicate prevention**: Only one pending invitation per email per organization.

### Registration Modes

- `create_organization`: User creates org, becomes `org_admin`, workspace auto-created
- `join_organization`: User provides invitation token, email must match, role from invitation
- `personal`: User gets personal workspace, `viewer` role, no org

### Key Code Paths

- `organizations/invitation_routes.py:signup_v2()`: Enhanced registration endpoint
- `organizations/invitation_service.py:InvitationService.create_invitation()`: Creates invitation with role validation
- `organizations/invitation_service.py:InvitationService.accept_invitation()`: Validates token, email match, expiry
- `organizations/invitation_service.py:RegistrationService.register()`: Three-mode registration dispatcher

## Alternatives Considered

1. **Open registration with org code**: Users enter an org code to join. Rejected — codes can be shared/leaked, no admin control over who joins or what role they get.
2. **Admin approval of self-join requests**: Users request to join, admin approves. Considered for future but adds latency and complexity.
3. **SSO-only onboarding**: No local registration. Rejected for initial implementation — SSO is a future capability (ADR-0012).

## Consequences

### Positive
- Organization admins have full control over membership
- Role assignment is determined at invitation time
- Prevents unauthorized users from accessing org data
- Audit trail of who invited whom and when
- Clear separation between org creation, join, and personal modes

### Negative
- Friction for new users (must wait for invitation)
- Admin must proactively invite team members
- No self-service join for existing organizations

### Mitigations
- Invitation emails can include direct acceptance links
- 7-day expiry gives users ample time to accept
- Personal workspace mode available for users who want to explore without an org
- Future: Admin approval workflow for self-join requests

## Implementation Notes

- Invitation tokens are generated using `generate_token()` from `shared/security.py`
- Email match validation prevents token hijacking (must use invited email)
- `InvitationAccept` schema requires `email` field for validation
- Revocation is supported for pending invitations
- Audit logs are created for invitation sent, accepted, and revoked events

## Future Considerations

- Bulk invitation (CSV upload of emails + roles)
- Admin approval workflow for self-join requests
- Invitation email templates with org branding
- Expiring unused invitations automatically via background job
- Integration with SCIM for automated user provisioning (ADR-0012)

## Related ADRs

- ADR-0005: Role-Based Access Control
- ADR-0006: Platform Owner vs Organization Administrator
