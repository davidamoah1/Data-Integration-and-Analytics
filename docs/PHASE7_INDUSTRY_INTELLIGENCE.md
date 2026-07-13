# Phase 7 — Executive Decision Center (Part 5)
# Industry Intelligence Framework

## Purpose

This document defines a modular, multi-industry intelligence layer for AEDIP. Every industry receives specialized KPIs, dashboards, AI insights, forecasts, reports, workflows, approvals, ETL templates, validation rules, and business glossaries while sharing the same secure enterprise platform, authentication, RBAC, AI engine, ETL, Decision Center, and API gateway.

---

## 1. Common Framework

### Shared Platform Services

| Capability | Implementation |
|------------|---------------|
| Authentication | Existing JWT/auth service. |
| RBAC | Existing role and permission engine. |
| AI Platform | Phase 6 AI engines + Phase 7 AI Decision Engine. |
| ETL | Existing ETL service with industry-aware templates. |
| Decision Center | Phase 7 Part 3 UI + Part 2/4 backend. |
| Reports | Existing report service + industry templates. |
| Notifications | Phase 7 notification service. |
| Workflow & Approvals | Phase 7 workflow engine. |
| Audit Logs | Existing audit logging. |
| Data Governance | Data quality, lineage, retention. |
| API Gateway | Existing FastAPI gateway. |

### Industry Module Pattern

Every industry is a **vertical module** composed of:

```
industries/{industry_key}/
├── config.py              # Industry registration, enabled features, defaults
├── kpi_catalog.py         # Industry-specific KPI definitions
├── dashboard_catalog.py   # Dashboard and widget definitions
├── report_catalog.py      # Report templates
├── etl_templates.py       # Extract/transform/load templates
├── validation_rules.py    # Data validation rules
├── business_rules.py      # Business logic rules
├── ai_strategies.py       # Prompts, forecast targets, recommendation rules
├── workflows.py           # Approval chains and workflow templates
├── roles.py               # Role templates and permissions
├── glossary.py            # Business glossary
├── sample_data.py         # Seed data structures
└── api.py                 # Industry-specific API extensions
```

### Industry Registration

```python
INDUSTRY_REGISTRY = {
    "health": {
        "name": "Health",
        "suites": ["hospital", "clinic", "laboratory", "regional_health", "district_health", "private_provider"],
        "default_modules": ["patient_analytics", "pharmacy", "laboratory", "disease_surveillance"],
    },
    "education": {
        "name": "Education",
        "suites": ["basic_school", "shs", "tvet", "university", "private_school"],
        "default_modules": ["enrollment", "attendance", "performance", "teacher_workload"],
    },
    # ... additional industries
}
```

### Multi-Tenancy & Organization Industry

- Each organization selects one primary industry and optional secondary industries.
- `organizations.industry` column determines active modules.
- Feature flags per organization enable/disable industry-specific modules.
- Data is isolated by `organization_id` and `industry_suite`.

---

## 2. Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Platform (Shared)                                  │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Notifications · Audit · Reports │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Industry     │                │  Industry       │               │  Industry          │
│  Module       │                │  Module       │               │  Module            │
│  (Health)     │                │  (Education)    │               │  (Business)        │
│               │                │                 │               │                    │
│ KPI Catalog   │                │ KPI Catalog     │               │ KPI Catalog        │
│ Dashboards    │                │ Dashboards      │               │ Dashboards         │
│ ETL Templates │                │ ETL Templates   │               │ ETL Templates      │
│ AI Strategies │                │ AI Strategies   │               │ AI Strategies      │
│ Workflows     │                │ Workflows       │               │ Workflows          │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### Industry Data Flow

1. **Ingest** — ETL templates map industry-specific sources to canonical tables.
2. **Validate** — Industry validation rules enforce schema and business constraints.
3. **Compute** — Industry KPI engine calculates metrics from canonical data.
4. **Analyze** — AI engines run industry-tuned prompts and forecast models.
5. **Surface** — Dashboards, reports, alerts, and recommendations render industry context.
6. **Decide** — Approval workflows and decision timeline capture outcomes.

### Extension Points

- **KPI Engine:** register industry KPIs by key.
- **Dashboard Engine:** register dashboard templates by industry.
- **ETL Engine:** register extractors and transformers by source type.
- **AI Engine:** register prompts, forecast targets, and recommendation rules by industry.
- **Workflow Engine:** register workflow and approval templates.

---

## 3. Database Extensions

### New Tables

