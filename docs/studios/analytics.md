# Analytics Studio

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Document the Analytics Studio — dashboards, KPIs, and visualizations.

## Scope

Analytics module features and capabilities.

## Audience

Product managers, analysts, and developers.

---

## 1. Overview

The Analytics Studio is the primary data visualization module. Users create dashboards with widgets, KPIs, and charts from their uploaded datasets.

## 2. Features

| Feature | Permission | Description |
|---------|------------|-------------|
| View dashboards | `dashboard.view` | View existing dashboards |
| Create dashboards | `dashboard.manage` | Create and edit dashboards |
| View analytics | `analytics.view` | View KPIs and analytics pages |
| Manage analytics | `analytics.manage` | Create and manage KPIs |
| Export analytics | `analytics.export` | Export dashboard data |

## 3. Key Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/analytics` | Analytics page | Dashboard builder and viewer |

## 4. Backend

| Endpoint | Permission | Description |
|----------|------------|-------------|
| `GET /api/analytics` | `analytics.view` | List analytics |
| `POST /api/analytics` | `analytics.manage` | Create analytics |
| `GET /api/dashboards` | `dashboard.view` | List dashboards |
| `POST /api/dashboards` | `dashboard.manage` | Create dashboard |

## Related Documents

- [../workflows/dashboard-generation.md](../workflows/dashboard-generation.md) — Dashboard workflow
- [../architecture/data-flow.md](../architecture/data-flow.md) — Data flow
- [../governance/permission-matrix.md](../governance/permission-matrix.md) — Permissions
