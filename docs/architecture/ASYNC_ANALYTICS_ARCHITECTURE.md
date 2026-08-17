# Async Analytics Architecture

## Overview

DataFlow uses a persistent background job system to handle long-running operations
(dataset workflow pipelines, ML experiments, report generation) without blocking
HTTP requests.

## Components

### Job Queue (`performance/queue.py`)

Two implementations, selected by configuration:

| Backend | Selection | Persistence | Workers |
|---------|-----------|-------------|---------|
| Redis | `REDIS_URL` configured | Redis-backed | Dedicated worker process |
| In-Memory | No Redis | In-process only | Same process |

The Redis-backed queue is required for production. The in-memory queue is used
for local development and serverless deployments where no worker exists.

### Job Service (`jobs/service.py`)

- `create_job()` — Creates a job record in the database and enqueues it
- `update_job_progress()` — Updates job status/progress from any process
- `get_job()` / `list_jobs()` — Read job state

Job states: `pending` → `running` → `completed` | `failed`

Jobs are persisted to the database (`jobs/models.py::Job`) immediately on
creation. This means job status survives API restarts — any process can read
the current state.

### Job Handlers (`jobs/handlers.py`)

Handlers are registered at startup via `register_builtin_handlers()`:

- `dataset_workflow` — Runs the full dataset intelligence pipeline
- Additional handlers can be registered by plugins/extensions

### Worker Entry Point (`performance/worker_entry.py`)

The dedicated worker process:
```bash
python -m performance.worker_entry
```

Runs in a separate container/process (see `docker-compose.prod.yml`).
Continuously polls the Redis queue and executes job handlers.

### Dataset Workflow Integration

When `REDIS_URL` is configured and the process is not serverless:

1. `POST /dataset-workflow/run` uploads the file to storage, creates a job, and returns `202 Accepted` with `job_id`
2. The worker picks up the job, downloads the file from storage, runs all pipeline stages
3. Each stage persists progress to `dataset_workflow_runs` table
4. Client polls `GET /dataset-workflow/{id}/status` or `GET /jobs/{job_id}` for progress

When no worker is available (serverless, local dev without Redis):

1. The pipeline runs synchronously in the request handler
2. Results are returned directly in the response

## Data Flow

```
Client → POST /dataset-workflow/run
  │
  ├─ [Redis available] → Save file to storage → Create Job → Enqueue → Return 202
  │                                                               │
  │                                          Worker picks up job ←┘
  │                                          Downloads file from storage
  │                                          Runs pipeline stages
  │                                          Persists state to DB
  │
  └─ [No Redis] → Parse file → Run pipeline synchronously → Return 200
```

## Configuration

```bash
# Required for async processing
REDIS_URL=redis://localhost:6379/0

# Storage backend for file persistence
STORAGE_BACKEND=local    # or: s3, r2, supabase
STORAGE_LOCAL_DIR=storage/files

# Worker settings
WORKER_CONCURRENCY=4     # Number of concurrent jobs
```

## Resilience

- **API restart**: Jobs in the database retain their status. Workers continue processing.
- **Worker restart**: In-progress jobs may need manual retry. Completed stages are preserved.
- **Network partition**: The Redis queue handles reconnection automatically.
- **Storage**: Files uploaded via workflow are stored in persistent object storage,
  not in memory, so they survive process restarts.
