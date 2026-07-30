# Frontend Navigation Matrix

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active

---

## Overview

This document defines the visibility rules for every navigation item and page in the DataFlow frontend. Navigation visibility is controlled by the `Sidebar` component (`frontend/components/layout/Sidebar.tsx`) using `hasPermission()` and `hasRole()` from the auth store.

---

## Sidebar Navigation Groups

### Overview Group

| Nav Item | Route | Permission Required | Role Required | Visible To |
|----------|-------|---------------------|---------------|------------|
| Dashboard | `/dashboard` | None | None | All authenticated users |
| Studios | `/studios` | None | None | All authenticated users |
| Templates | `/templates` | None | None | All authenticated users |

### Data Group

| Nav Item | Route | Permission Required | Role Required | Visible To |
|----------|-------|---------------------|---------------|------------|
| Smart Capture | `/capture` | None | None | All authenticated users |
| Datasets | `/datasets` | `datasets.view` | None | All except pure viewer (no datasets.view) |
| Analytics | `/analytics` | `analytics.view` | None | Analysts, managers, admins |
| Reports | `/reports` | `reports.view` | None | Analysts, managers, admins |

### Intelligence Group

| Nav Item | Route | Permission Required | Role Required | Visible To |
|----------|-------|---------------------|---------------|------------|
| Analytics Assistant | `/ai` | `ai.use` | None | Users with AI access |
| Scheduler | `/scheduler` | None | None | All authenticated users |

### Administration Group

| Nav Item | Route | Permission Required | Role Required | Visible To |
|----------|-------|---------------------|---------------|------------|
| Notifications | `/notifications` | None | None | All authenticated users |
| Members | `/admin` | `users.read` | None | Org admins, dept managers, auditors |
| Admin Portal | `/admin-portal` | None | `super_admin` | Platform Owner only |
| Audit Logs | `/audit` | `audit.view` | None | Auditors, org admins, super admins |

### Platform Group

| Nav Item | Route | Permission Required | Role Required | Visible To |
|----------|-------|---------------------|---------------|------------|
| Billing | `/billing` | None | None | All authenticated users (placeholder) |
| Connectors | `/connectors` | None | None | All authenticated users (placeholder) |
| Marketplace | `/marketplace` | None | None | All authenticated users (placeholder) |
| API Keys | `/api-keys` | None | None | All authenticated users (future) |
| Webhooks | `/webhooks` | None | None | All authenticated users (placeholder) |
| Settings | `/settings` | None | None | All authenticated users |

---

## Page-Level Access Control

### Public Pages (No Authentication)

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Marketing landing page |
| Login | `/login` | Login form |
| Signup | `/signup` | Multi-mode registration |
| Invite Accept | `/invite` | Invitation acceptance page |
| Forgot Password | `/forgot-password` | Password reset request |
| Reset Password | `/reset-password` | Password reset form |
| About | `/about` | About page |
| Features | `/features` | Feature showcase |
| Pricing | `/pricing` | Pricing plans |
| Solutions | `/solutions` | Solutions overview |
| Industries | `/industries` | Industry showcase |
| Contact | `/contact` | Contact form |
| Help | `/help` | Help center |
| Feedback | `/feedback` | Feedback form |
| Privacy | `/privacy` | Privacy policy |
| Terms | `/terms` | Terms of service |

### Authenticated Pages (App Layout)

| Page | Route | Permission | Role | Notes |
|------|-------|------------|------|-------|
| Dashboard | `/dashboard` | None | None | Welcome screen with stats |
| Onboarding | `/onboarding` | None | None | First-time setup wizard |
| Studios | `/studios` | None | None | Industry studio cards |
| Templates | `/templates` | None | None | Template library |
| Smart Capture | `/capture` | None | None | Document upload + OCR |
| Datasets | `/datasets` | `datasets.view` | None | Dataset list + management |
| Analytics | `/analytics` | `analytics.view` | None | Dashboard builder |
| Reports | `/reports` | `reports.view` | None | Report list + generation |
| AI Assistant | `/ai` | `ai.use` | None | Conversational analytics |
| Scheduler | `/scheduler` | None | None | Pipeline scheduling (placeholder) |
| Notifications | `/notifications` | None | None | User notifications |
| Members | `/admin` | `users.read` | None | User management |
| Admin Portal | `/admin-portal` | None | `super_admin` | Platform-wide admin |
| Audit Logs | `/audit` | `audit.view` | None | Audit log viewer |
| Settings | `/settings` | None | None | Settings tabs (filtered by permission) |
| Billing | `/billing` | None | None | Billing placeholder |
| Connectors | `/connectors` | None | None | Integration connectors (placeholder) |
| Marketplace | `/marketplace` | None | None | Extension marketplace (placeholder) |
| API Keys | `/api-keys` | None | None | API key management (future) |
| Webhooks | `/webhooks` | None | None | Webhook configuration (placeholder) |
| Workflows | `/workflows` | None | None | ETL workflow list |
| Forbidden | `/forbidden` | None | None | 403 error page |
| Offline | `/offline` | None | None | Offline indicator |

