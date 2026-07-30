# Email Integration

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Planned  
> **Owner**: Backend Lead

---

## Purpose

Document email service integration for transactional emails.

## Scope

Invitation emails, password reset emails, notification emails.

## Audience

Backend developers and product managers.

---

> **⚠️ Planned**: Email service integration is not yet fully implemented. Invitation tokens are generated but not automatically emailed.

## 1. Current State

- Invitation tokens are generated and returned via API
- Password reset tokens are generated and returned via API
- No automated email sending yet
- Users must manually share invitation links

## 2. Planned Email Service

| Provider | Status | Use Case |
|----------|--------|----------|
| SMTP | ⚠️ Planned | Self-hosted email |
| SendGrid | ⚠️ Planned | Cloud email service |
| AWS SES | ⚠️ Planned | Amazon email service |
| Postmark | ⚠️ Planned | Transactional email |

## 3. Planned Email Types

| Email | Trigger | Template |
|-------|---------|----------|
| Invitation email | Invitation created | Organization invite with accept link |
| Password reset | Reset requested | Reset link with token |
| Email verification | Signup completed | Verification link |
| Report ready | Scheduled report completed | Download link |
| Welcome email | Registration completed | Getting started guide |

## Related Documents

- [../backend/authentication.md](../backend/authentication.md) — Authentication
- [../governance/organization-model.md](../governance/organization-model.md) — Invitations
- [future-integrations.md](future-integrations.md) — Future integrations
