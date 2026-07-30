# ADR-0002: Blank Workspace by Default

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0003, ADR-0009 |

---

## Context

Enterprise customers expect a clean, professional onboarding experience. When a new organization is created, the workspace should be empty — no demo data, no sample dashboards, no pre-populated datasets. Demo data creates confusion, pollutes analytics, and undermines trust in a production environment.

However, some users may want sample data to explore the platform's capabilities before uploading their own data. This should be an explicit, opt-in action — never automatic.

## Decision

New user registration and organization creation always produce a **blank workspace**. No demo or sample data is created automatically.

### Implementation

1. **Signup flow** (`authentication/routes.py`, `organizations/invitation_service.py`): Creates user, optionally organization, and workspace — no demo data.
2. **Demo data seeding** (`enterprise/demo_data.py`): Only invoked when `SEED_DEMO_DATA=true` environment variable is set. This is off by default in production.
3. **Dashboard** (`frontend/app/(app)/dashboard/page.tsx`): Shows empty states with guidance ("No datasets yet", "No dashboards yet") and quick start cards.
4. **Onboarding** (`frontend/app/onboarding/page.tsx`): Collects user preferences without creating any data.

### Key Code Paths

- `api/main.py:222-230`: `seed_demo_data()` called only if `SEED_DEMO_DATA` is true
- `authentication/routes.py:signup()`: Creates user + org + workspace, no demo data
- `organizations/invitation_service.py:RegistrationService._register_with_org()`: Creates org + workspace, no demo data
- `organizations/invitation_service.py:RegistrationService._register_personal()`: Creates personal workspace, no demo data

## Alternatives Considered

1. **Auto-seed demo data on signup**: Rejected because it pollutes production analytics, confuses users, and requires cleanup.
2. **Ask during onboarding**: Rejected as the default because it adds friction and creates inconsistency. Users can request sample data later.
3. **Per-org demo data flag**: Considered for future implementation but adds complexity. Current approach is simpler and safer.

## Consequences

### Positive
- Clean, professional onboarding experience
- No data pollution in production
- Users see real value only from their own data
- Analytics and reports reflect actual usage from day one
- No cleanup required for production deployments

### Negative
- Some users may find the empty workspace intimidating
- New users may not understand the platform's capabilities without examples
- Requires good empty-state UX to guide users

### Mitigations
- Quick Start cards on dashboard guide first actions
- Empty states include clear CTAs ("Upload your first dataset")
- Onboarding wizard collects goals for personalization
- Optional sample workspace available via `SEED_DEMO_DATA` flag (see ADR-0003)

## Implementation Notes

- The `SEED_DEMO_DATA` environment variable is checked in `api/main.py` during startup
- Demo data is only for pilot/onboarding environments, never production
- The `seed_demo_data()` function creates a separate demo organization with demo users

## Future Considerations

- Add a "Load Sample Data" button in settings (opt-in, user-initiated)
- Create industry-specific sample datasets that can be loaded on demand
- Add a guided tour that uses synthetic data without persisting it

## Related ADRs

- ADR-0003: Optional Sample Workspace
- ADR-0009: Workspace Model
