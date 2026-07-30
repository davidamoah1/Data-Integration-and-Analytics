# Integration Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: QA Lead

---

## Purpose

Integration testing guide for API endpoints and database interactions.

## Scope

Tests that verify multiple components work together.

## Audience

Backend developers and QA engineers.

---

## 1. Framework

- **pytest** with FastAPI `TestClient`
- Database: In-memory SQLite or test PostgreSQL
- Run: `pytest tests/integration/`

## 2. Test Areas

| Area | Description | Key Tests |
|------|-------------|-----------|
| Auth flow | Login → API call → logout | Token lifecycle |
| RBAC | Permission enforcement on endpoints | 403 for missing permissions |
| Tenant isolation | Cross-org access prevention | 403 for cross-org |
| User management | Create → assign role → list | Org-scoped listing |
| Invitation flow | Create → accept → login | Email match, expiry |
| Organization CRUD | Create → update → delete | Org access checks |

## 3. Test Pattern

```python
def test_user_cannot_access_other_org(client, auth_headers):
    """Non-super-admin cannot access other org's users."""
    response = client.get(
        f"/api/users?organization_id={other_org_id}",
        headers=auth_headers
    )
    assert response.status_code == 403
```

## 4. Test Database

- Use separate test database or in-memory SQLite
- Tables created fresh per test session
- Seed minimal data (roles, permissions, test users)
- Clean up between tests

## Related Documents

- [unit-tests.md](unit-tests.md) — Unit tests
- [e2e-tests.md](e2e-tests.md) — E2E tests
- [security-tests.md](security-tests.md) — Security tests
