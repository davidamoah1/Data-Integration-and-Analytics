# ADR-0003: Optional Sample Workspace

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0002, ADR-0009 |

---

## Context

While blank workspaces are the default (ADR-0002), some users — especially those evaluating the platform or training new team members — benefit from sample data to understand capabilities. This sample data must be:
- Opt-in only (never automatic)
- Isolated from production data
- Easy to remove
- Clearly labeled as sample/demo data

## Decision

Sample data is available as an **opt-in, environment-controlled** feature. It is never created automatically during user registration.

### Implementation

1. **Environment variable**: `SEED_DEMO_DATA=true` controls demo data seeding at application startup.
2. **Demo data module** (`enterprise/demo_data.py`): Contains `seed_demo_data()` function that creates a separate demo organization with demo users, sample dashboards, KPIs, ETL pipelines, AI conversations, and AI reports.
3. **Isolation**: Demo data is created in a separate demo organization, not mixed with real user data.
4. **Production default**: `SEED_DEMO_DATA` is off (`false`) in production deployments.

### Key Code Paths

- `api/main.py:222-230`: Conditional call to `seed_demo_data()`
- `enterprise/demo_data.py:seed_demo_data()`: Creates demo org, users, dashboards, pipelines
- Configuration check: `if config.SEED_DEMO_DATA: seed_demo_data(db)`

## Alternatives Considered

1. **Per-user sample data toggle**: Rejected for initial implementation due to complexity. Users can request demo access separately.
2. **Sample data in every workspace**: Rejected — violates ADR-0002 (blank workspace principle).
3. **Separate demo instance**: Good for marketing but doesn't help users explore within their own workspace.

## Consequences

### Positive
- Production data stays clean
- Demo data is clearly separated
- Easy to enable for pilot deployments
- No risk of accidental demo data in production

### Negative
- No in-app "Load Sample Data" button yet (future enhancement)
- Users must be directed to a demo instance or have admin enable the flag

### Mitigations
- Document the `SEED_DEMO_DATA` flag in deployment guides
- Future: Add in-app "Load Sample Data" button in settings
- Future: Create industry-specific sample datasets

## Implementation Notes

- The `seed_demo_data()` function is idempotent — it checks for existing demo data before creating
- Demo users have predictable emails (e.g., `demo@dataflow.io`) for easy identification
- Demo organization has a distinct slug (`demo`) for easy identification and cleanup

## Future Considerations

- Add "Load Sample Data" button in organization settings (creates sample datasets in current org)
- Create industry-specific sample workspaces (healthcare, education, business, research)
- Add "Remove Sample Data" functionality
- Time-limited sample data that auto-expires

## Related ADRs

- ADR-0002: Blank Workspace by Default
- ADR-0009: Workspace Model
