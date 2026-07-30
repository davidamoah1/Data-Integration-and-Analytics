# ADR-0011: Template Architecture

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0009 |

---

## Context

DataFlow serves multiple industries (healthcare, education, business, research). Each industry has different data structures, analysis patterns, and reporting needs. Without templates, every user starts from scratch, leading to:
- Slow onboarding
- Inconsistent configurations
- Reinvention of common patterns

The platform needs reusable templates that provide industry-specific starting points while maintaining the blank workspace principle (ADR-0002).

## Decision

We implemented a **template architecture** with industry-specific studios and a template library.

### Studio Model

Studios are industry-specific entry points that provide:
- Curated dashboard templates
- Industry-relevant dataset schemas
- Pre-configured report formats
- Domain-specific AI prompts

### Studios

| Studio | Route | Focus |
|--------|-------|-------|
| Analytics Studio | `/analytics` | General-purpose data analytics |
| Healthcare Studio | `/studios` → Healthcare | Healthcare data, patient analytics, compliance |
| Education Studio | `/studios` → Education | Student performance, enrollment analytics |
| Business Studio | `/studios` → Business | Sales, operations, financial analytics |
| Research Studio | `/studios` → Research | Survey analysis, statistical modeling |
| Automation Studio | `/studios` → Automation | ETL pipelines, workflow automation |

### Template Library

The template library (`/templates`) provides:
- Pre-built dashboard layouts
- Report templates with standard sections
- Dataset schema templates
- Workflow templates for common ETL patterns

### Implementation

1. **Studios page** (`frontend/app/(app)/studios/page.tsx`): Cards for each industry studio
2. **Templates page** (`frontend/app/(app)/templates/page.tsx`): Template library browser
3. **Guided tasks** (`frontend/lib/workflows.ts:GUIDED_TASKS`): Quick start cards on dashboard
4. **Onboarding** (`frontend/app/onboarding/page.tsx`): Collects industry preference for studio recommendation

### Current Scope

- Studios and templates are **navigation and curation layers** — they guide users to relevant features
- Templates do not auto-create data (consistent with ADR-0002)
- Template application is user-initiated
- Future: Template application will create pre-configured dashboards/reports from user's data

## Alternatives Considered

1. **No templates**: Every user starts from scratch. Rejected — poor onboarding experience.
2. **Auto-applied templates**: Templates applied automatically on signup. Rejected — violates ADR-0002.
3. **Industry-specific deployments**: Separate codebase per industry. Rejected — maintenance nightmare.

## Consequences

### Positive
- Industry-specific entry points improve relevance
- Template library reduces time-to-value
- Studios provide curated experience without auto-creating data
- Templates are opt-in and user-initiated

### Negative
- Templates are currently navigation-only (no actual template application yet)
- No template versioning or sharing
- No custom template creation by users

### Mitigations
- Quick Start cards guide users to relevant actions
- Onboarding collects industry for personalization
- Future: Implement actual template application (create dashboard from template)

## Implementation Notes

- `GUIDED_TASKS` in `frontend/lib/workflows.ts` defines dashboard quick-start cards
- Studios page renders industry cards with icons and descriptions
- Templates page is a placeholder for future template browser
- Onboarding wizard collects `industry` and `organization_type` for personalization

## Future Considerations

- Implement template application (create dashboard/report from template using user's data)
- Add custom template creation (users save their dashboards as templates)
- Add template sharing within organization
- Add template marketplace (community-contributed templates)
- Add template versioning and updates
- Support industry-specific AI prompts and report formats

## Related ADRs

- ADR-0002: Blank Workspace by Default
- ADR-0009: Workspace Model
