# User Journey Maps

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active

---

## Overview

This document maps the complete lifecycle for every user role on the DataFlow platform. Each journey includes entry points, goals, primary tasks, decision points, error handling, success outcomes, and exit points.

---

## 1. Platform Owner Journey (`super_admin`)

### Entry Point
- **URL**: `/login` — Platform owner logs in with super admin credentials

### Goals
- Monitor platform health and all organizations
- Manage all organizations (create, suspend, activate)
- Review platform-wide audit logs
- Configure platform-level settings

### Journey Diagram

```
Platform Login
    ↓
Dashboard (platform overview)
    ↓
┌─────────────────────────────────┐
│  Decision: What to do?          │
├─────────────────────────────────┤
│  → View platform health         │
│  → Manage organizations         │
│  → Monitor analytics            │
│  → Review audit logs            │
│  → Configure platform settings  │
└─────────────────────────────────┘
    ↓
Admin Portal (/admin-portal)
    ↓
View tenant list + stats
    ↓
┌─────────────────────────────────┐
│  Decision: Tenant action?       │
├─────────────────────────────────┤
│  → Suspend tenant               │
│  → Activate tenant              │
│  → View tenant details          │
└─────────────────────────────────┘
    ↓
Audit Logs (/audit)
    ↓
Review security events
    ↓
Settings (/settings) — all tabs visible
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Login** (`/login`) — Enter credentials, receive JWT tokens
2. **Dashboard** (`/dashboard`) — Platform-wide stats, quick start cards
3. **Admin Portal** (`/admin-portal`) — Tenant list with suspend/activate actions
4. **Audit Logs** (`/audit`) — Search and filter platform-wide audit entries
5. **Settings** (`/settings`) — All settings tabs including platform-level configuration

### Decision Points
- Suspend vs. activate tenant (requires confirmation)
- Filter audit logs by date range, action type, or user
- Configure platform-level settings

### Error Handling
- **Tenant suspension failure**: Error message displayed on admin portal page
- **Audit log fetch failure**: Error state with retry button
- **Session expired**: Redirect to login page

### Success Outcomes
- All organizations visible and manageable
- Platform health monitored
- Security events reviewed
- Settings configured

### Exit Points
- Sign out (session revoked)
- Session timeout (auto-logout)

### Estimated Time-to-Value
- **First login to platform overview**: < 1 minute
- **Tenant management**: < 2 minutes per action

---

## 2. Organization Administrator Journey (`org_admin`)

### Entry Point
- **Registration** (`/signup`) — Creates organization, becomes org_admin
- **Invitation** (`/invite`) — Accepts invitation with org_admin role

### Goals
- Set up and manage the organization
- Invite and manage members
- Create departments and assign roles
- Upload datasets and create dashboards
- Generate and export reports

### Journey Diagram

```
Create Organization (/signup)
    ↓
Onboarding Wizard (/onboarding)
    ↓
┌─────────────────────────────────┐
│  Collect: Industry, Type, Goal  │
└─────────────────────────────────┘
    ↓
Dashboard (empty workspace)
    ↓
┌─────────────────────────────────┐
│  Decision: First action?       │
├─────────────────────────────────┤
│  → Invite team members          │
│  → Create departments           │
│  → Upload datasets              │
│  → Create dashboards           │
│  → Generate reports            │
│  → Configure org settings      │
└─────────────────────────────────┘
    ↓
Members (/admin) — Invite users
    ↓
┌─────────────────────────────────┐
│  Enter email + select role     │
│  → Cannot assign super_admin   │
│  → Cannot assign org_owner     │
└─────────────────────────────────┘
    ↓
Settings (/settings) — Organization tab
    ↓
Departments — Create + manage
    ↓
Datasets (/datasets) — Upload data
    ↓
Analytics (/analytics) — Build dashboards
    ↓
Reports (/reports) — Generate + export
    ↓
