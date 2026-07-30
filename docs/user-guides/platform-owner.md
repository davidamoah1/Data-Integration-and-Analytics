# Platform Owner Guide

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Technical Writer

---

## Purpose

Guide for Platform Owners (super_admin role).

## Scope

All features available to platform owners.

## Audience

Platform owners and super administrators.

---

## 1. Overview

As a Platform Owner, you have full access to all organizations, users, and system settings. You are the highest authority in the platform.

## 2. Key Capabilities

- Access all organizations (cross-tenant)
- Manage all users across all orgs
- Suspend and activate organizations
- View all audit logs
- Manage system roles and permissions
- Access the Admin Portal

## 3. Admin Portal

Navigate to `/admin-portal` (visible only to `super_admin` role).

### Features
- View all organizations
- Suspend/activate organizations
- View platform-wide statistics
- Manage system-wide settings

## 4. User Management

- View all users across all orgs
- Create users in any org
- Assign any role including `super_admin` and `org_owner`
- Delete users

## 5. Audit Logs

- View audit logs for all organizations
- Filter by action, user, date range
- Export audit data

## 6. Important Notes

- All your actions are audit-logged
- You bypass all permission checks — exercise caution
- You can access any organization's data
- Role assignment to `super_admin` should be rare and deliberate

## Related Documents

- [../governance/roles.md](../governance/roles.md) — Role definitions
- [../workflows/user-journeys.md](../workflows/user-journeys.md) — Platform Owner journey
- [../governance/security-model.md](../governance/security-model.md) — Security model
