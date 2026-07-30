# Contributor Documentation Checklist

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Owner**: Technical Writing Team

---

## Purpose

A checklist for contributors to ensure documentation is complete when making code changes.

## Scope

All PRs that modify the DataFlow codebase.

## Audience

All contributors.

---

## Pre-PR Checklist

### General

- [ ] I have read the [STYLE_GUIDE.md](STYLE_GUIDE.md)
- [ ] I have read the [MAINTENANCE_POLICY.md](MAINTENANCE_POLICY.md)
- [ ] My documentation updates are in the same PR as code changes

### If I added a new API endpoint

- [ ] Updated [backend/endpoints.md](backend/endpoints.md) with the new endpoint
- [ ] Updated [api/openapi.md](api/openapi.md) if applicable
- [ ] Added request/response example to [api/examples.md](api/examples.md)
- [ ] Updated [governance/api-authorization-matrix.md](governance/api-authorization-matrix.md) if auth changed

### If I added a new permission

- [ ] Updated [governance/permission-matrix.md](governance/permission-matrix.md)
- [ ] Updated [governance/permission-matrix.json](governance/permission-matrix.json)
- [ ] Updated `frontend/lib/permissions.ts` (source code)
- [ ] Updated `authentication/services.py:seed_default_data()` (source code)
- [ ] Updated [governance/authorization.md](governance/authorization.md) if enforcement changed

### If I added a new role

- [ ] Updated [governance/roles.md](governance/roles.md)
- [ ] Updated [governance/permission-matrix.md](governance/permission-matrix.md)
- [ ] Updated [governance/permission-matrix.json](governance/permission-matrix.json)
- [ ] Added a user guide in [user-guides/](user-guides/)
- [ ] Updated [governance/frontend-navigation-matrix.md](governance/frontend-navigation-matrix.md)
- [ ] Updated [workflows/user-journeys.md](workflows/user-journeys.md)

### If I added a new database table

- [ ] Updated [database/schema.md](database/schema.md)
- [ ] Updated [database/entity-relationship.md](database/entity-relationship.md)
- [ ] Updated [database/migrations.md](database/migrations.md) if migration needed

### If I added a new frontend page

- [ ] Updated [frontend/routing.md](frontend/routing.md)
- [ ] Updated [frontend/navigation.md](frontend/navigation.md) if sidebar changed
- [ ] Updated [governance/frontend-navigation-matrix.md](governance/frontend-navigation-matrix.md)
- [ ] Added appropriate `RouteGuard` permission/role check

### If I made an architectural decision

- [ ] Created a new ADR in [architecture/adr/](architecture/adr/)
- [ ] Updated [architecture/overview.md](architecture/overview.md) if high-level changed
- [ ] Updated [architecture/system-design.md](architecture/system-design.md) if components changed
- [ ] Updated relevant ADR cross-references

### If I added a new module or studio

- [ ] Created documentation in [studios/](studios/)
- [ ] Updated [product/feature-catalog.md](product/feature-catalog.md)
- [ ] Updated [architecture/component-diagram.md](architecture/component-diagram.md)

### If I changed deployment

- [ ] Updated [deployment/](deployment/) docs
- [ ] Updated [deployment/environments.md](deployment/environments.md) if env vars changed
- [ ] Updated [architecture/deployment-architecture.md](architecture/deployment-architecture.md)

### If I changed security

- [ ] Updated [governance/security-model.md](governance/security-model.md)
- [ ] Updated [governance/compliance-notes.md](governance/compliance-notes.md) if compliance affected
- [ ] Updated [testing/security-tests.md](testing/security-tests.md) if test approach changed

---

## Post-PR Checklist

- [ ] All internal links in changed documents are valid
- [ ] Document version numbers incremented
- [ ] `Last Updated` dates updated
- [ ] No placeholder content remains
- [ ] Mermaid diagrams render correctly (if added)
- [ ] Terminology matches [STYLE_GUIDE.md](STYLE_GUIDE.md)
