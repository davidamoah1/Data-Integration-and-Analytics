# Maintenance Guidelines

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active

---

## Overview

These guidelines ensure governance documentation remains synchronized with the source code. **No implementation should proceed without keeping these documents synchronized with the codebase.**

---

## 1. When to Update Documentation

### Permission Matrix (`permission-matrix.md`, `permission-matrix.json`)

Update when:
- A new permission is added to `authentication/services.py:seed_default_data()`
- A new role is created (system or custom)
- A role's permissions are changed
- A new module is added to the platform
- `frontend/lib/permissions.ts` is modified

### API Authorization Matrix (`api-authorization-matrix.md`)

Update when:
- A new API endpoint is added
- An endpoint's required permission changes
- An endpoint's org scope changes
- A new router is registered in `api/main.py`

### Frontend Navigation Matrix (`frontend-navigation-matrix.md`)

Update when:
- A new page is added to `frontend/app/`
- A sidebar item is added, removed, or modified in `Sidebar.tsx`
- A settings tab is added or its permission changes
- A `RouteGuard` or `Can` component's permission/role check changes

### User Journeys (`user-journeys.md`)

Update when:
- A new role is introduced
- A registration mode is added or changed
- A significant UX flow changes (onboarding, dashboard, settings)
- Error handling or empty states are modified

### ADRs (`adr/`)

- **Existing ADRs**: Do not modify accepted ADRs. If a decision changes, create a new ADR that supersedes the old one and update the old ADR's status to "Superseded by ADR-XXXX".
- **New ADRs**: Create when a significant architectural decision is made. Use the next available number.

---

## 2. Update Process

### Step 1: Make Code Changes
Implement the feature, permission, or architectural change in the source code.

### Step 2: Update Documentation
Update all relevant governance documents to reflect the changes.

### Step 3: Update JSON
If permissions or roles changed, update `permission-matrix.json` to match.

### Step 4: Verify Consistency
Check that:
- Permission strings in documentation match `frontend/lib/permissions.ts` and `authentication/services.py`
- Role names in documentation match `frontend/lib/permissions.ts` and `platform_features/rbac.py`
- API paths in documentation match actual route definitions
- Frontend routes in documentation match `frontend/app/` structure

### Step 5: Commit Together
Commit documentation updates in the same commit or PR as the code changes.

---

## 3. Review Checklist

Before merging any PR that affects permissions, roles, or architecture:

- [ ] `permission-matrix.md` updated with any new permissions or roles
- [ ] `permission-matrix.json` updated to match
- [ ] `api-authorization-matrix.md` updated for new/changed endpoints
- [ ] `frontend-navigation-matrix.md` updated for new/changed pages or nav items
- [ ] `user-journeys.md` updated if user flows changed
- [ ] New ADR created if architectural decision was made
- [ ] All permission strings are consistent across frontend and backend
- [ ] All role names are consistent across frontend and backend

---

## 4. Naming Conventions

### Permissions
- Format: `module.action` (e.g., `datasets.upload`, `reports.export`)
- Lowercase, dot-separated
- Must match between `frontend/lib/permissions.ts` and `authentication/services.py`

### Roles
- Format: `snake_case` (e.g., `super_admin`, `org_admin`, `data_analyst`)
- Must match between `frontend/lib/permissions.ts:ROLES` and `platform_features/rbac.py:ROLE_HIERARCHY`

### ADRs
- Format: `ADR-XXXX-descriptive-title.md` (e.g., `ADR-0001-enterprise-multi-tenant-architecture.md`)
- Sequential numbering starting from 0001
- Kebab-case for filename

### Documentation Files
- Markdown format (`.md`)
- Machine-readable files use JSON (`.json`)
- All files in `docs/governance/` directory

---

## 5. Version Control

- All governance documents are version-controlled in the repository
- Each document has a version number and last-updated date in its header
- Major changes should increment the version number
- Use semantic versioning: `MAJOR.MINOR.PATCH`
  - MAJOR: Architectural change (new ADR, permission model redesign)
  - MINOR: New permissions, roles, or modules added
  - PATCH: Corrections, clarifications, or minor updates

---

## 6. Ownership

- **Architecture Board**: Owns ADRs and governance summary
- **Backend Team**: Owns API authorization matrix, permission matrix (backend accuracy)
- **Frontend Team**: Owns frontend navigation matrix, user journeys (UX accuracy)
- **Security Team**: Owns permission restrictions, audit logging ADR
- **Product Manager**: Owns user journeys, role definitions

All changes require review by at least one team owner before merging.
