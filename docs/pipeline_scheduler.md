# Pipeline Scheduler — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-28

---

## 1. Overview

The Pipeline Scheduler is responsible for triggering workflow executions based on time or events. The current release provides a foundation using the existing `scheduler/` module and a manual execution API; event triggers will be added incrementally.

---

## 2. Supported triggers

| Trigger | Status | Notes |
| :--- | :--- | :--- |
| Manual API execution | ✅ | `POST /api/workflows/{id}/execute` |
| Scheduled / cron | 🔄 | Reuse `scheduler` module; workflow cron trigger planned |
| Webhook | ✅ | Generic webhook endpoint can be wired to execute workflows |
| File uploaded | 🔄 | Future: ETL upload event hook |
| Dataset approved | 🔄 | Future: validation approval event hook |
| Folder monitored | 🔄 | Future: poller or SFTP folder watcher |

---

## 3. Cron scheduling

Workflow versions can be scheduled by creating a `ScheduledReport` (or a future `WorkflowSchedule`) that stores a cron expression and the workflow/version id. A background worker evaluates due schedules and calls the execution API.

Example cron expressions:

- `0 8 * * 1` — Every Monday at 8:00 AM
- `0 0 * * *` — Daily at midnight
- `*/15 * * * *` — Every 15 minutes

---

## 4. Webhook trigger

A lightweight webhook receiver can be added:

```http
POST /api/workflows/{workflow_id}/webhook/{secret}
```

The receiver validates a shared secret and starts an execution using the published version of the workflow.

---

## 5. Execution queue

All executions create a `WorkflowJob` entry. In production, a worker pool polls the queue:

```sql
SELECT * FROM workflow_jobs
WHERE status = 'pending' AND scheduled_at <= NOW()
ORDER BY priority DESC, created_at ASC;
```

Workers claim jobs by setting `status = 'running'` and `worker_id`.

---

## 6. Retry and back-off

Scheduled or triggered executions inherit the retry policy defined on each node. If a workflow fails, the job record tracks `retry_count` against `max_retries`.

---

## 7. Operations

- List schedules: `GET /api/scheduler/reports`
- Create schedule: `POST /api/scheduler/reports`
- Toggle schedule: `POST /api/scheduler/reports/{id}/toggle`
- List jobs: `GET /api/workflows/jobs`
- View execution history: `GET /api/workflows/executions`