```sql
CREATE TABLE industries (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  key VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  icon VARCHAR(64),
  is_active BOOLEAN DEFAULT TRUE,
  default_modules JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_key (key)
) ENGINE=InnoDB;

CREATE TABLE industry_suites (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  key VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  description TEXT,
  default_modules JSON,
  sample_organization_name VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_industry_suite (industry_id, key),
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE organization_industry_settings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT NOT NULL,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  enabled_modules JSON,
  feature_flags JSON,
  default_dashboard_id BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_org (organization_id, industry_id),
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id)
) ENGINE=InnoDB;

CREATE TABLE industry_kpis (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(128),
  formula TEXT,
  unit VARCHAR(64),
  target_value DECIMAL(18,4),
  threshold_warning DECIMAL(18,4),
  threshold_critical DECIMAL(18,4),
  data_source VARCHAR(255),
  refresh_frequency VARCHAR(64),
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  UNIQUE KEY uniq_kpi (industry_id, suite_id, key),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_dashboards (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  layout JSON NOT NULL,
  widgets JSON NOT NULL,
  target_roles JSON,
  is_default BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  UNIQUE KEY uniq_dashboard (industry_id, suite_id, key),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  template_config JSON NOT NULL,
  target_roles JSON,
  schedule VARCHAR(64),
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  UNIQUE KEY uniq_report (industry_id, suite_id, key),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_etl_templates (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  name VARCHAR(255) NOT NULL,
  source_type VARCHAR(128) NOT NULL,
  extractor_config JSON,
  transform_config JSON,
  validation_rules JSON,
  target_tables JSON,
  sample_file_path VARCHAR(512),
  is_active BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_workflows (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  workflow_definition JSON NOT NULL,
  approval_chain JSON,
  trigger_events JSON,
  is_active BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  UNIQUE KEY uniq_workflow (industry_id, suite_id, key),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_glossary (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  term VARCHAR(128) NOT NULL,
  definition TEXT NOT NULL,
  related_kpis JSON,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;

CREATE TABLE industry_role_templates (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_id BIGINT NOT NULL,
  suite_id BIGINT,
  key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  permissions JSON NOT NULL,
  default_dashboard_id BIGINT,
  FOREIGN KEY (industry_id) REFERENCES industries(id),
  FOREIGN KEY (suite_id) REFERENCES industry_suites(id),
  UNIQUE KEY uniq_role (industry_id, suite_id, key),
  INDEX idx_industry (industry_id)
) ENGINE=InnoDB;
```

### Extension Columns

```sql
ALTER TABLE organizations ADD COLUMN industry_id BIGINT AFTER name;
ALTER TABLE organizations ADD COLUMN suite_id BIGINT AFTER industry_id;
ALTER TABLE organizations ADD FOREIGN KEY (industry_id) REFERENCES industries(id);
ALTER TABLE organizations ADD FOREIGN KEY (suite_id) REFERENCES industry_suites(id);
ALTER TABLE organizations ADD INDEX idx_industry (industry_id);

ALTER TABLE dc_alerts ADD COLUMN industry_context JSON;
ALTER TABLE ai_recommendations ADD COLUMN industry_key VARCHAR(64);
ALTER TABLE ai_recommendations ADD INDEX idx_industry (industry_key);
```

---

## 4. API Extensions

Base path: `/api/v1/industries`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List registered industries. |
| GET | `/{key}` | Get industry details and enabled modules. |
| GET | `/{key}/suites` | List suites for an industry. |
| GET | `/{key}/kpis` | List industry KPI definitions. |
| GET | `/{key}/dashboards` | List industry dashboards. |
| GET | `/{key}/dashboards/{dashboard_key}` | Get dashboard layout. |
| GET | `/{key}/reports` | List industry report templates. |
| GET | `/{key}/etl-templates` | List ETL templates. |
| GET | `/{key}/workflows` | List workflow templates. |
| GET | `/{key}/glossary` | List glossary terms. |
| GET | `/{key}/roles` | List industry role templates. |
| POST | `/{key}/kpis/calculate` | Trigger KPI recalculation. |
| POST | `/{key}/etl-templates/{id}/run` | Run an industry ETL template. |
| POST | `/{key}/workflows/{id}/start` | Start a workflow instance. |
| GET | `/organization/settings` | Get current org industry settings. |
| PUT | `/organization/settings` | Update org industry settings. |
| GET | `/health-score` | Get Organization Health Score with industry weights. |

### Industry-Specific Endpoints (examples)

| Method | Path | Industry | Description |
|--------|------|----------|-------------|
| GET | `/health/patients/admissions` | Health | Admissions analytics. |
| GET | `/education/enrollment/forecast` | Education | Enrollment forecast. |
| GET | `/church/giving/trends` | Church | Giving analytics. |
| GET | `/government/projects/status` | Government | Project status. |
| GET | `/business/sales/performance` | Business | Sales performance. |
| GET | `/ngo/impact/metrics` | NGO | Impact metrics. |
| GET | `/agriculture/yield/forecast` | Agriculture | Crop yield forecast. |

---

## 5. AI Strategies

### Industry-Aware Prompts

Each AI engine accepts `industry_key` and `suite_key` to load specialized prompts and context.

