# Automation Studio

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Document the Automation Studio for ETL pipelines and workflow automation.

## Scope

ETL pipelines, workflow management, and scheduling.

## Audience

Data engineers and automation specialists.

---

## 1. Overview

The Automation Studio provides ETL pipeline management, workflow automation, and scheduled job execution.

## 2. Features

| Feature | Permission | Description |
|---------|------------|-------------|
| Create pipelines | `pipelines.create` | Create ETL workflows |
| Execute pipelines | `pipelines.execute` | Run ETL pipelines |
| View pipelines | `pipelines.view` | View pipeline status |
| Import data | `etl.import` | Import data via pipelines |
| Export data | `etl.export` | Export data via pipelines |

## 3. Workflow Service

`workflows/service.py` demonstrates org-scoped access control:
- `_org_id()` — gets current user's org ID
- `_ensure_org_access(resource)` — verifies access to resource's org
- `_query_org_scoped()` — filters queries by org ID
- Super admins exempt from org checks

## 4. Key Routes

| Route | Description |
|------|-------------|
| `/workflows` | Workflow list |
| `/scheduler` | Job scheduling (placeholder) |

## 5. Backend Endpoints

| Endpoint | Permission | Description |
|----------|------------|-------------|
| `GET /api/workflows` | Authenticated | List workflows (org-scoped) |
| `POST /api/workflows` | `pipelines.create` | Create workflow |
| `POST /api/workflows/{id}/execute` | `pipelines.execute` | Execute workflow |
| `GET /api/scheduler` | Authenticated | List scheduled jobs |

## Related Documents

- [../workflows/etl-pipeline.md](../workflows/etl-pipeline.md) — ETL workflow
- [../architecture/data-flow.md](../architecture/data-flow.md) — Data flow
- [../backend/services.md](../backend/services.md) — Service layer
