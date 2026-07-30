# User Personas

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

User personas for each platform role.

## Scope

All user types and their characteristics.

## Audience

Product managers, UX designers, and developers.

---

## 1. Platform Owner (Super Admin)

- **Role**: `super_admin`
- **Who**: Platform operator or SaaS provider employee
- **Goals**: Manage all organizations, monitor platform health, ensure security
- **Pain Points**: Need visibility across all tenants, manage billing, handle support
- **Key Features**: Admin Portal, all orgs view, tenant suspend/activate, audit logs

## 2. Organization Administrator

- **Role**: `org_admin`
- **Who**: IT manager or department head within an organization
- **Goals**: Manage org users, configure settings, oversee data governance
- **Pain Points**: User onboarding, role management, security compliance
- **Key Features**: User management, invitations, role assignment, settings

## 3. Department Manager

- **Role**: `dept_manager`
- **Who**: Team lead managing a department within an organization
- **Goals**: Oversee department operations, assign tasks, review analytics
- **Pain Points**: Department-level visibility, team coordination
- **Key Features**: Department dashboards, team overview, reports

## 4. Data Analyst

- **Role**: `data_analyst`
- **Who**: Data professional analyzing organizational data
- **Goals**: Create dashboards, generate reports, find insights
- **Pain Points**: Data preparation, visualization, sharing insights
- **Key Features**: Analytics Studio, dashboards, reports, AI assistant

## 5. Researcher

- **Role**: `researcher`
- **Who**: Academic or market researcher
- **Goals**: Upload research data, run statistical analysis, publish findings
- **Pain Points**: Data import, statistical tools, publication-ready outputs
- **Key Features**: Research Studio, ML models, report export

## 6. Data Entry Officer

- **Role**: `data_entry_officer`
- **Who**: Clerk or assistant processing paper documents
- **Goals**: Digitize documents quickly and accurately
- **Pain Points**: Manual data entry, accuracy, speed
- **Key Features**: Smart Data Capture, OCR, confidence scoring

## 7. Viewer

- **Role**: `viewer`
- **Who**: Executive or stakeholder who needs read-only access
- **Goals**: View dashboards and reports without editing
- **Pain Points**: Too many features, just wants to see data
- **Key Features**: Dashboard viewing, report viewing (read-only)

## 8. Personal Workspace User

- **Role**: `viewer` (personal)
- **Who**: Individual exploring the platform without an organization
- **Goals**: Try the platform, personal data analysis
- **Pain Points**: Limited features, no org context
- **Key Features**: Personal workspace, limited analytics

## Related Documents

- [../governance/roles.md](../governance/roles.md) — Role definitions
- [../workflows/user-journeys.md](../workflows/user-journeys.md) — User journeys
- [../user-guides/](../user-guides/) — Role-specific guides