```python
PROMPT_TEMPLATES = {
    "health": {
        "recommendation": "...health-specific recommendation prompt...",
        "forecast": "...epidemiology-aware forecast prompt...",
        "root_cause": "...patient-flow root cause prompt...",
    },
    "education": {
        "recommendation": "...education-specific recommendation prompt...",
        "forecast": "...enrollment forecast prompt...",
    },
    # ...
}
```

### Industry Forecast Targets

| Industry | Targets |
|----------|---------|
| Health | admissions, discharges, bed occupancy, disease cases, medicine demand, waiting time |
| Education | enrollment, attendance, graduation, dropout, exam performance, fee collection |
| Church | attendance, giving, membership, visitor retention, event participation |
| Government | project completion, budget utilization, citizen service requests |
| Business | sales, revenue, inventory, customer acquisition, churn |
| NGO | beneficiaries served, donations, project reach, impact indicators |
| Agriculture | crop yield, rainfall, input costs, market price, demand |
| Retail | sales, inventory turnover, customer visits, promotion lift |
| Manufacturing | production output, defect rate, downtime, maintenance |
| Logistics | deliveries, fuel cost, route efficiency, on-time rate |

### Recommendation Rules

- Rules stored in `industry_recommendation_rules` JSON or table.
- Map trigger patterns (KPI threshold, anomaly, forecast risk) to suggested actions.
- AI engine uses rules + LLM reasoning to generate final recommendations.

### Benchmarks

- Internal benchmarking is always available.
- Cross-organization benchmarking requires opt-in and anonymization.
- Benchmark dimensions vary by industry: departments, regions, schools, hospitals, churches, projects, business units.

---

## 6. Industry Suites Catalog

### 6.1 Health Suite

#### Overview
Healthcare intelligence for hospitals, clinics, laboratories, regional/district directorates, and private providers.

#### Business Problems
- Bed occupancy mismanagement
- Medicine stockouts
- Long patient waiting times
- Disease outbreak detection delays
- High readmission rates
- Resource underutilization

#### Data Sources
- HMIS, EMR, OPD registers, lab systems, pharmacy systems, inventory systems, DHIMS2, surveillance reports.

#### Key KPIs
- Bed Occupancy Rate
- Average Length of Stay
- OPD Attendance
- Admission & Discharge Rate
- Readmission Rate
- Mortality Rate
- Waiting Time
- Medicine Stock Availability
- Lab Turnaround Time
- Maternal & Child Health Indicators
- Vaccination Coverage
- Disease Surveillance Counts
- Revenue per Patient

#### Executive Dashboard
- Organization Health Score
- Patient volume trend
- Bed occupancy gauge
- Critical medicine alerts
- Disease surveillance heatmap
- Department performance grid
- AI recommendations

#### Department Dashboards
- OPD, IPD, Pharmacy, Laboratory, Maternity, Surgery, Finance, HR.

#### AI Insights
- Admission trend drivers
- Readmission risk patients
- Medicine shortage predictions
- Disease outbreak early warning
- Optimal staffing recommendations

#### Forecast Models
- Prophet for admissions and disease cases
- ARIMA for bed occupancy
- XGBoost for waiting time and readmission risk

#### ETL Templates
- Patient admissions CSV
- Pharmacy inventory feed
- Lab results HL7/FHIR
- Disease surveillance DHIMS2

#### Validation Rules
- Patient ID uniqueness
- Valid gender/age ranges
- Discharge date ≥ admission date
- Non-negative quantities

#### Reports
- Daily patient summary
- Monthly morbidity/mortality
- Quarterly health sector performance

#### Workflows
- Medicine reorder approval
- Referral escalation
- Outbreak alert chain

#### Roles
- Hospital Director, Medical Superintendent, Head of Nursing, Pharmacy Manager, Lab Manager, Finance Officer.

#### Glossary
- OPD, IPD, HMIS, DHIMS2, Bed Occupancy, Readmission, TAT.

---

### 6.2 Education Suite

#### Overview
Intelligence for basic schools, SHS, TVET, universities, and private schools.

#### Business Problems
- Enrollment decline
- High dropout rates
- Teacher workload imbalance
- Exam performance gaps
- Fee collection delays

#### Data Sources
- Student information systems, attendance systems, LMS, exam systems, finance systems.

#### Key KPIs
- Enrollment Rate
- Attendance Rate
- Dropout Rate
- Pass Rate
- Graduation Rate
- Teacher-Student Ratio
- Average Class Size
- Fee Collection Rate
- Learning Outcomes Index

#### Executive Dashboard
- Enrollment trend
- Attendance heatmap
- Exam performance by subject
- Teacher workload
- AI recommendations

#### AI Insights
- At-risk students
- Enrollment forecast by region
- Subject performance drivers
- Teacher shortage predictions

#### Forecast Models
- Prophet for enrollment
- XGBoost for dropout risk
- ARIMA for attendance

