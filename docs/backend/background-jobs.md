# Background Jobs

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Document background jobs and schedulers.

## Scope

APScheduler configuration, scheduled tasks, and serverless considerations.

## Audience

Backend developers and DevOps engineers.

---

## 1. Scheduler

- **Library**: APScheduler
- **Implementation**: `scheduler/report_scheduler.py:ReportScheduler`
- **Started**: During application lifespan (non-serverless only)
- **Stored**: `app.state.report_scheduler`

## 2. Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily backup | 02:00 UTC | `BackupService.create_backup()` |
| Report generation | Configurable | Scheduled report generation |

## 3. Serverless Mode

On Vercel (`VERCEL=1`), the scheduler is **not started**. Background jobs must be handled by:
- Vercel Cron Jobs
- External cron service
- Queue-based processing (future)

## 4. Key Files

| File | Purpose |
|------|---------|
| `scheduler/report_scheduler.py` | `ReportScheduler` class |
| `scheduler/routes.py` | Scheduler API routes |
| `scheduler/models.py` | Scheduled job models |
| `services/backup_service.py` | Backup service |

## Related Documents

- [../architecture/system-design.md](../architecture/system-design.md) — System design
- [../deployment/vercel.md](../deployment/vercel.md) — Vercel deployment
- [../operations/maintenance.md](../operations/maintenance.md) — Maintenance tasks
