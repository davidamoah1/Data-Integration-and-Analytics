# ADR-0007: Department-Based Data Governance

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-30 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001, ADR-0005, ADR-0009 |

---

## Context

Large organizations need to subdivide access beyond the organization level. A healthcare organization may have separate departments for Research, Clinical Operations, and Administration — each with different data access needs. Without department-level governance, all org members see all org data.

## Decision

We implemented **departments** as an organizational subdivision with role-based access control at the department level.

### Implementation

1. **Department model** (`organizations/models.py:Department`): Belongs to an organization, has name, description, and is_active flag.
2. **Department routes** (`organizations/services.py:dept_router`): CRUD for departments with `departments.manage` permission.
3. **User-department association**: Users have an optional `department_id` field on the User model.
4. **Department Manager role** (`dept_manager`): Can view department members and manage department operations.
5. **Department Officer role** (`dept_officer`): Read-only access to department dashboards and reports.

### Key Code Paths

- `organizations/services.py:create_department()`: Creates department within org (non-super-admin must use own org_id)
- `organizations/services.py:list_departments()`: Super admin can specify org_id; others use own
- `authentication/models.py:User.department_id`: Optional foreign key to department
- `platform_features/rbac.py:ROLE_HIERARCHY`: `dept_manager` at level 60, `dept_officer` at level 20

### Current Scope

- Departments are primarily an organizational construct for user grouping
- Data-level department scoping (e.g., datasets visible only to a department) is **not yet implemented**
- Department managers can view users in their org but not filter by department in the current API
- Future: Department-level query scoping will be added

## Alternatives Considered

1. **No departments**: All org members see all data. Rejected — insufficient for large organizations.
2. **Sub-organizations**: Nested orgs with their own isolation. Rejected — too complex, adds tenant nesting.
3. **Tag-based grouping**: Users tagged with labels instead of formal departments. Rejected — lacks structure and governance.

## Consequences

### Positive
- Organizations can structure teams into departments
- Department managers have a distinct role with appropriate permissions
- Department officers have limited, read-only access
- Foundation for future department-level data scoping

### Negative
- Department-level data isolation is not yet enforced in queries
- Department managers can see all org users, not just their department
- No department-level dashboards or reports (all org-scoped)

### Mitigations
- `departments.manage` permission controls who can create/modify departments
- Department assignment is visible in user profiles
- Future: Add `department_id` filter to dataset, dashboard, and report queries

## Implementation Notes

- Departments are created via `/api/departments` with `departments.manage` permission
- Non-super-admin users can only create departments within their own organization
- The `DepartmentCreate` schema requires `organization_id` and `name`
- Department deletion is a soft-delete (sets `is_deleted = 1`)

## Future Considerations

- Implement department-level query scoping (filter datasets/dashboards by department)
- Add department-level dashboards (visible only to department members)
- Add department-level audit logs
- Support department-level role assignments (e.g., a dept_manager for each department)
- Add department analytics and reporting

## Related ADRs

- ADR-0001: Enterprise Multi-Tenant Architecture
- ADR-0005: Role-Based Access Control
- ADR-0009: Workspace Model