#### ETL Templates
- Student enrollment CSV
- Daily attendance feed
- Exam results CSV
- Fee collection feed

#### Validation Rules
- Valid student ID
- Age in expected range
- Attendance ≤ 100%
- Exam score within 0–100

#### Reports
- Enrollment report
- Exam performance analysis
- Dropout risk report

#### Workflows
- Student transfer approval
- Scholarship recommendation
- Teacher deployment request

#### Roles
- Headteacher, Principal, Registrar, Finance Officer, Teacher, School Board.

#### Glossary
- SHS, TVET, BECE, WASSCE, Dropout, Cohort.

---

### 6.3 Church Suite

#### Overview
Intelligence for small churches, mega churches, and church headquarters.

#### Business Problems
- Visitor retention
- Giving decline
- Volunteer engagement
- Event attendance gaps
- Follow-up leakage

#### Data Sources
- Member databases, attendance kiosks, giving platforms, event systems, small group systems.

#### Key KPIs
- Total Membership
- Weekly Attendance
- Visitor Count
- Visitor Retention Rate
- Giving Amount
- Giving per Capita
- Department Participation
- Event Attendance
- Volunteer Count
- Small Group Involvement
- Follow-up Completion Rate

#### Executive Dashboard
- Attendance trend
- Giving dashboard
- Membership growth
- Ministry participation
- AI growth insights

#### AI Insights
- Giving trend drivers
- Visitor retention predictions
- Event impact analysis
- Ministry growth opportunities

#### Forecast Models
- Prophet for attendance and giving
- XGBoost for visitor retention

#### ETL Templates
- Member register CSV
- Weekly attendance CSV
- Giving statement import
- Event attendance CSV

#### Validation Rules
- Valid phone/email
- Non-negative giving amounts
- Attendance date format

#### Reports
- Monthly church health report
- Giving analysis
- Growth report

#### Workflows
- New member follow-up
- Event approval
- Volunteer onboarding

#### Roles
- Senior Pastor, Head of Ministries, Finance Secretary, Small Group Leader, Admin.

#### Glossary
- Giving, Tithe, Offering, Membership, Visitor, Small Group, Ministry.

---

### 6.4 Government Suite

#### Overview
Intelligence for ministries, departments, agencies, and MMDAs.

#### Business Problems
- Project delays
- Budget overruns
- Citizen service gaps
- Reporting fragmentation
- Approval bottlenecks

#### Data Sources
- Project management systems, budget systems, payroll, citizen service portals, procurement systems.

#### Key KPIs
- Project Completion Rate
- Budget Utilization
- Citizen Service Requests
- Procurement Cycle Time
- Revenue Mobilization
- Expenditure vs Budget
- Staff Strength
- Policy Implementation Rate

#### Executive Dashboard
- Project portfolio status
- Budget performance
- Citizen service metrics
- Regional performance map
- AI decision support

#### AI Insights
- At-risk projects
- Budget variance drivers
- Revenue forecast
- Approval bottleneck analysis

#### Forecast Models
- Prophet for revenue
- XGBoost for project delay risk

#### ETL Templates
- Project list CSV
- Budget execution CSV
- Citizen requests CSV

#### Validation Rules
- Valid project code
- Date consistency
- Budget line alignment

#### Reports
- Quarterly performance report
- Budget execution report
- Citizen service report

#### Workflows
- Project approval chain
- Budget release approval
- Procurement approval

#### Roles
- Minister, Chief Director, Director, Regional Director, Budget Officer, M&E Officer.

#### Glossary
- MMDA, MOU, PI, Budget Utilization, Procurement, Citizen Service.

---

### 6.5 Business Suite (SME & Enterprise)

#### Overview
General business intelligence for sales, finance, inventory, CRM, HR, projects, and assets.

#### Business Problems
- Sales volatility
- Cash flow gaps
- Inventory mismanagement
- Customer churn
- Project delays

#### Data Sources
- ERP, accounting software, CRM, POS, payroll, project management tools.

#### Key KPIs
- Revenue
- Gross Profit Margin
- Net Profit Margin
- Sales Growth
- Customer Acquisition Cost
- Customer Lifetime Value
- Inventory Turnover
- Accounts Receivable Days
- Employee Productivity
- Project Margin

#### Executive Dashboard
- Revenue and profit trends
- Sales pipeline
- Cash flow forecast
- Top customers/products
- AI recommendations

#### AI Insights
- Sales forecast
- Churn risk customers
- Inventory reorder points
- Cash flow risks

#### Forecast Models
- Prophet/XGBoost for revenue
- ARIMA for cash flow
- Classification for churn risk

#### ETL Templates
- Sales CSV
- Customer CSV
- Inventory CSV
- GL entries CSV

#### Validation Rules
- Positive revenue amounts
- Date ordering
- Customer ID present

#### Reports
- P&L report
- Cash flow report
- Sales performance report

#### Workflows
- Quote approval
- Purchase order approval
- Budget vs actual review

