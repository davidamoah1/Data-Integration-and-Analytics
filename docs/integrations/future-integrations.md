# Future Integrations

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Solution Architect

---

## Purpose

Document all planned future integrations.

## Scope

All integrations not yet implemented.

## Audience

Product managers, architects, and developers.

---

## 1. Planned Integrations

| Integration | Priority | Target | Description |
|-------------|----------|--------|-------------|
| SAML 2.0 SSO | Medium | Q3 2026 | Enterprise single sign-on |
| OIDC SSO | Medium | Q3 2026 | OpenID Connect authentication |
| SCIM 2.0 | Medium | Q3 2026 | Automated user provisioning |
| API Keys | High | Q3 2026 | Programmatic API access |
| MFA (TOTP) | High | Q3 2026 | Multi-factor authentication |
| Cloud Storage (S3) | Medium | Q4 2026 | Dataset file storage offloading |
| Email Service | Medium | Q3 2026 | Transactional email sending |
| Stripe Billing | Low | Q4 2026 | Payment processing |
| White-Label | Low | Q4 2026 | Custom branding per org |
| Webhooks (outbound) | Medium | Q3 2026 | Event notifications to external systems |
| Plugin Marketplace | Low | Q4 2026 | Community extensions |

## 2. Architecture Readiness

All planned integrations are designed as extensions to the current architecture:
- SSO: JWT-based auth supports SAML/OIDC token verification
- MFA: User model has extension columns ready
- API Keys: APIToken model exists in database
- SCIM: User CRUD endpoints can be adapted for SCIM
- Cloud Storage: Dataset model can store external URLs

See [ADR-0012](../architecture/adr/README.md) for detailed readiness assessment.

## 3. Frontend Placeholder Pages

The following frontend pages exist as placeholders for future features:
- `/api-keys` — API key management
- `/billing` — Billing and subscription
- `/connectors` — Data connectors
- `/webhooks` — Webhook configuration
- `/marketplace` — Extension marketplace

## Related Documents

- [../architecture/integrations.md](../architecture/integrations.md) — Current integrations
- [../architecture/adr/README.md](../architecture/adr/README.md) — ADR-0012 (Future Readiness)
- [../product/roadmap.md](../product/roadmap.md) — Product roadmap
