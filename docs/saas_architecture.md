# SaaS Architecture

## Overview

DataFlow is a multi-tenant SaaS platform for enterprise data intelligence, designed to serve thousands of organizations across Ghana, Africa, and globally.

## Architecture Principles

- **Multi-tenant isolation**: Every organization's data is isolated at the query level via `organization_id` filtering
- **RBAC**: Role-based access control with super_admin, org_admin, and user roles
- **Subscription-gated features**: Feature flags enforce plan-based access
- **Horizontal scalability**: Stateless backend, database-per-tenant option for enterprise
- **Pluggable providers**: Payment, email, SMS providers are abstracted for regional customization

## System Components

### Core Platform
- **ETL Engine**: Data extraction, transformation, loading
- **AI Copilot**: Natural language data queries
- **ML Engine**: Forecasting, classification, clustering
- **Dashboard Engine**: Real-time analytics dashboards
- **Workflow Engine**: Automated data pipelines
- **Semantic Layer**: Business metric definitions
- **Metadata Catalog**: Dataset and column metadata

### Ecosystem
- **Connector Framework**: 22+ data source connectors
- **Public API Platform**: API key management and usage tracking
- **Webhook System**: Event-driven integrations
- **Plugin Marketplace**: Installable extensions
- **Industry Packages**: Pre-built solutions (healthcare, education, banking, agriculture)

### SaaS Layer
- **Subscription & Billing**: 5-tier plans (Free, Starter, Professional, Business, Enterprise)
- **Feature Flags**: Plan-gated and per-organization feature access
- **Onboarding**: Guided 9-step setup flow
- **Customer Success**: Health scoring and support tickets
- **Admin Portal**: Super admin tenant management
- **Notifications**: Multi-channel (in-app, email, SMS, webhook)

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TailwindCSS |
| Backend | FastAPI, Python 3.12 |
| Database | MySQL (production), SQLite (development) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT + RBAC |
| Deployment | Vercel (frontend), Hostinger VPS (backend) |

## Tenant Isolation Model

```
Request → JWT Auth → organization_id extracted
         → All queries filtered by organization_id
         → Super admin bypasses filter (with audit logging)
         → Cross-tenant access raises 403
```

## Database Schema

All organization-owned tables include an `organization_id` column:
- `datasets`, `dashboards`, `kpis`, `reports`
- `workflow_definitions`, `workflow_executions`
- `ecosystem_connectors`, `ecosystem_api_keys`
- `ecosystem_webhook_subscriptions`, `ecosystem_plugin_installations`
- `saas_subscriptions`, `saas_usage_records`, `saas_onboarding_records`
