# Missing Features

## Overview

Features required for a production-ready enterprise Data Intelligence Platform, identified during the system audit.

---

## CRITICAL

### MF-C1: No Password Reset Flow (Frontend)
**Location**: `frontend/app/forgot-password/`, `frontend/app/reset-password/`
**Description**: Frontend pages exist for forgot-password and reset-password, but the backend password reset flow is incomplete. No email verification, no token generation endpoint exposed in the frontend service layer.
**Required for**: User onboarding, account recovery, compliance.
**Fix**: Complete the password reset flow: request reset → email token → reset password → verify.

### MF-C2: No Email Verification Flow
**Location**: `authentication/models.py:40` (`email_verified_at` column exists)
**Description**: The `User` model has an `email_verified_at` column but there is no endpoint or flow to verify email addresses. Signup does not require email verification.
**Required for**: Account security, compliance, preventing fake accounts.
**Fix**: Add email verification endpoint, send verification email on signup, block access until verified.

### MF-C3: No Search Results Page
**Location**: `frontend/app/`
**Description**: The `AdaptiveSearch` component routes to `/search?q=` but no `/search` page exists. The search feature is non-functional.
**Required for**: Finding datasets, dashboards, reports across the platform.
**Fix**: Create `/search` page that consumes query and scope parameters, calls backend search API.

---

## HIGH

### MF-H1: No User Profile Management
**Location**: `frontend/app/(app)/settings/`
**Description**: Settings page exists but lacks profile editing (name, avatar, phone, timezone, language). The `User` model supports these fields but no UI exists.
**Required for**: User self-service, personalization.
**Fix**: Add profile editing form in settings.

### MF-H2: No Organization Settings UI
**Location**: `frontend/app/(app)/settings/`
**Description**: No UI for organization owners/admins to manage organization settings (name, branding, industry, workspace type).
**Required for**: Organization management, multi-tenant configuration.
**Fix**: Add organization settings panel for org_owner and org_admin roles.

### MF-H3: No Department Management UI
**Location**: `frontend/app/(app)/admin/`
**Description**: The backend supports department CRUD, but the frontend admin page only shows user management. No department creation/editing UI.
**Required for**: Department-level organization, role assignment.
**Fix**: Add department management tab in admin panel.

### MF-H4: No Notification Delivery System
**Location**: `frontend/lib/notifications.ts`
**Description**: Notification type configuration exists (17 types), but there is no backend notification delivery system (WebSocket, polling, or push). The TopNav shows "No new notifications" statically.
**Required for**: Real-time user engagement, alerting.
**Fix**: Implement notification delivery via WebSocket or polling. Connect to backend notification API.

### MF-H5: No Feature Flag Management UI
**Location**: `frontend/lib/navigation.ts` (accepts feature flags)
**Description**: The navigation engine accepts feature flags but there is no UI for platform admins to manage them. The backend has `platform_features` module.
**Required for**: Progressive rollout, A/B testing, platform control.
**Fix**: Add feature flag management UI in admin portal.

### MF-H6: No API Key Management UI
**Location**: `frontend/app/(app)/api-keys/`
**Description**: Page exists but has no functional UI for creating, viewing, or revoking API keys. The backend has `APIToken` model and encryption support.
**Required for**: Developer integration, API access management.
**Fix**: Build API key management UI with create/list/revoke functionality.

### MF-H7: No Webhook Management UI
**Location**: `frontend/app/(app)/webhooks/`
**Description**: Page exists but has no functional UI. Backend has webhook routes in `ecosystem/webhook_routes.py`.
**Required for**: Integration, automation.
**Fix**: Build webhook management UI.

### MF-H8: No Billing/Subscription Management UI
**Location**: `frontend/app/(app)/billing/`
**Description**: Page exists but has no functional UI. Backend has SaaS subscription and billing routes.
**Required for**: SaaS monetization, plan management.
**Fix**: Build billing UI showing current plan, usage, invoices, and upgrade options.

---

## MEDIUM

### MF-M1: No Data Export/Download
**Location**: `frontend/app/(app)/datasets/`
**Description**: Users can upload datasets but cannot download or export them. No CSV/Excel export endpoint in the frontend.
**Required for**: Data portability, offline analysis.
**Fix**: Add export/download buttons on dataset detail page.

### MF-M2: No Report Scheduling UI
**Location**: `frontend/app/(app)/scheduler/`
**Description**: Page exists but has no UI for scheduling reports. Backend has `scheduler/routes.py` with full scheduling support.
**Required for**: Automated reporting, enterprise workflows.
**Fix**: Build report scheduler UI.

### MF-M3: No User Invitation Flow (Frontend)
**Location**: `frontend/app/invite/`
**Description**: Invite page exists but may not be fully functional. Backend has `invitation_routes.py` with full invitation support.
**Required for**: Organization onboarding, team building.
**Fix**: Complete invitation flow UI: send invite → accept → signup → join org.

### MF-M4: No Data Lineage Visualization
**Location**: `etl/` module
**Description**: Backend has ETL lineage tracking but no frontend visualization.
**Required for**: Data governance, impact analysis.
**Fix**: Add data lineage graph visualization.

### MF-M5: No Audit Log Export
**Location**: `frontend/app/(app)/audit/`
**Description**: Audit logs can be viewed but not exported. Compliance often requires audit log export.
**Required for**: Compliance, external auditing.
**Fix**: Add CSV/PDF export for audit logs.

### MF-M6: No Two-Factor Authentication (2FA)
**Location**: `authentication/`
**Description**: No 2FA/MFA support. JWT-only authentication.
**Required for**: Enterprise security, compliance (HIPAA, SOC 2).
**Fix**: Add TOTP-based 2FA with recovery codes.

### MF-M7: No Session Management UI
**Location**: `frontend/app/(app)/settings/`
**Description**: Backend tracks sessions (IP, user agent, device) but no UI shows active sessions.
**Required for**: Security awareness, session revocation.
**Fix**: Add active sessions panel in settings with revoke buttons.

---

## LOW

### MF-L1: No Dark Mode Toggle in Settings
**Location**: `frontend/components/layout/TopNav.tsx`
**Description**: Theme toggle exists in TopNav but not in settings page.
**Fix**: Add theme preference in settings.

### MF-L2: No Language/Localization Support
**Location**: `frontend/`
**Description**: All strings are hardcoded in English. The `User` model has `language` field but no i18n.
**Fix**: Add next-intl or similar i18n framework.

### MF-L3: No Keyboard Shortcuts Documentation
**Location**: `frontend/`
**Description**: `⌘K` opens search but no documentation or help panel lists available shortcuts.
**Fix**: Add keyboard shortcuts overlay.

### MF-L4: No Onboarding Completion Tracking
**Location**: `frontend/app/onboarding/`
**Description**: The `AdaptiveOnboarding` component exists but is not connected to the `onboarding_completed` field on the `User` model.
**Fix**: Mark onboarding complete in backend when flow finishes.

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 8 |
| Medium | 7 |
| Low | 4 |
| **Total** | **22** |