#### Roles
- CEO, CFO, Sales Manager, Operations Manager, HR Manager.

#### Glossary
- CAC, LTV, GMV, ARR, MRR, Churn, Pipeline.

---

### 6.6 NGO Suite

#### Overview
Intelligence for international NGOs, local NGOs, and foundations.

#### Business Problems
- Donor reporting burden
- Beneficiary tracking gaps
- M&E data fragmentation
- Impact measurement difficulty
- Budget compliance

#### Data Sources
- Beneficiary databases, donor systems, project management tools, M&E forms, financial systems.

#### Key KPIs
- Beneficiaries Reached
- Projects Active
- Donations Received
- Budget Utilization
- Impact Indicators
- Program Coverage
- Staff per Beneficiary
- Reporting Timeliness

#### Executive Dashboard
- Beneficiary reach
- Donation trend
- Project status
- Impact indicators
- AI recommendations

#### AI Insights
- Funding gap predictions
- Beneficiary growth trends
- Program effectiveness drivers
- Risk of delayed reports

#### Forecast Models
- Prophet for donations
- XGBoost for beneficiary reach

#### ETL Templates
- Beneficiary registration CSV
- Donation feed
- Project progress CSV
- Indicator data CSV

#### Validation Rules
- Valid beneficiary ID
- Date in project period
- Indicator value in range

#### Reports
- Donor report
- Impact report
- Quarterly program report

#### Workflows
- Project approval
- Fund release
- Beneficiary enrollment

#### Roles
- Executive Director, Program Manager, M&E Officer, Finance Officer, Field Officer.

#### Glossary
- Beneficiary, M&E, Indicator, Donor, Grant, Impact.

---

### 6.7 Agriculture Suite

#### Overview
Intelligence for farmers, cooperatives, and agribusinesses.

#### Business Problems
- Yield unpredictability
- Weather risk
- Input cost volatility
- Post-harvest losses
- Market price fluctuations

#### Data Sources
- Farm management systems, weather APIs, satellite/GIS, market price feeds, warehouse systems.

#### Key KPIs
- Crop Yield (tons/hectare)
- Area Planted
- Input Cost per Hectare
- Rainfall
- Market Price
- Warehouse Stock
- Distribution Volume
- Profit per Hectare

#### Executive Dashboard
- Yield map
- Weather dashboard
- Input cost trend
- Market price comparison
- AI recommendations

#### AI Insights
- Yield forecast
- Optimal planting time
- Pest/disease risk
- Market price predictions

#### Forecast Models
- Prophet for yield and price
- XGBoost for weather impact
- ARIMA for demand

#### GIS Ready
- GeoJSON field boundaries
- Choropleth yield maps
- Weather overlay

#### ETL Templates
- Farm register CSV
- Harvest CSV
- Weather CSV
- Market price CSV

#### Validation Rules
- Valid GPS coordinates
- Non-negative area
- Rainfall ≥ 0

#### Reports
- Seasonal production report
- Market analysis
- Profitability report

#### Workflows
- Input procurement approval
- Harvest planning
- Market dispatch

#### Roles
- Farm Manager, Agronomist, Warehouse Manager, Sales Officer.

#### Glossary
- Hectare, Yield, Input, Post-harvest, GIS, Cooperative.

---

### 6.8 Retail Suite

#### Overview
Intelligence for retail stores, chains, and e-commerce.

#### Business Problems
- Stockouts and overstock
- Promotion effectiveness
- Customer churn
- Sales forecast accuracy
- Supplier delays

#### Data Sources
- POS systems, inventory systems, supplier systems, CRM, e-commerce platforms.

#### Key KPIs
- Sales Revenue
- Units Sold
- Gross Margin
- Inventory Turnover
- Stockout Rate
- Customer Count
- Average Transaction Value
- Promotion Lift
- Supplier Lead Time
- Sell-Through Rate

#### Executive Dashboard
- Sales trend
- Top products
- Inventory status
- Promotion performance
- AI recommendations

#### AI Insights
- Demand forecast
- Reorder recommendations
- Promotion optimization
- Customer segmentation

#### Forecast Models
- Prophet for sales
- XGBoost for demand
- ARIMA for inventory

#### ETL Templates
- POS transaction CSV
- Inventory CSV
- Customer CSV
- Promotion CSV

#### Validation Rules
- Non-negative prices/quantities
- Valid SKU
- Transaction date ordering

#### Reports
- Sales performance report
- Inventory report
- Promotion effectiveness report

#### Workflows
- Purchase order approval
- Promotion approval
- Stock transfer

#### Roles
- Retail Manager, Buyer, Store Manager, Marketing Manager.

#### Glossary
- SKU, POS, Sell-Through, GMROI, Stockout, Promotion Lift.

---

### 6.9 Manufacturing Suite

#### Overview
Intelligence for production, machines, maintenance, quality, inventory, and supply chain.

