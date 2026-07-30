# Unit Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: QA Lead

---

## Purpose

Unit testing guide and conventions.

## Scope

Backend (pytest) and frontend (Vitest) unit tests.

## Audience

All developers.

---

## 1. Backend Unit Tests

### Framework

- **pytest** with fixtures
- Run: `pytest tests/`
- Test files: `tests/test_*.py`

### Conventions

- Test classes grouped by module: `TestAuth`, `TestUsers`, `TestOrganizations`
- Test methods: `test_<action>_<condition>`
- Use fixtures for database sessions and test users
- Mock external services

### Key Test Areas

| Area | File | Tests |
|------|------|-------|
| Authentication | `tests/test_auth.py` | Login, signup, token refresh |
| Users | `tests/test_users.py` | CRUD, role assignment |
| Organizations | `tests/test_orgs.py` | CRUD, scoping |
| Invitations | `tests/test_invitations.py` | Create, accept, revoke |
| Permissions | `tests/test_permissions.py` | RBAC checks |

## 2. Frontend Unit Tests

### Framework

- **Vitest** with React Testing Library
- Run: `cd frontend && npm test`
- Run once: `cd frontend && npm run test:run`
- Test files: `frontend/__tests__/*.test.ts(x)`

### Conventions

- Test files co-located with components or in `__tests__/`
- Use `render()`, `screen()`, `fireEvent()` from Testing Library
- Mock API calls with `vi.mock()`

### Key Test Areas

| Area | Tests |
|------|-------|
| Auth store | Login, logout, hasPermission, hasRole |
| RouteGuard | Permission check, redirect |
| Can component | Conditional rendering |
| Sidebar | Visibility logic |

## Related Documents

- [strategy.md](strategy.md) — Testing strategy
- [integration-tests.md](integration-tests.md) — Integration tests