Audit Logs (/audit) — Review activity
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Signup** (`/signup`) — Select "Create Organization", enter org name + details
2. **Onboarding** (`/onboarding`) — Industry, organization type, primary goal
3. **Dashboard** (`/dashboard`) — Empty state with quick start cards
4. **Members** (`/admin`) — User list, invite form, role assignment
5. **Settings** (`/settings?tab=organization`) — Org name, description, contact info
6. **Settings** (`/settings?tab=departments`) — Create departments, assign members
7. **Datasets** (`/datasets`) — Upload CSV/Excel, view dataset list
8. **Analytics** (`/analytics`) — Create dashboards with widgets
9. **Reports** (`/reports`) — Generate reports, export to PDF/CSV
10. **Audit Logs** (`/audit`) — Review org activity

### Decision Points
- Which role to assign to invited member (cannot assign platform-level roles)
- Whether to create departments before inviting members
- Which datasets to upload first
- Dashboard layout and KPI selection

### Error Handling
- **Duplicate organization**: "This organization already exists" — prompted to request invitation
- **Invitation already exists**: "An active invitation already exists for this email"
- **Dataset upload failure**: Error state with retry
- **Role assignment to cross-org user**: 403 Forbidden

### Success Outcomes
- Organization created with blank workspace
- Team members invited and assigned roles
- Departments created and members assigned
- Datasets uploaded and analyzed
- Dashboards created and shared
- Reports generated and exported

### Exit Points
- Sign out
- Organization deleted (by super admin)

### Estimated Time-to-Value
- **Org creation to first dashboard**: 15-30 minutes
- **First team member invited**: 2 minutes

---

## 3. Analyst Journey (`data_analyst`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with data_analyst role

### Goals
- Upload and analyze datasets
- Create dashboards for data visualization
- Generate and export reports
- Use ML models for predictions

### Journey Diagram

```
Accept Invitation (/invite)
    ↓
Login (/login) — subsequent logins
    ↓
Dashboard (/dashboard)
    ↓
┌─────────────────────────────────┐
│  Decision: Analysis task?      │
├─────────────────────────────────┤
│  → Upload dataset               │
│  → View existing datasets      │
│  → Create dashboard            │
│  → Generate report             │
│  → Use ML models               │
└─────────────────────────────────┘
    ↓
Datasets (/datasets) — Upload CSV
    ↓
┌─────────────────────────────────┐
│  Validate: File format, size   │
│  → Error: Invalid format       │
│  → Success: Dataset uploaded   │
└─────────────────────────────────┘
    ↓
Analytics (/analytics) — Build dashboard
    ↓
┌─────────────────────────────────┐
│  Select dataset + chart type   │
│  Configure widgets + KPIs      │
└─────────────────────────────────┘
    ↓
Reports (/reports) — Generate report
    ↓
┌─────────────────────────────────┐
│  Decision: Export format?      │
├─────────────────────────────────┤
│  → PDF                         │
│  → CSV                         │
│  → Excel                       │
└─────────────────────────────────┘
    ↓
Export → Download
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite** (`/invite`) — Enter token, email, name, password
2. **Dashboard** (`/dashboard`) — See assigned datasets and dashboards
3. **Datasets** (`/datasets`) — Upload, view, filter datasets
4. **Analytics** (`/analytics`) — Create dashboards with visualizations
5. **Reports** (`/reports`) — Generate reports from dashboards/datasets
6. **Export** — Download report in selected format

### Decision Points
- Which dataset to analyze
- Chart type selection (bar, line, pie, scatter)
- Report format (PDF, CSV, Excel)
- Whether to use ML predictions

### Error Handling
- **Dataset upload failure**: Error message with supported formats
- **Dashboard save failure**: Validation errors for widget configuration
- **Report generation failure**: Error state with retry
- **No datasets available**: Empty state with upload CTA

### Success Outcomes
- Datasets uploaded and validated
- Dashboards created with meaningful visualizations
- Reports generated and exported
- ML predictions applied to datasets

### Exit Points
- Sign out
- Role changed by org admin

### Estimated Time-to-Value
- **First dataset uploaded**: 2-5 minutes
- **First dashboard created**: 10-15 minutes
- **First report exported**: 15-20 minutes

---

## 4. Researcher Journey (`researcher`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with researcher role

### Goals
- Import survey/research data
- Clean and prepare responses
- Run statistical analysis
- Generate publication-ready reports
- Export findings

### Journey Diagram

```
Accept Invitation (/invite)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard)
    ↓
Datasets (/datasets) — Import survey data
    ↓
