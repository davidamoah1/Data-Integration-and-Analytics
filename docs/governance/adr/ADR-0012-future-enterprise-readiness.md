# ADR-0012: Future Enterprise Readiness

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0004, ADR-0005, ADR-0008, ADR-0010 |

---

## Context

The current platform provides a solid foundation for enterprise multi-tenancy, RBAC, and audit logging. However, enterprise customers increasingly require additional capabilities for security, compliance, and operational efficiency.

This ADR documents **planned future capabilities** that are not yet implemented. These are architectural extension points that the current design supports without redesign.

> **IMPORTANT**: All features listed below are **future capabilities** and are **not yet implemented**. This ADR serves as a planning document and architectural readiness assessment.

## Decision

We will plan for the following enterprise capabilities, designed as extensions to the current architecture:

---

## 1. Single Sign-On (SSO)

### Status: Planned (Not Implemented)

### Description
Allow users to authenticate via enterprise identity providers (IdP) using SAML 2.0 or OpenID Connect (OIDC).

### Architecture Extension Points
- **Current**: JWT-based authentication with `create_access_token()` and `create_refresh_token()`
- **Future**: Add SAML/OIDC token verification in `get_current_user()` dependency
- **Future**: Map IdP users to local users via email or external ID
- **Future**: Auto-provision users on first SSO login

### Implementation Plan
1. Add `sso_providers` table (provider name, entity_id, metadata_url, cert)
2. Add SAML/OIDC callback endpoint
3. Map IdP groups to platform roles
4. Support multiple IdPs per organization

### Dependencies
- `python3-saml` or `authlib` for SAML/OIDC
- Organization-level IdP configuration

---

## 2. Multi-Factor Authentication (MFA)

### Status: Planned (Not Implemented)

### Description
Require a second authentication factor (TOTP, SMS, email) for sensitive accounts.

### Architecture Extension Points
- **Current**: Password-based authentication in `AuthService.login()`
- **Future**: Add MFA challenge step after password verification
- **Future**: Store MFA secret in `User` model (new column)
- **Future**: Enforce MFA for `super_admin` role

### Implementation Plan
1. Add `mfa_secret`, `mfa_enabled` columns to `User` model
2. Add TOTP setup endpoint (QR code generation)
3. Add MFA verification step in login flow
4. Add backup codes
5. Enforce MFA for super_admin role

### Dependencies
- `pyotp` for TOTP generation
- QR code library for setup

---

## 3. SCIM (System for Cross-domain Identity Management)

### Status: Planned (Not Implemented)

### Description
Automated user provisioning and deprovisioning via SCIM 2.0 API. Enterprise IdPs (Okta, Azure AD) can push user changes to DataFlow automatically.

### Architecture Extension Points
- **Current**: Manual user creation via `UserService.create_user()` and invitation workflow
- **Future**: Add SCIM 2.0 compliant endpoints (`/scim/v2/Users`, `/scim/v2/Groups`)
- **Future**: Map SCIM groups to platform roles
- **Future**: Auto-create/activate/deactivate users based on IdP changes

### Implementation Plan
1. Add SCIM 2.0 router with standard endpoints
2. Map SCIM user attributes to User model
3. Map SCIM groups to roles
4. Support `PATCH` for user updates
5. Handle deactivation on IdP removal

### Dependencies
- SCIM 2.0 compliance library or custom implementation
- Integration with SSO provider

---

## 4. API Keys

### Status: Planned (Not Implemented)

### Description
Allow programmatic access via API keys with scoped permissions. API keys enable automation and integrations without user credentials.

### Architecture Extension Points
- **Current**: JWT-based authentication via `HTTPBearer` in `get_current_user()`
- **Future**: Add API key authentication as alternative to JWT
- **Future**: API keys have scoped permissions (subset of user permissions)
- **Future**: API keys are org-scoped

### Implementation Plan
1. Add `api_keys` table (key, user_id, org_id, scopes, is_active, expires_at)
2. Add API key authentication in `get_current_user()` (check both JWT and API key)
3. Add API key management endpoints (`/api/api-keys`)
4. Add rate limiting per API key
5. Add API key audit logging

### Dependencies
- None (can use existing auth infrastructure)
- Frontend page exists as placeholder (`/api-keys`)

---

## 5. White-Label Deployments

### Status: Planned (Not Implemented)

### Description
Allow organizations to customize the platform's branding (logo, colors, domain) for their users.

### Architecture Extension Points
- **Current**: Fixed DataFlow branding in frontend
- **Future**: Add `organization_branding` table (logo_url, primary_color, custom_domain)
- **Future**: Serve branded assets based on domain or org_id
- **Future**: Custom email templates per org

### Implementation Plan
1. Add branding model and settings
2. Add branding API endpoints
3. Modify frontend to load org branding
4. Support custom domains (CNAME + SSL)
5. Custom email templates for invitations

### Dependencies
- DNS management for custom domains
- SSL certificate provisioning
- CDN for branded assets

---

## 6. Enterprise Licensing

### Status: Planned (Not Implemented)

### Description
Support tiered licensing (Free, Professional, Enterprise) with feature gates and usage limits.

### Architecture Extension Points
- **Current**: All features available to all users
- **Future**: Add `license_tier` to Organization model
- **Future**: Feature gates based on license tier
- **Future**: Usage limits (datasets, users, API calls) per tier

### Implementation Plan
1. Add `license_tier` and `license_expires_at` to Organization model
2. Add license validation middleware
3. Add feature gate checks in routes and frontend
4. Add usage tracking and limits
5. Add billing integration (Stripe or local payment gateway)

### Dependencies
- Payment gateway integration
- License management service
- Frontend billing page exists as placeholder (`/billing`)

---

## Architecture Readiness Assessment

| Capability | Current Readiness | Required Changes |
|------------|-------------------|------------------|
| SSO | Medium | New auth flow, IdP config model, user mapping |
| MFA | Medium | New columns on User, TOTP library, login flow change |
| SCIM | Medium | New SCIM router, user mapping, group-to-role mapping |
| API Keys | High | New table, auth alternative, management endpoints |
| White-Label | Medium | Branding model, frontend dynamic assets, DNS |
| Licensing | Medium | License model, feature gates, billing integration |

## Consequences

### Positive
- Current architecture supports all planned features without redesign
- Extension points are well-defined and documented
- Each feature can be implemented independently
- RBAC and tenant isolation provide the foundation for all enterprise features

### Negative
- All features require significant development effort
- Some features (SSO, SCIM) have external dependencies
- White-label requires infrastructure changes (DNS, SSL)

### Mitigations
- Implement features incrementally (API Keys first, then MFA, then SSO)
- Each feature is independently valuable
- Frontend placeholder pages exist for API Keys and Billing

## Implementation Notes

- Frontend placeholder pages exist: `/api-keys`, `/billing`, `/connectors`, `/webhooks`, `/marketplace`
- These pages are visible in the sidebar but show placeholder content
- The `settings.manage` permission is reserved for platform-level settings (future)
- The `organizations.manage` permission can be extended for org-level branding

## Future Considerations

- Prioritize features based on customer demand
- API Keys and MFA are likely first priorities (lowest complexity, highest value)
- SSO and SCIM are critical for large enterprise customers
- White-label and licensing are monetization features
- All features should maintain the current security model (org isolation, RBAC, audit logging)

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0004: Invitation-Based User Onboarding
- ADR-0005: Role-Based Access Control
- ADR-0008: Permission Middleware
- ADR-0010: Audit Logging
