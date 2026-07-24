# AEDIP End User Guide

## Welcome to DataFlow

DataFlow is your Enterprise Data Intelligence Platform. This guide helps you get started in minutes.

## Quick Start (5 Minutes)

### 1. Log In

- Navigate to your DataFlow dashboard URL
- Enter your email and password
- Contact your administrator if you don't have credentials

### 2. Complete Onboarding (First-Time Users)

New users see an 8-step guided tour:
1. **Welcome** — Platform overview
2. **Organization Profile** — Set up your org
3. **Your Profile** — Personalize your account
4. **Invite Your Team** — Add team members
5. **Import Data** — Upload your first dataset
6. **ETL Pipeline** — Set up data transformation
7. **First Dashboard** — View your analytics
8. **AI Copilot** — Chat with your data

You can skip the tour and explore on your own at any time.

### 3. Choose Your Data Source

- **Live Database**: Connect directly to your organization's database
- **Upload File**: Upload a CSV or Excel file for quick analysis

### 4. Select an Industry Pack

In the sidebar, choose from:
- **SME** — Sales dashboards with revenue, profit, and product analysis
- **Healthcare** — Patient billing, insurance coverage, department efficiency
- **Education** — Tuition collection, program enrollment, department analytics
- **Government** — Project spending, contractor performance, budget allocation
- **Church** — Offering trends, member giving patterns, ministry performance
- **NGO** — Donation growth, program impact, funding source diversity

Each pack shows **completely different dashboards** with sector-specific KPIs and chart types.

### 5. Explore Your Dashboard

- **KPI Cards**: See key metrics at the top (sector-specific labels)
- **Charts**: Scroll down to view trend lines, category breakdowns, regional analysis
- **Filters**: Use the sidebar to filter by region, category, or date range
- **Data Table**: Browse individual records at the bottom

### 6. Ask the AI Copilot

- Scroll to the **AI Copilot** section at the bottom
- Type a question in plain English (e.g., "What are the top selling products?")
- The AI will analyze your data and provide insights with citations

### 7. Export Your Data

- Click **Download Filtered Data** in the sidebar
- Get a CSV file with your current filtered view

## Navigation

Use the sidebar **Navigation** to switch between pages:

### Dashboard
Main analytics view with KPIs, charts, filters, data table, and AI Copilot.

### Administration
- View and edit organization profile (name, timezone, contact info)
- Customize branding (colors, logo, theme)
- Manage users and roles
- View audit logs and security events
- Check subscription status and plan limits

### Support
- Submit general feedback
- Report bugs with reproduction steps
- Request new features
- View system diagnostics (CPU, memory, disk, API health)

### Observability
- View API status and subsystem health
- Monitor login activity over time
- Review audit logs and security events
- Track system logs

## Features

### Sector-Specific Dashboards

Each industry pack provides a **unique dashboard layout**:

- **SME**: Revenue trends, profit by region, top products scatter, heatmap
- **Healthcare**: Billing by department (treemap), insurance breakdown (sunburst), patient flow (funnel)
- **Education**: Enrollment trends, department performance (waterfall), program comparison
- **Government**: Spending by ministry (icicle), contractor performance, budget vs actual
- **Church**: Offering trends, giving by event type (rose chart), member growth
- **NGO**: Donation growth, funding source diversity (sunburst), program impact (treemap)

### AI Copilot

Ask questions like:
- "Show me profit by region"
- "What's the revenue trend over the last 6 months?"
- "Which products have the highest profit margin?"
- "Generate an executive summary report"
- "What anomalies do you see in the data?"

### ETL Pipelines

- Automated data extraction and loading
- Schedule recurring pipelines (daily, weekly, monthly)
- Monitor job status and history
- Automatic data cleaning: duplicates, date formats, currency strings, missing values
- Data quality scoring

### Data Upload

- Supported formats: CSV, XLSX, XLS
- Maximum file size depends on your subscription plan
- Automatic column detection and mapping
- Data cleaning on upload:
  - Duplicate removal
  - Date format normalization
  - Currency string parsing (e.g., "$2,068.74" → 2068.74)
  - Missing value handling
  - Text trimming and case normalization

### Reports

- **Executive Summary** — High-level KPIs and trends
- **Monthly Operations** — Pipeline status, user activity, system health
- **Custom Reports** — Generate via AI Copilot with natural language
- Export as Markdown, HTML, or PDF

## Tips

- Use filters to focus on specific data segments
- Export data regularly for offline analysis
- Ask the AI Copilot for quick insights — it understands your data context
- Check the quick-start checklist in the sidebar
- Switch industry packs to see different dashboard layouts
- Use the Support page to report issues or request features
- Contact your admin for new data sources, pipelines, or user invitations

## FAQ

**Q: How do I change my password?**
A: Contact your administrator or use the profile settings.

**Q: Can I upload my own data?**
A: Yes, use the "Upload File" option in the sidebar. Supported formats: CSV, XLSX, XLS.

**Q: Why is my dashboard empty?**
A: The database may not have data yet. Upload a file or ask your admin to run an ETL pipeline.

**Q: How accurate is the AI Copilot?**
A: The AI analyzes your actual data. Always verify critical decisions with manual review.

**Q: Why do I see different charts after selecting an industry pack?**
A: Each industry pack provides a completely unique dashboard with sector-specific KPIs, chart types, and analytics.

**Q: How do I upgrade my subscription?**
A: Navigate to Administration → Organization → Subscription Status, or ask your admin to use the API.

**Q: What happens when my trial expires?**
A: Your access is restricted to 1 user and 1 dashboard. Upgrade to a paid plan to restore full access.

**Q: How do I report a bug?**
A: Use the Support page → Bug Report tab. Provide steps to reproduce for faster resolution.

**Q: Can I customize the dashboard colors?**
A: Yes, admins can customize branding via Administration → Branding.