### Settings Tabs (Permission-Filtered)

| Tab | Permission Required | Role Required | Visible To |
|-----|---------------------|---------------|------------|
| Profile | `profile.update` | None | All users |
| Appearance | None | None | All users |
| Security | None | None | All users |
| Notifications | `notifications.manage` | None | Users with notification access |
| Organization | `organizations.manage` | None | Org admins, super admins |
| Departments | `departments.manage` | None | Dept managers, org admins |
| Users | `users.read` | None | Users with read access |
| Roles | `roles.read` | None | Users with role read access |
| Sessions | `sessions.manage` | None | Users with session management |
| Audit | `audit.view` | None | Auditors, admins |

---

## Role-to-Navigation Mapping

### Platform Owner (`super_admin`)

- **All sidebar items visible** including Admin Portal
- **All settings tabs visible**

### Organization Administrator (`org_admin`)

- **Visible**: Dashboard, Studios, Templates, Smart Capture, Datasets, Analytics, Reports, AI Assistant, Scheduler, Notifications, Members, Audit Logs, Billing, Connectors, Marketplace, API Keys, Webhooks, Settings
- **Hidden**: Admin Portal (super_admin only)
- **Settings tabs**: All except those requiring `settings.manage`

### Department Manager (`dept_manager`)

- **Visible**: Dashboard, Studios, Templates, Smart Capture, Datasets, Analytics, Reports, Scheduler, Notifications, Members, Settings
- **Hidden**: AI Assistant (no `ai.use`), Audit Logs (no `audit.view`), Admin Portal
- **Settings tabs**: Profile, Appearance, Security, Notifications

### Data Analyst (`data_analyst`)

- **Visible**: Dashboard, Studios, Templates, Datasets, Analytics, Reports, Scheduler, Notifications, Settings
- **Hidden**: Smart Capture (no `datasets.upload`), AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Business Analyst (`business_analyst`)

- **Visible**: Dashboard, Studios, Templates, Datasets, Analytics, Reports, Scheduler, Notifications, Settings
- **Hidden**: Smart Capture, AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Executive (`executive`)

- **Visible**: Dashboard, Studios, Templates, Analytics, Reports, Scheduler, Notifications, Settings
- **Hidden**: Datasets, Smart Capture, AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Data Entry Officer (`data_entry_officer`)

- **Visible**: Dashboard, Studios, Templates, Smart Capture, Datasets, Scheduler, Notifications, Settings
- **Hidden**: Analytics, Reports, AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Researcher (`researcher`)

- **Visible**: Dashboard, Studios, Templates, Smart Capture, Datasets, Analytics, Reports, Scheduler, Notifications, Settings
- **Hidden**: AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Auditor (`auditor`)

- **Visible**: Dashboard, Studios, Templates, Scheduler, Notifications, Members, Audit Logs, Settings
- **Hidden**: Smart Capture, Datasets, Analytics, Reports, AI Assistant, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Viewer (`viewer`)

- **Visible**: Dashboard, Studios, Templates, Scheduler, Notifications, Settings
- **Hidden**: Smart Capture, Datasets, Analytics, Reports, AI Assistant, Members, Audit Logs, Admin Portal
- **Settings tabs**: Profile, Appearance, Security

### Personal Workspace User (`viewer`, no org)

- **Visible**: Dashboard, Studios, Templates, Smart Capture, Scheduler, Notifications, Settings
- **Hidden**: All org-scoped items (Members, Audit Logs, Admin Portal)
- **Settings tabs**: Profile, Appearance, Security

---

## Route Guard Implementation

Frontend route protection is implemented via:
- **`RouteGuard` component** (`frontend/components/auth/RouteGuard.tsx`) — wraps pages with auth + permission checks
- **`Can` component** (`frontend/components/auth/Can.tsx`) — conditionally renders UI elements based on permissions
- **`useAuthStore` hook** (`frontend/stores/authStore.ts`) — provides `hasPermission()` and `hasRole()` functions

### RouteGuard Logic

```
if (!isAuthenticated) → redirect to /login
if (permission && !hasPermission(permission)) → redirect to /forbidden
if (role && !hasRole(role)) → redirect to /forbidden
```

### Can Component Logic

```
if (permission) → check hasPermission(permission)
if (permissions) → check all/any (based on requireAll flag)
if (!allowed) → render fallback
if (allowed) → render children
```

---

## Cross-References

- **Sidebar implementation**: `frontend/components/layout/Sidebar.tsx`
- **RouteGuard**: `frontend/components/auth/RouteGuard.tsx`
- **Can component**: `frontend/components/auth/Can.tsx`
- **Auth store**: `frontend/stores/authStore.ts`
- **Permission constants**: `frontend/lib/permissions.ts`
