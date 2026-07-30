# ADR-0009: Workspace Model

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0002, ADR-0007 |

---

## Context

The platform needs to support both organizational and personal workspaces. An organization workspace is shared among org members, while a personal workspace belongs to a single user. The workspace model must:
- Distinguish between organization and personal workspaces
- Support future workspace-level data scoping
- Auto-create a workspace on registration
- Allow users to upgrade from personal to organizational

## Decision

We implemented a **Workspace model** that supports both organization-scoped and user-scoped workspaces.

### Model

```
Workspace
├── organization_id (nullable) → Organization workspace
├── user_id (nullable) → Personal workspace
├── name
├── type: "organization" | "personal"
├── is_active
└── is_deleted
```

### Workspace Types

1. **Organization Workspace**: `organization_id` set, `user_id` null, `type = "organization"`
   - Created automatically when an organization is created
   - Shared among all org members
   - Named `"{OrgName} Workspace"`

2. **Personal Workspace**: `organization_id` null, `user_id` set, `type = "personal"`
   - Created automatically on personal signup
   - Belongs to a single user
   - Named `"{FullName}'s Workspace"`

### Implementation

1. **Workspace model** (`organizations/workspace_models.py:Workspace`): Stores workspace metadata
2. **Auto-creation**: Workspaces are created during registration in both signup endpoints
3. **RegistrationService** (`organizations/invitation_service.py`):
   - `_register_with_org()`: Creates org workspace
   - `_register_personal()`: Creates personal workspace
4. **Old signup** (`authentication/routes.py:signup()`): Creates org workspace when org is created

### Key Code Paths

```python
# Organization workspace creation
workspace = Workspace(
    organization_id=org.id,
    name=f"{request.organization_name} Workspace",
    type="organization",
)

# Personal workspace creation
workspace = Workspace(
    user_id=user.id,
    name=f"{request.full_name}'s Workspace",
    type="personal",
)
```

### Current Scope

- Workspaces are created but **not yet used for query scoping**
- All data queries are scoped by `organization_id` on the resource, not by workspace
- The workspace model exists as a foundation for future workspace-level features
- Future: Datasets, dashboards, and reports can be scoped to a workspace

## Alternatives Considered

1. **No workspace model**: Just use organization_id for scoping. Rejected — no support for personal workspaces.
2. **Separate personal and org models**: Different models for personal vs org data. Rejected — unnecessary complexity.
3. **Workspace as a tenant**: Workspaces as the primary tenant unit. Rejected — organizations are the tenant boundary; workspaces are a subdivision.

## Consequences

### Positive
- Supports both organizational and personal use cases
- Foundation for workspace-level data scoping
- Clear separation: org workspace vs personal workspace
- Auto-created on registration (no manual setup needed)
- Upgrade path: personal → create/join organization

### Negative
- Workspaces are not yet used in data queries (model exists but unused in scoping)
- No workspace switching UI yet
- No workspace-level permissions yet

### Mitigations
- Organization-level scoping is fully implemented and enforced
- Workspace model is ready for future implementation
- Personal workspace users can upgrade by creating or joining an org

## Implementation Notes

- `Workspace.organization_id` is nullable (null for personal workspaces)
- `Workspace.user_id` is nullable (null for org workspaces)
- `Workspace.type` is a string: `"organization"` or `"personal"`
- Workspaces have `is_active` and `is_deleted` flags for lifecycle management
- The `Invitation` model also lives in `workspace_models.py`

## Future Considerations

- Implement workspace-level query scoping (datasets, dashboards, reports belong to a workspace)
- Add workspace switching UI (users can have multiple workspaces)
- Add workspace-level permissions (e.g., workspace admin, workspace viewer)
- Support workspace sharing (invite users to a specific workspace)
- Add workspace templates (pre-configured workspace setups)
- Support workspace archiving and restoration

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0002: Blank Workspace by Default
- ADR-0007: Department-Based Data Governance