┌─────────────────────────────────┐
│  Validate: Survey format       │
│  → Clean responses             │
│  → Remove duplicates           │
│  → Handle missing values       │
└─────────────────────────────────┘
    ↓
Analytics (/analytics) — Statistical analysis
    ↓
┌─────────────────────────────────┐
│  Select analysis type:         │
│  → Descriptive statistics      │
│  → Correlation analysis        │
│  → Regression                  │
│  → ML predictions              │
└─────────────────────────────────┘
    ↓
Reports (/reports) — Publication-ready report
    ↓
┌─────────────────────────────────┐
│  Format: PDF, CSV, Excel       │
│  Include: Charts, tables, text │
└─────────────────────────────────┘
    ↓
Export → Download
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite** (`/invite`) — Accept invitation
2. **Dashboard** (`/dashboard`) — Overview of research datasets
3. **Datasets** (`/datasets`) — Upload survey data (CSV, Excel)
4. **Analytics** (`/analytics`) — Statistical analysis and visualization
5. **Reports** (`/reports`) — Generate publication-ready reports
6. **Export** — Download in selected format

### Decision Points
- Data cleaning approach (remove duplicates, handle missing values)
- Analysis type (descriptive, inferential, predictive)
- Report format and content selection
- Whether to use ML for predictive analysis

### Error Handling
- **Invalid survey format**: Error with supported formats
- **Analysis failure**: Error with retry option
- **Empty dataset**: Empty state with upload guidance

### Success Outcomes
- Survey data imported and cleaned
- Statistical analysis completed
- Publication-ready report generated
- Findings exported in desired format

### Exit Points
- Sign out
- Role changed by org admin

### Estimated Time-to-Value
- **First dataset imported**: 3-5 minutes
- **First analysis completed**: 10-20 minutes
- **Publication-ready report**: 20-30 minutes

---

## 5. Data Entry Officer Journey (`data_entry_officer`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with data_entry_officer role

### Goals
- Capture documents using Smart Data Capture
- Review extracted data
- Correct low-confidence fields
- Submit processed data
- Track processing status

### Journey Diagram

```
Accept Invitation (/invite)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard)
    ↓
Smart Capture (/capture)
    ↓
┌─────────────────────────────────┐
│  Upload document               │
│  → Scan/photograph             │
│  → Upload PDF/image            │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  OCR Processing                │
│  → Extract fields              │
│  → Confidence scoring          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Review extracted data         │
│  → High confidence: Auto-accept│
│  → Low confidence: Manual fix │
│  → Missing fields: Enter       │
└─────────────────────────────────┘
    ↓
Submit → Dataset created
    ↓
┌─────────────────────────────────┐
│  Track processing status       │
│  → Processing → Ready          │
│  → Processing → Failed         │
└─────────────────────────────────┘
    ↓
Datasets (/datasets) — View submitted data
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite** (`/invite`) — Accept invitation
2. **Dashboard** (`/dashboard`) — Overview with quick start
3. **Smart Capture** (`/capture`) — Document upload interface
4. **Review** — Extracted data with confidence indicators
5. **Datasets** (`/datasets`) — View submitted datasets and status

### Decision Points
- Upload method (scan, photo, file upload)
- Which fields to correct (based on confidence score)
- Whether to resubmit failed documents

### Error Handling
- **OCR failure**: Error with retry, manual entry option
- **Upload failure**: Error with supported formats (PDF, JPG, PNG)
- **Processing failure**: Error state with resubmit option

### Success Outcomes
- Document captured and processed
- Extracted data reviewed and corrected
- Dataset created from captured data
- Processing status tracked

### Exit Points
- Sign out
- Role changed by org admin

### Estimated Time-to-Value
- **First document captured**: 1-2 minutes
- **Data reviewed and submitted**: 3-5 minutes per document

---

## 6. Viewer Journey (`viewer`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with viewer role
- **Personal signup** (`/signup`) — Creates personal workspace

### Goals
- View dashboards created by others
- View reports
- Download approved reports
- Update own profile

### Journey Diagram

```
Accept Invitation (/invite) or Signup (/signup)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard)
    ↓