#### Business Problems
- Unplanned downtime
- Quality defects
- Production schedule delays
- Maintenance backlog
- Supply chain disruptions

#### Data Sources
- MES, ERP, SCADA, quality systems, maintenance systems, inventory systems.

#### Key KPIs
- OEE (Overall Equipment Effectiveness)
- Production Output
- Defect Rate
- Downtime Hours
- Maintenance Cost
- On-Time Delivery
- Raw Material Inventory
- Yield
- Throughput

#### Executive Dashboard
- OEE trend
- Production schedule
- Quality alerts
- Maintenance backlog
- AI recommendations

#### AI Insights
- Downtime prediction
- Quality defect root cause
- Maintenance scheduling
- Supply chain risk

#### Forecast Models
- Prophet for production output
- XGBoost for downtime risk
- ARIMA for maintenance cost

#### ETL Templates
- Production log CSV
- Machine sensor CSV
- Quality inspection CSV
- Maintenance record CSV

#### Validation Rules
- Valid machine ID
- Non-negative output
- Timestamp ordering

#### Reports
- Production report
- Quality report
- Maintenance report

#### Workflows
- Maintenance request approval
- Production schedule change
- Quality hold release

#### Roles
- Plant Manager, Production Manager, Quality Manager, Maintenance Supervisor.

#### Glossary
- OEE, TPM, Downtime, Defect Rate, Throughput, MES.

---

### 6.10 Logistics Suite

#### Overview
Intelligence for fleet, routes, warehouses, drivers, fuel, and deliveries.

#### Business Problems
- Route inefficiency
- Fuel cost escalation
- Late deliveries
- Driver safety
- Warehouse capacity gaps

#### Data Sources
- Fleet management systems, GPS tracking, fuel cards, delivery systems, warehouse systems.

#### Key KPIs
- On-Time Delivery Rate
- Average Delivery Time
- Fuel Cost per km
- Fleet Utilization
- Route Efficiency
- Driver Safety Score
- Warehouse Capacity
- Cost per Delivery
- Delivery Accuracy

#### Executive Dashboard
- Delivery map
- Fleet status
- Fuel cost trend
- On-time performance
- AI recommendations

#### AI Insights
- Optimal route suggestions
- Fuel cost drivers
- Delivery delay predictions
- Warehouse capacity forecast

#### Forecast Models
- Prophet for delivery volume
- XGBoost for delay risk
- ARIMA for fuel cost

#### ETL Templates
- Trip CSV
- Fuel transaction CSV
- Delivery CSV
- Driver CSV

#### Validation Rules
- Valid vehicle ID
- Distance ≥ 0
- Fuel amount ≥ 0
- Timestamp consistency

#### Reports
- Delivery performance report
- Fuel analysis
- Fleet utilization report

#### Workflows
- Route approval
- Maintenance request
- Delivery exception escalation

#### Roles
- Logistics Manager, Fleet Manager, Warehouse Manager, Driver Supervisor.

#### Glossary
- ETA, POD, Fleet, Route, Utilization, On-Time Delivery.

---

## 7. Additional Industries Extension Template

For each additional industry (finance, banking, insurance, hospitality, tourism, mining, construction, real estate, telecommunications, energy, utilities, human resources, procurement, supply chain, research, universities-as-enterprise, SMEs), the following template is used.

```python
INDUSTRY_TEMPLATE = {
    "overview": "Industry description and value proposition.",
    "business_problems": ["..."],
    "data_sources": ["..."],
    "kpis": [{"key": "...", "name": "...", "formula": "...", "unit": "..."}],
    "executive_dashboard": {"widgets": [...]},
    "department_dashboards": ["..."],
    "ai_insights": ["..."],
    "forecast_targets": ["..."],
    "decision_models": ["..."],
    "workflow_templates": ["..."],
    "approval_chains": ["..."],
    "etl_templates": ["..."],
    "import_templates": ["..."],
    "validation_rules": ["..."],
    "reports": ["..."],
    "charts": ["..."],
    "alerts": ["..."],
    "notifications": ["..."],
    "health_metrics": ["..."],
    "compliance_requirements": ["..."],
    "role_templates": ["..."],
    "permissions": ["..."],
    "database_extensions": ["..."],
    "api_extensions": ["..."],
    "background_jobs": ["..."],
    "automation_rules": ["..."],
    "benchmark_metrics": ["..."],
    "data_quality_rules": ["..."],
    "recommendation_rules": ["..."],
    "glossary": {"term": "definition"},
    "sample_data_structure": {...}
}
```

Industries are registered in `INDUSTRY_REGISTRY` and implemented by following the module pattern.

---

## 8. Role Matrix & Permissions

### Common Roles per Industry

