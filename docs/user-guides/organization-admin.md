# Organization Admin Guide

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Technical Writer

---

## Purpose

Guide for Organization Administrators (org_admin role).

## Scope

All features available to org admins within their organization.

## Audience

Organization administrators.

---

## 1. Overview

As an Organization Admin, you manage users, settings, and data within your organization. You cannot access other organizations.

## 2. Key Capabilities

- Manage users in your org (create, edit, delete)
- Invite new users with specific roles
- Assign roles (except `super_admin` and `org_owner`)
- Manage departments
- View audit logs for your org
- Configure organization settings
- Manage datasets, dashboards, and reports

## 3. User Management

Navigate to `/admin` to manage users.

### Invite Users
1. Go to Members page
2. Click "Invite User"
3. Enter email and select role
4. Invitation sent with 7-day expiry
5. User must accept with matching email

### Assign Roles
1. Go to user profile
2. Select roles to assign
3. Cannot assign `super_admin` or `org_owner`

### Delete Users
1. Go to user profile
2. Click "Delete" (soft delete)
3. User sessions revoked

## 4. Department Management

Navigate to Settings → Departments.

- Create departments for your org
- Assign users to departments
- Department managers can oversee department operations

## 5. Audit Logs

Navigate to `/audit` to view org activity.

- Filter by action type, user, date
- All critical actions are logged
- Export for compliance reports

## 6. Settings

Navigate to `/settings` for:
- Profile settings
- Appearance (theme)
- Security (password, sessions)
- Organization settings
- Notification preferences

## Related Documents

- [../governance/roles.md](../governance/roles.md) — Role definitions
- [../workflows/user-journeys.md](../workflows/user-journeys.md) — Org Admin journey
- [../governance/organization-model.md](../governance/organization-model.md) — Org model