┌─────────────────────────────────┐
│  Decision: What to view?      │
├─────────────────────────────────┤
│  → View dashboards             │
│  → View reports                │
│  → Download reports            │
│  → Update profile             │
└─────────────────────────────────┘
    ↓
Analytics (/analytics) — View dashboards (read-only)
    ↓
Reports (/reports) — View reports
    ↓
┌─────────────────────────────────┐
│  Decision: Download?           │
│  → PDF                         │
│  → CSV                         │
└─────────────────────────────────┘
    ↓
Settings (/settings) — Update profile
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite/Signup** — Accept invitation or create account
2. **Dashboard** (`/dashboard`) — Overview of available dashboards
3. **Analytics** (`/analytics`) — View dashboards (no edit capability)
4. **Reports** (`/reports`) — View reports, download if available
5. **Settings** (`/settings`) — Update profile, appearance, security

### Decision Points
- Which dashboard to view
- Whether to download a report
- Profile and appearance settings

### Error Handling
- **No dashboards available**: Empty state with guidance
- **No reports available**: Empty state
- **Permission denied for edit**: Read-only view (no error — edit controls hidden)

### Success Outcomes
- Dashboards viewed and understood
- Reports downloaded for offline review
- Profile updated

### Exit Points
- Sign out
- Role upgraded by org admin

### Estimated Time-to-Value
- **First dashboard view**: < 1 minute
- **First report download**: 1-2 minutes

---

## 7. Personal Workspace User Journey (`viewer`, no org)

### Entry Point
- **Registration** (`/signup`) — Selects "Personal" mode

### Goals
- Explore the platform with a personal workspace
- Upload personal datasets
- Create personal dashboards
- Generate reports
- Eventually upgrade to or join an organization

### Journey Diagram

```
Signup (/signup) — Personal mode
    ↓
┌─────────────────────────────────┐
│  No organization created       │
│  Personal workspace auto-created│
│  Assigned viewer role           │
└─────────────────────────────────┘
    ↓
Onboarding (/onboarding) — Collect preferences
    ↓
Dashboard (/dashboard) — Empty personal workspace
    ↓
┌─────────────────────────────────┐
│  Decision: What to do?        │
├─────────────────────────────────┤
│  → Upload personal dataset     │
│  → Create personal dashboard   │
│  → Generate report             │
│  → Join organization           │
│  → Create organization         │
└─────────────────────────────────┘
    ↓
Datasets (/datasets) — Upload personal data
    ↓
Analytics (/analytics) — Create dashboard
    ↓
Reports (/reports) — Generate report
    ↓
┌─────────────────────────────────┐
│  Decision: Upgrade?           │
├─────────────────────────────────┤
│  → Create organization         │
│  → Accept invitation           │
│  → Continue personal           │
└─────────────────────────────────┘
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Signup** (`/signup`) — Select "Personal" mode, enter details
2. **Onboarding** (`/onboarding`) — Industry, goals (for personalization)
3. **Dashboard** (`/dashboard`) — Empty workspace with quick start cards
4. **Datasets** (`/datasets`) — Upload personal datasets
5. **Analytics** (`/analytics`) — Create personal dashboards
6. **Reports** (`/reports`) — Generate and export reports
7. **Upgrade** — Create org or accept invitation to join existing org

### Decision Points
- Whether to stay personal or join/create an organization
- Which datasets to upload
- Dashboard creation and customization

### Error Handling
- **No org membership**: Cannot access org-scoped features (Members, Audit Logs)
- **Dataset upload failure**: Error with retry
- **Empty workspace**: Empty states with guidance CTAs

### Success Outcomes
- Personal workspace set up with datasets
- Dashboards created for personal analysis
- Reports generated
- Organization joined or created (upgrade path)

### Exit Points
- Sign out
- Upgrade to organization (creates or joins org)
- Account deletion

### Estimated Time-to-Value
- **First dataset uploaded**: 2-5 minutes
- **First dashboard created**: 10-15 minutes
- **Organization upgrade**: 5 minutes

---

## 8. Department Manager Journey (`dept_manager`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with dept_manager role

### Goals
- Manage department operations
- View team members
- Run ETL pipelines
- Generate department reports
- View analytics

### Journey Diagram

```
Accept Invitation (/invite)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard)
    ↓