| Role | Typical Permissions |
|------|---------------------|
| Executive | `decision_center.read`, `reports.read`, `ai.recommendations.approve`, `kpi.*` |
| Department Head | `department.read`, `kpi.read`, `workflow.execute`, `reports.read` |
| Analyst | `data.read`, `reports.create`, `etl.read`, `dashboard.read` |
| Operator | `data.entry`, `workflow.task`, `alerts.read` |
| Viewer | `dashboard.read`, `reports.read` |

### Permission Naming Convention

```
{industry}.{module}.{action}
```

Examples:
- `health.patient.read`
- `health.pharmacy.manage`
- `education.enrollment.read`
- `church.giving.read`
- `agriculture.yield.forecast`
- `business.sales.read`

### Industry Role Templates

Stored in `industry_role_templates`. On organization onboarding, the platform clones the selected industry's role templates and assigns default permissions.

---

## 9. KPI Catalog

### KPI Definition Schema

```json
{
  "key": "bed_occupancy_rate",
  "name": "Bed Occupancy Rate",
  "industry": "health",
  "suite": "hospital",
  "category": "Operations",
  "description": "Percentage of available beds that are occupied.",
  "formula": "(occupied_beds / total_beds) * 100",
  "unit": "%",
  "target_value": 85,
  "threshold_warning": 75,
  "threshold_critical": 90,
  "data_source": "bed_occupancy_fact",
  "refresh_frequency": "hourly",
  "dimensions": ["ward", "department", "date"]
}
```

### Sample KPIs by Industry

| Industry | Sample KPIs |
|----------|--------------|
| Health | Bed Occupancy Rate, OPD Attendance, Waiting Time, Mortality Rate |
| Education | Enrollment Rate, Attendance Rate, Pass Rate, Dropout Rate |
| Church | Attendance, Giving, Visitor Retention, Small Group Participation |
| Government | Budget Utilization, Project Completion, Citizen Requests |
| Business | Revenue, Gross Margin, CAC, Inventory Turnover |
| NGO | Beneficiaries Reached, Budget Utilization, Impact Indicators |
| Agriculture | Crop Yield, Input Cost, Market Price, Profit per Hectare |
| Retail | Sales Revenue, Stockout Rate, Promotion Lift, Sell-Through |
| Manufacturing | OEE, Defect Rate, Downtime, On-Time Delivery |
| Logistics | On-Time Delivery, Fuel Cost/km, Fleet Utilization |

---

## 10. Report Catalog

### Report Templates

| Industry | Report |
|----------|--------|
| Health | Daily Patient Summary, Monthly Morbidity/Mortality, Quarterly Health Performance |
| Education | Enrollment Report, Exam Performance, Dropout Risk Report |
| Church | Monthly Church Health, Giving Analysis, Growth Report |
| Government | Quarterly Performance, Budget Execution, Citizen Service |
| Business | P&L, Cash Flow, Sales Performance |
| NGO | Donor Report, Impact Report, Program Report |
| Agriculture | Seasonal Production, Market Analysis, Profitability |
| Retail | Sales Performance, Inventory, Promotion Effectiveness |
| Manufacturing | Production, Quality, Maintenance |
| Logistics | Delivery Performance, Fuel Analysis, Fleet Utilization |

---

## 11. Dashboard Catalog

### Dashboard Templates

| Industry | Dashboard | Key Widgets |
|----------|-----------|-------------|
| Health | Executive Health | Health Score, Admissions, Bed Occupancy, Alerts, AI Recs |
| Education | Executive Education | Enrollment, Attendance, Performance, Teacher Workload |
| Church | Executive Church | Attendance, Giving, Membership, Ministries |
| Government | Executive Government | Projects, Budget, Citizen Services, Regional Map |
| Business | Executive Business | Revenue, Profit, Pipeline, Cash Flow |
| NGO | Executive NGO | Beneficiaries, Donations, Projects, Impact |
| Agriculture | Executive Agriculture | Yield Map, Weather, Market, Inputs |
| Retail | Executive Retail | Sales, Inventory, Promotions, Customers |
| Manufacturing | Executive Manufacturing | OEE, Production, Quality, Maintenance |
| Logistics | Executive Logistics | Deliveries, Fleet, Fuel, Routes |

---

## 12. ETL Templates

### Template Structure

```python
ETL_TEMPLATE = {
    "name": "Hospital Admissions Import",
    "source_type": "csv",
    "extractor": "csv_upload",
    "transform_config": {
        "columns": ["patient_id", "admission_date", "discharge_date", "ward", "diagnosis"],
        "date_format": "%Y-%m-%d",
        "deduplicate_by": ["patient_id", "admission_date"],
    },
    "validation_rules": {
        "patient_id": {"required": True, "unique": True},
        "admission_date": {"required": True, "type": "date"},
        "discharge_date": {"type": "date", "gte_field": "admission_date"},
    },
    "target_tables": ["patients", "admissions"],
    "sample_file": "samples/health_admissions.csv"
}
```

### Common Templates

