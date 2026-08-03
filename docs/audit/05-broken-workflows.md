# Broken Workflows

## Overview

User workflows that are broken, incomplete, or non-functional, identified during the system audit.

---

## CRITICAL

### BW-C1: Audit Page Crashes on Data Load
**Location**: `frontend/app/(app)/audit/page.tsx:42-43`
**Description**: The audit page calls `apiClient.get<AuditLog[]>('/audit/logs')` but the backend returns `{ logs: [...], total, page, page_size }`. The code then calls `logs.filter()` on the response object, which is not an array.
**Status**: **Partially fixed** — we patched this to extract `data.logs`, but the root cause (inconsistent API response format) remains.
**Impact**: Auditors cannot view audit logs. Complete workflow failure.
**Root Cause**: Backend returns paginated dict, frontend expects plain array.

### BW-C2: Search Returns 404
**Location**: `frontend/components/adaptive/AdaptiveSearch.tsx:94`
**Description**: The `AdaptiveSearch` component routes to `/search?q=` but no `/search` page exists. Users get a 404 error.
**Impact**: Search is completely non-functional. Users cannot find datasets, dashboards, or reports.
**Fix**: Create `/search` page.

### BW-C3: Onboarding Flow Not Connected
**Location**: `frontend/app/onboarding/page.tsx`
**Description**: The existing onboarding page uses a static 6-step flow. The new `AdaptiveOnboarding` component exists but is not used. The onboarding completion is not tracked in the backend (`onboarding_completed` field on User model).
**Impact**: All users see the same generic onboarding regardless of role. Onboarding state is lost.
**Fix**: Replace onboarding page with `AdaptiveOnboarding`. Connect to backend completion endpoint.

---

## HIGH

### BW-H1: Notifications Always Show "No new notifications"
**Location**: `frontend/components/layout/TopNav.tsx`
**Description**: The TopNav notification dropdown is static. It shows "No new notifications" regardless of actual notification state. The backend has a notifications API but the TopNav does not call it.
**Impact**: Users miss important notifications. Workflow appears broken.
**Fix**: Connect TopNav notifications to `/notifications` API endpoint with polling.

### BW-H2: Demo Page Form Has No Backend Integration
**Location**: `frontend/app/demo/page.tsx:23-27`
**Description**: The demo booking form simulates submission with `setTimeout(r, 1500)` and does not call any backend API. Demo requests are not stored or sent.
**Impact**: All demo requests are lost. Sales team has no visibility.
**Fix**: Create backend endpoint for demo requests and connect form.

### BW-H3: Contact Page Form Has No Backend Integration
**Location**: `frontend/app/contact/page.tsx:20-27`
**Description**: Same as demo page — contact form simulates submission without backend integration.
**Impact**: Contact messages are lost.
**Fix**: Create backend endpoint for contact messages.

### BW-H4: Settings Pages May Be Incomplete
**Location**: `frontend/app/(app)/settings/`
**Description**: Settings page exists with 11 component files in `components/settings/` but the completeness of each settings panel has not been verified.
**Impact**: Users may encounter incomplete or broken settings panels.
**Fix**: Audit each settings panel for completeness.

### BW-H5: API Keys Page Has No Functionality
**Location**: `frontend/app/(app)/api-keys/`
**Description**: Page exists but has no functional content. No API key creation, listing, or revocation.
**Impact**: Users cannot manage API keys. Developer integration blocked.
**Fix**: Build API key management UI.

### BW-H6: Webhooks Page Has No Functionality
**Location**: `frontend/app/(app)/webhooks/`
**Description**: Page exists but has no functional content.
**Impact**: Users cannot configure webhooks. Integration blocked.
**Fix**: Build webhook management UI.

---

## MEDIUM

### BW-M1: Billing Page Has No Functionality
**Location**: `frontend/app/(app)/billing/`
**Description**: Page exists but has no functional content. Backend has SaaS subscription routes.
**Impact**: Users cannot view or manage subscriptions.
**Fix**: Build billing UI.

### BW-M2: Scheduler Page Has No Functionality
**Location**: `frontend/app/(app)/scheduler/`
**Description**: Page exists but has no functional content. Backend has scheduler routes.
**Impact**: Users cannot schedule reports.
**Fix**: Build scheduler UI.

### BW-M3: Marketplace Page Has No Functionality
**Location**: `frontend/app/(app)/marketplace/`
**Description**: Page exists but has no functional content. Backend has ecosystem marketplace routes.
**Impact**: Users cannot browse or install marketplace items.
**Fix**: Build marketplace UI.

### BW-M4: Connectors Page Has No Functionality
**Location**: `frontend/app/(app)/connectors/`
**Description**: Page exists but has no functional content. Backend has connector routes.
**Impact**: Users cannot configure data connectors.
**Fix**: Build connectors UI.

### BW-M5: Templates Page Has No Functionality
**Location**: `frontend/app/(app)/templates/`
**Description**: Page exists but has no functional content.
**Impact**: Users cannot browse or use templates.
**Fix**: Build templates UI.

### BW-M6: Duplicate Root Route Definitions
**Location**: `api/main.py:425-432, 702-710`
**Description**: Two `@app.get("/")` endpoints are defined — one serving the landing page (line 425) and one returning API info (line 702). FastAPI will use the first registered route, making the second dead code.
**Impact**: Confusion, dead code.
**Fix**: Remove the duplicate root endpoint.

---

## LOW

### BW-L1: Feedback Page Status Unknown
**Location**: `frontend/app/feedback/`
**Description**: Page exists but completeness is unknown.
**Fix**: Verify feedback page functionality.

### BW-L2: Help Page Status Unknown
**Location**: `frontend/app/help/`
**Description**: Page exists but may duplicate the `AdaptiveHelp` component in TopNav.
**Fix**: Consolidate help into one consistent experience.

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 6 |
| Medium | 6 |
| Low | 2 |
| **Total** | **17** |