┌─────────────────────────────────┐
│  Decision: Department task?   │
├─────────────────────────────────┤
│  → View team members           │
│  → Run ETL pipelines           │
│  → View dashboards             │
│  → Generate reports            │
│  → Export data                 │
└─────────────────────────────────┘
    ↓
Members (/admin) — View department members
    ↓
Datasets (/datasets) — View datasets
    ↓
Analytics (/analytics) — View department dashboards
    ↓
Reports (/reports) — Generate + export department reports
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite** (`/invite`) — Accept invitation
2. **Dashboard** (`/dashboard`) — Department overview
3. **Members** (`/admin`) — View team (read-only)
4. **Datasets** (`/datasets`) — View department datasets
5. **Analytics** (`/analytics`) — View department dashboards
6. **Reports** (`/reports`) — Generate and export reports

### Decision Points
- Which reports to generate
- Which datasets to export
- Dashboard viewing preferences

### Error Handling
- **No department assigned**: Prompt to contact org admin
- **Report generation failure**: Error with retry
- **Export failure**: Error with alternative format suggestion

### Success Outcomes
- Department operations managed
- Team members visible
- Reports generated and exported
- Data exported for department use

### Exit Points
- Sign out
- Role changed by org admin

### Estimated Time-to-Value
- **First dashboard view**: 1-2 minutes
- **First report generated**: 5-10 minutes

---

## 9. Auditor Journey (`auditor`)

### Entry Point
- **Invitation** (`/invite`) — Accepts invitation with auditor role

### Goals
- Review audit logs for security events
- View user activity within the organization
- Ensure compliance with policies

### Journey Diagram

```
Accept Invitation (/invite)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard)
    ↓
┌─────────────────────────────────┐
│  Decision: Audit task?        │
├─────────────────────────────────┤
│  → Review audit logs           │
│  → View user list              │
│  → Check security events       │
│  → Export audit findings       │
└─────────────────────────────────┘
    ↓
Audit Logs (/audit) — Search + filter
    ↓
┌─────────────────────────────────┐
│  Filter by:                    │
│  → Date range                  │
│  → Action type                 │
│  → User                        │
│  → Resource type               │
└─────────────────────────────────┘
    ↓
Members (/admin) — View user list
    ↓
Sign Out
```

### Screen-by-Screen Flow

1. **Invite** (`/invite`) — Accept invitation
2. **Dashboard** (`/dashboard`) — Overview
3. **Audit Logs** (`/audit`) — Search, filter, and review audit entries
4. **Members** (`/admin`) — View user list (read-only)

### Decision Points
- Which date range to filter audit logs
- Which action types to investigate
- Whether to escalate findings to org admin

### Error Handling
- **No audit logs**: Empty state with guidance
- **Search failure**: Error with retry
- **Permission denied for user details**: Limited view (read-only)

### Success Outcomes
- Security events reviewed
- User activity audited
- Compliance verified
- Findings documented

### Exit Points
- Sign out
- Role changed by org admin

### Estimated Time-to-Value
- **First audit log review**: 1-2 minutes
- **Full security review**: 15-30 minutes

---

## UX Recommendations

### High Priority
1. **Onboarding progress indicator** — Show completion percentage in onboarding wizard
2. **Empty state CTAs** — All empty states should have clear, actionable next steps
3. **Role-based dashboard** — Customize dashboard widgets based on user role
4. **Quick actions menu** — Floating action button for common tasks per role

### Medium Priority
5. **Guided tour** — First-time interactive walkthrough for each role
6. **Notification preferences** — Let users choose which notifications to receive
7. **Dashboard templates** — Pre-built dashboard templates per industry
8. **Bulk operations** — Bulk dataset upload, bulk user invitation

### Low Priority
9. **Keyboard shortcuts** — Power user keyboard navigation
10. **Dark mode default** — Auto-detect system preference (already implemented)
11. **Mobile responsive** — Optimize for tablet/mobile viewing
12. **Accessibility audit** — WCAG 2.1 AA compliance review

---

## Cross-References

- **Permission matrix**: `permission-matrix.md`
- **Frontend navigation**: `frontend-navigation-matrix.md`
- **API authorization**: `api-authorization-matrix.md`
- **ADR library**: `adr/` directory