| Industry | Template |
|----------|----------|
| Health | Patient admissions, pharmacy inventory, lab results |
| Education | Student enrollment, attendance, exam results |
| Church | Member register, attendance, giving |
| Government | Projects, budget execution, citizen requests |
| Business | Sales, customers, inventory, GL |
| NGO | Beneficiaries, donations, project indicators |
| Agriculture | Farm register, harvest, weather, market price |
| Retail | POS transactions, inventory, customers |
| Manufacturing | Production log, machine sensors, quality |
| Logistics | Trips, fuel, deliveries, drivers |

---

## 13. Automation Rules

### Rule Engine

Rules are stored as JSON and evaluated by the automation service.

```json
{
  "rule_id": "health_medicine_low_stock",
  "industry": "health",
  "trigger": {
    "type": "kpi_threshold",
    "kpi": "medicine_stock_days",
    "condition": "<",
    "value": 7
  },
  "actions": [
    {"type": "alert", "severity": "high"},
    {"type": "notification", "channels": ["email", "push"], "recipients": ["pharmacy_manager"]},
    {"type": "create_task", "assignee_role": "pharmacy_manager"},
    {"type": "recommendation", "template": "reorder_medicine"}
  ]
}
```

### Sample Rules

| Industry | Rule |
|----------|------|
| Health | Low medicine stock → alert + reorder recommendation |
| Education | Attendance drops below 80% → alert principal |
| Church | Visitor retention below 30% → follow-up workflow |
| Government | Project delay > 30 days → escalate to director |
| Business | Cash flow below threshold → CFO alert |
| NGO | Donation shortfall → fundraising recommendation |
| Agriculture | Yield forecast below target → advisory |
| Retail | Stockout rate > 5% → reorder recommendation |
| Manufacturing | OEE < 60% → maintenance alert |
| Logistics | On-time delivery < 90% → route review |

---

## 14. Data Quality Rules

### Framework

| Rule Type | Example |
|-----------|---------|
| Completeness | Required fields present |
| Uniqueness | Patient ID, student ID, SKU unique |
| Validity | Date ranges, numeric ranges, enum values |
| Consistency | Discharge date ≥ admission date |
| Timeliness | Data received within expected window |
| Referential | Foreign key relationships valid |

### Industry Examples

| Industry | Rule |
|----------|------|
| Health | Admission date before discharge date |
| Education | Attendance ≤ 100% |
| Church | Giving amount non-negative |
| Government | Project budget ≥ spent amount |
| Business | Revenue ≥ 0 |
| NGO | Beneficiary count is integer ≥ 0 |
| Agriculture | Area planted > 0 |
| Retail | Quantity sold ≤ stock on hand |
| Manufacturing | Downtime ≤ total shift time |
| Logistics | Distance ≥ 0 |

---

## 15. Deployment Strategy

### Rollout Phases

1. **Core Framework** — deploy `industries` tables, registry, and module loader.
2. **Pilot Industry** — fully implement Health Suite.
3. **Second Wave** — Education, Church, Government.
4. **Third Wave** — Business, NGO, Agriculture, Retail.
5. **Fourth Wave** — Manufacturing, Logistics.
6. **Expansion** — additional industries via extension template.

### Configuration

```env
INDUSTRIES_ENABLED=health,education,church,government,business,ngo,agriculture,retail,manufacturing,logistics
DEFAULT_INDUSTRY=health
CROSS_ORG_BENCHMARKS_ENABLED=false
INDUSTRY_AI_TEMPLATES_DIR=industries/prompts
```

### Scaling

- Industry modules load lazily based on organization selection.
- ETL templates and AI prompts cached in Redis.
- KPI computation parallelized per industry module.
- Background jobs isolated per industry to prevent noisy neighbor issues.

---

## 16. Output Summary

1. **Complete Industry Framework** — shared platform + vertical modules.
2. **Architecture** — module pattern, data flow, extension points.
3. **Database Extensions** — `industries`, `industry_suites`, `organization_industry_settings`, `industry_kpis`, `industry_dashboards`, `industry_reports`, `industry_etl_templates`, `industry_workflows`, `industry_glossary`, `industry_role_templates`.
4. **API Extensions** — `/industries/*` endpoints and industry-specific routes.
5. **AI Strategies** — industry-aware prompts, forecast targets, recommendation rules, benchmarks.
6. **Workflow Designs** — approval chains and workflow templates per suite.
7. **Role Matrix & Permissions** — common roles, permission naming, role templates.
8. **KPI Catalog** — KPI schema and sample KPIs per industry.
9. **Report Catalog** — industry report templates.
10. **Dashboard Catalog** — industry dashboard templates.
11. **ETL Templates** — template structure and per-industry templates.
12. **Automation Rules** — rule engine and sample rules.
13. **Deployment Strategy** — phased rollout, configuration, scaling.

All specifications are enterprise-grade, modular, scalable, and ready for implementation.
