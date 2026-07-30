# Role-to-Navigation Mapping

## Overview

This document describes the adaptive navigation system that dynamically generates sidebar menus, dashboard widgets, quick actions, onboarding flows, help content, search scopes, and notification types based on the user's role, permissions, workspace type, and feature flags.

## Architecture

```
User Auth State (roles, permissions)
         │
         ▼
┌─────────────────────┐
│  navigation.ts      │──→ buildNavigation() ──→ Sidebar
│  dashboards.ts      │──→ getDashboardConfig() ──→ AdaptiveDashboard
│  onboarding.ts      │──→ getOnboardingFlow() ──→ AdaptiveOnboarding
│  help.ts            │──→ getHelpConfig() ──→ AdaptiveHelp
│  search.ts          │──→ getSearchConfig() ──→ AdaptiveSearch
│  notifications.ts   │──→ getNotificationTypes() ──→ NotificationSettings
└─────────────────────┘
```

## Primary Role Resolution

When a user has multiple roles, the system selects a **primary role** by priority:

1. `super_admin` — Platform Owner
2. `org_owner` — Organization Owner
3. `org_admin` — Organization Administrator
4. `dept_manager` — Department Manager
5. `auditor` — Auditor
6. `data_engineer` — Data Engineer
7. `data_analyst` — Data Analyst
8. `researcher` — Researcher
9. `business_analyst` — Business Analyst
10. `executive` — Executive
11. `dept_officer` — Department Officer
12. `data_entry_officer` — Data Entry Officer
13. `viewer` — Viewer

## Role-to-Navigation Mapping

### Super Admin (`super_admin`)

| Group | Items |
|-------|-------|
| Platform | Dashboard, Platform Analytics, Monitoring, Security |
| Administration | Admin Portal, Members, Audit Logs, Feature Flags, Platform Settings |
| Platform Tools | Studios, Templates, Connectors, Marketplace, API Keys, Webhooks, Billing |
| System | Notifications, Settings |

**Dashboard**: Platform health KPIs, system status, global analytics
**Quick Actions**: View Organizations, Audit Center, Feature Flags
**Onboarding**: Platform configuration (review orgs, feature flags, security)
**Help**: Platform management, system operations
**Search Scopes**: Organizations, Users, Datasets, Dashboards, Reports, Audit Logs
**Notifications**: Organization activity, security alerts, platform incidents, audit exports, system maintenance

### Organization Owner (`org_owner`)

| Group | Items |
|-------|-------|
| Overview | Dashboard, Studios, Templates |
| Data | Smart Capture, Datasets, Analytics, Reports |
| Intelligence | AI Assistant, Scheduler |
| Administration | Notifications, Members, Departments, Audit Logs |
| Platform | Connectors, Settings |

**Dashboard**: Org KPIs (members, departments, datasets, storage), member activity, data status
**Quick Actions**: Invite Member, Create Department, Upload Dataset, Create Dashboard, Generate Report
**Onboarding**: Organization setup (invite, departments, upload, dashboard)
**Help**: Organization setup, data management
**Search Scopes**: Members, Datasets, Dashboards, Reports, Departments
**Notifications**: Org activity, dataset uploads, report generation, invitations, security alerts, system maintenance

### Organization Admin (`org_admin`)

Same navigation as `org_owner`.

### Department Manager (`dept_manager`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Department | Members, Datasets, Reports |
| Intelligence | Analytics, AI Assistant |
| Personal | Notifications, Profile |

**Dashboard**: Department KPIs (team size, datasets, reports, pending reviews), team activity
**Quick Actions**: Upload Dataset, Create Dashboard, Generate Report
**Onboarding**: Department setup (review team, upload, dashboard)
**Help**: Department management, data & analytics
**Search Scopes**: Datasets, Dashboards, Reports
**Notifications**: Department activity, dataset uploads/processing, report generation, capture review

### Data Engineer (`data_engineer`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Data | Datasets, Connectors, Scheduler |
| Intelligence | Analytics, AI Assistant |
| Personal | Notifications, Profile |

**Dashboard**: Pipeline status (active pipelines, datasets, jobs, connectors), job history
**Quick Actions**: Upload Dataset, Connect Database, Schedule Pipeline
**Onboarding**: Engineering setup (connect, upload, schedule)
**Help**: Data pipelines
**Search Scopes**: Datasets, Connectors
**Notifications**: Dataset uploads, pipeline failures/completions

### Data Analyst (`data_analyst`)

| Group | Items |
|-------|-------|
| Overview | Dashboard, Templates |
| Analytics Studio | Datasets, Analytics, Reports |
| Intelligence | AI Assistant, Scheduler |
| Personal | Notifications, Profile |

**Dashboard**: Data overview (datasets, processing, dashboards, reports), suggested analyses
**Quick Actions**: Upload Dataset, Run Validation, Create Dashboard, Generate Report
**Onboarding**: Analyst onboarding (upload, validate, dashboard, report)
**Help**: Data preparation, analysis & visualization
**Search Scopes**: Datasets, Dashboards, Reports, Templates
**Notifications**: Dataset uploads/processing, report generation/scheduling, dashboard sharing

### Business Analyst (`business_analyst`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Analytics | Analytics, Reports, Datasets |
| Intelligence | AI Assistant |
| Personal | Notifications, Profile |

