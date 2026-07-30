# End-to-End Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Planned  
> **Owner**: QA Lead

---

## Purpose

E2E testing guide for critical user flows.

## Scope

Browser-based tests simulating real user interactions.

## Audience

QA engineers and frontend developers.

---

> **⚠️ Planned**: E2E tests are not yet implemented. This document describes the planned approach.

## 1. Planned Framework

- **Playwright** for browser automation
- Run: `npx playwright test`
- Test files: `e2e/*.spec.ts`

## 2. Critical User Flows to Test

| Flow | Steps | Priority |
|------|-------|----------|
| Registration (create org) | Signup → onboarding → dashboard | High |
| Registration (personal) | Signup → dashboard | High |
| Invitation flow | Invite → accept → login | High |
| Dataset upload | Upload → view → delete | High |
| Dashboard creation | Create → configure → save → view | Medium |
| Report generation | Generate → view → export | Medium |
| Document capture | Upload → review → submit | Medium |
| User management | List → create → assign role → delete | High |
| Role management | List → create custom role → assign | Medium |
| Audit log viewing | Navigate → filter → view | Low |
| Theme switching | Light → dark → system | Low |
| Settings | Profile → appearance → security | Medium |

## 3. Test Environment

- Separate test database
- Seeded test data (not demo data)
- Test users with known credentials
- Cleanup between test runs

## Related Documents

- [strategy.md](strategy.md) — Testing strategy
- [integration-tests.md](integration-tests.md) — Integration tests
- [performance-tests.md](performance-tests.md) — Performance tests
