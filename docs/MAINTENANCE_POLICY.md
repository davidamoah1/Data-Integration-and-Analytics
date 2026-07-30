# Documentation Maintenance Policy

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Owner**: Enterprise Architecture Board

---

## Purpose

Ensure documentation remains synchronized with the codebase throughout the product lifecycle.

## Scope

All files in the `/docs` directory and subdirectories.

## Audience

All contributors — developers, QA, product managers, DevOps.

---

## 1. Synchronization Rules

### Code changes that require documentation updates

| Code Change | Documentation to Update |
|-------------|----------------------|
| New API endpoint | `backend/endpoints.md`, `api/` docs |
| New permission | `governance/permission-matrix.md`, `governance/permission-matrix.json` |
| New role | `governance/roles.md`, `governance/permission-matrix.md`, `user-guides/` |
| New database table | `database/schema.md`, `database/entity-relationship.md` |
| New frontend page | `frontend/routing.md`, `frontend/navigation.md` |
| New sidebar item | `frontend/navigation.md`, `governance/frontend-navigation-matrix.md` |
| Architectural decision | New ADR in `architecture/adr/` |
| New module/studio | `studios/` docs, `product/feature-catalog.md` |
| New workflow | `workflows/` docs |
| New integration | `integrations/` docs |
| Deployment change | `deployment/` docs |
| Security change | `governance/security-model.md` |
| Environment variable change | `deployment/environments.md` |

### Commit Rule

**Documentation updates must be in the same commit or PR as the code changes.**

A PR without required documentation updates should be blocked in review.

---

## 2. Review Process

### PR Review Checklist

- [ ] All affected documentation files updated
- [ ] Version number incremented on changed documents
- [ ] `Last Updated` date updated
- [ ] Cross-references still valid
- [ ] No broken links
- [ ] Terminology consistent with [STYLE_GUIDE.md](STYLE_GUIDE.md)
- [ ] New features marked as planned if not yet implemented
- [ ] Mermaid diagrams updated if architecture changed

### Reviewer Responsibilities

- **Backend reviewer**: Verify `backend/`, `database/`, `api/` docs
- **Frontend reviewer**: Verify `frontend/`, `user-guides/` docs
- **Architecture reviewer**: Verify `architecture/`, ADRs
- **Security reviewer**: Verify `governance/security-model.md`, `governance/compliance-notes.md`
- **Product reviewer**: Verify `product/`, `user-guides/` docs

---

## 3. Update Cadence

| Document Type | Update Frequency |
|--------------|-----------------|
| ADRs | On architectural decision |
| Permission matrix | On permission/role change |
| API endpoints | On endpoint change |
| Database schema | On schema change |
| Release notes | On each release |
| User guides | On UX change |
| Deployment docs | On deployment change |
| Architecture overview | Quarterly review |
| Product roadmap | Monthly review |

---

## 4. Ownership

| Section | Owner | Reviewer |
|---------|-------|----------|
| `architecture/` | Enterprise Architect | CTO |
| `governance/` | Security Architect | CTO |
| `database/` | Database Architect | Backend Lead |
| `backend/` | Backend Lead | Enterprise Architect |
| `frontend/` | Frontend Lead | UX Designer |
| `studios/` | Product Manager | Solution Architect |
| `workflows/` | Product Manager | UX Designer |
| `integrations/` | DevOps Engineer | Backend Lead |
| `deployment/` | DevOps Engineer | CTO |
| `testing/` | QA Lead | Backend Lead |
| `operations/` | DevOps Engineer | CTO |
| `product/` | Product Manager | CTO |
| `user-guides/` | Technical Writer | Product Manager |
| `api/` | Backend Lead | Technical Writer |
| `release-notes/` | DevOps Engineer | Product Manager |

---

## 5. Deprecation

When a feature is deprecated:
1. Update the relevant document's status to `Deprecated`
2. Add a deprecation notice at the top
3. Link to the replacement document or feature
4. Keep the document for reference (do not delete)
5. Remove deprecated docs from the main navigation index

---

## 6. Automated Checks (Future)

> **⚠️ Planned**: The following automated checks are not yet implemented.

- CI pipeline validates all internal links in `/docs`
- CI pipeline checks for stale documents (not updated in 6 months)
- Pre-commit hook warns when code changes don't include doc changes
- Automated ADR numbering for new ADR files
