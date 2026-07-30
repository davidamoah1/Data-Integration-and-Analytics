# Reporting

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Document the reporting module — report generation and export.

## Scope

Report creation, export formats, and scheduling.

## Audience

Analysts, product managers, and developers.

---

## 1. Overview

The reporting module allows users to generate reports from their data and export them in multiple formats.

## 2. Features

| Feature | Permission | Description |
|---------|------------|-------------|
| Generate reports | `reports.generate` | Create reports from datasets/dashboards |
| View reports | `reports.view` | View existing reports |
| Export reports | `reports.export` | Export to PDF, CSV, Excel |
| Schedule reports | `pipelines.execute` | Schedule recurring report generation |

## 3. Export Formats

| Format | Description |
|--------|-------------|
| PDF | Formatted document with charts and tables |
| CSV | Raw data export |
| Excel | Spreadsheet with formatting |

## 4. Backend

| Endpoint | Permission | Description |
|----------|------------|-------------|
| `GET /api/reports` | `reports.view` | List reports (org-scoped) |
| `POST /api/reports` | `reports.generate` | Generate report |
| `GET /api/reports/{id}` | `reports.view` | Get report |
| `GET /api/reports/{id}/export` | `reports.export` | Export report |

## 5. Scheduled Reports

Reports can be scheduled via the Scheduler module:
- Daily, weekly, monthly schedules
- Delivered via notification or download link
- Background job via APScheduler

## Related Documents

- [../workflows/report-generation.md](../workflows/report-generation.md) — Report workflow
- [../backend/background-jobs.md](../backend/background-jobs.md) — Background jobs
- [analytics.md](analytics.md) — Analytics Studio