**Dashboard**: Overview (dashboards, reports, datasets), recent insights
**Quick Actions**: View Dashboards, Generate Report
**Onboarding**: Business analytics onboarding (dashboards, reports, AI)
**Help**: Dashboards & reports
**Search Scopes**: Dashboards, Reports, Datasets
**Notifications**: Report generation, dashboard sharing

### Executive (`executive`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Insights | Analytics, Reports |
| Personal | Notifications, Profile |

**Dashboard**: Organization performance (dashboards, reports), recent reports
**Quick Actions**: View Dashboards, View Reports
**Onboarding**: Executive onboarding (dashboards, reports)
**Help**: Executive view
**Search Scopes**: Dashboards, Reports
**Notifications**: Report generation, dashboard sharing

### Researcher (`researcher`)

| Group | Items |
|-------|-------|
| Overview | Dashboard, Templates |
| Research Studio | Datasets, Statistics, Reports |
| Intelligence | AI Assistant, Scheduler |
| Personal | Notifications, Profile |

**Dashboard**: Research projects (projects, surveys, queue, publications)
**Quick Actions**: Import Survey, Run Analysis, Publication Report
**Onboarding**: Researcher onboarding (import, statistics, report)
**Help**: Research workflow
**Search Scopes**: Datasets, Reports
**Notifications**: Dataset uploads/processing, report generation/scheduling

### Auditor (`auditor`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Audit | Audit Logs, Members |
| Data | Datasets, Reports |
| Personal | Notifications, Profile |

**Dashboard**: Audit overview (logs, security events, users), recent audit events
**Quick Actions**: View Audit Logs, View Members
**Onboarding**: Auditor onboarding (audit logs, members)
**Help**: Audit & compliance
**Search Scopes**: Audit Logs, Users
**Notifications**: Security alerts, audit exports

### Department Officer (`dept_officer`)

| Group | Items |
|-------|-------|
| Overview | Dashboard |
| Data | Datasets, Reports |
| Personal | Notifications, Profile |

**Dashboard**: Overview (datasets, reports)
**Quick Actions**: Upload Dataset, View Reports
**Onboarding**: Department officer onboarding (datasets, reports)
**Help**: Data & reports
**Search Scopes**: Datasets, Reports
**Notifications**: Department activity, dataset processing, report generation

### Data Entry Officer (`data_entry_officer`)

| Group | Items |
|-------|-------|
| Capture | Smart Data Capture |
| Data | Datasets |
| Personal | Notifications, Profile |

**Dashboard**: Today's assignments (assignments, pending, queue, validation status)
**Quick Actions**: Capture Document, Review Records, Submit Data
**Onboarding**: Data capture onboarding (capture, review, submit)
**Help**: Smart data capture
**Search Scopes**: Datasets
**Notifications**: Capture assignments, capture review

### Viewer (`viewer`)

| Group | Items |
|-------|-------|
| View | Dashboard, Analytics, Reports |
| Personal | Notifications, Profile |

**Dashboard**: Favorite dashboards, recent reports
**Quick Actions**: View Dashboards, View Reports
**Onboarding**: Viewer onboarding (dashboards, reports)
**Help**: Viewing content
**Search Scopes**: Dashboards, Reports
**Notifications**: Report generation, dashboard sharing

## Permission Filtering

All navigation items, dashboard widgets, quick actions, and search scopes are filtered by permission:

- If an item has a `permission` property, the user must have that permission
- `super_admin` bypasses all permission checks
- Items without a `permission` property are visible to all authenticated users

## Workspace Type Filtering

When `workspaceType` is `'personal'`:
- Administration, Platform, and Platform Tools groups are hidden
- Items requiring `super_admin` role are hidden

## Feature Flag Filtering

Navigation items can be gated by feature flags:
- `/api-keys` → `api_keys` flag
- `/webhooks` → `webhooks` flag
- `/marketplace` → `marketplace` flag
- `/billing` → `billing` flag
- `/connectors` → `connectors` flag

If a flag is explicitly `false`, the corresponding navigation item is hidden.

## File Reference

| File | Purpose |
|------|---------|
| `frontend/lib/navigation.ts` | Dynamic navigation engine with role profiles |
| `frontend/lib/dashboards.ts` | Role-specific dashboard configurations |
| `frontend/lib/onboarding.ts` | Role-specific onboarding flows |
| `frontend/lib/help.ts` | Context-aware help configurations |
| `frontend/lib/search.ts` | Adaptive search scope configurations |
| `frontend/lib/notifications.ts` | Role-based notification type configurations |
| `frontend/components/layout/Sidebar.tsx` | Sidebar using `buildNavigation()` |
| `frontend/components/adaptive/AdaptiveDashboard.tsx` | Role-aware dashboard renderer |
| `frontend/components/adaptive/QuickActions.tsx` | Role-specific quick actions |
| `frontend/components/adaptive/AdaptiveEmptyState.tsx` | Role-aware empty states |
| `frontend/components/adaptive/AdaptiveSearch.tsx` | Permission-scoped search |
| `frontend/components/adaptive/AdaptiveHelp.tsx` | Context-aware help panel |
| `frontend/components/adaptive/AdaptiveOnboarding.tsx` | Role-specific onboarding flow |
| `frontend/components/auth/Can.tsx` | Permission-aware component renderer |
| `frontend/components/auth/RouteGuard.tsx` | Permission-aware route guard |
