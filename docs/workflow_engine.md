# Workflow Engine — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-28

---

## 1. Overview

The DataFlow Workflow Engine is a reusable, tenant-isolated orchestration system for defining and executing data pipelines as directed acyclic graphs (DAGs). It integrates ingestion, validation, transformation, AI analysis, semantic mapping, dashboard/report generation, exports, and notifications into a single execution model.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Workflow Definition                      │
│  (name, description, organization, active/inactive)          │
└──────────────────────┬────────────────────────────────────────┘
                       │ has many
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Workflow Version (immutable)                │
│  status: draft | published | archived                          │
│  nodes[]  edges[]  config{}                                    │
└──────────────────────┬────────────────────────────────────────┘
                       │ executed as
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Workflow Execution                          │
│  execution_id, status, metrics, errors, lineage, ai_summary  │
└──────────────────────┬────────────────────────────────────────┘
                       │ queued as
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       Workflow Job                            │
│  status, retry_count, scheduled/started/completed_at          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Nodes

A workflow is composed of nodes. Each node has a unique `id`, a `type`, a `config`, and optional `inputs` references.

### 3.1 Built-in node types

| Category | Node types |
| :--- | :--- |
| **Sources** | `read_csv`, `read_excel`, `read_sql`, `read_rest`, `read_sftp` |
| **Processing** | `validate_data`, `clean_data`, `transform_data`, `aggregate_data`, `merge_data`, `join_data`, `execute_sql`, `execute_python` |
| **Intelligence** | `ai_analysis`, `semantic_mapping`, `metadata_generation`, `dashboard_generation`, `report_generation` |
| **Export** | `export_dataset`, `export_csv`, `export_excel`, `export_pdf`, `save_dataset`, `archive_dataset` |
| **Notification** | `send_email`, `send_sms`, `send_webhook` |
| **Control** | `approval_step`, `manual_review` |

### 3.2 Node result

Every node returns a `NodeResult`:

```json
{
  "status": "completed | failed | skipped | pending_approval",
  "rows_processed": 1000,
  "rows_failed": 0,
  "errors": [],
  "warnings": [],
  "metadata": {}
}
```

### 3.3 Input references

Nodes can reference upstream data with template syntax:

```json
{
  "dataset": "{{source.data}}"
}
```

### 3.4 Custom nodes

Register custom node factories at runtime:

```python
from workflows.nodes import register_node, WorkflowNode, NodeResult

class MyCustomNode(WorkflowNode):
    NODE_TYPE = "custom_action"
    def run(self, ctx):
        return NodeResult(status="completed", data={"ok": True})

register_node("custom_action", lambda nid, cfg: MyCustomNode(nid, cfg))
```

---

## 4. Execution Model

The engine (`workflows/engine.py`) executes a workflow version:

1. Builds a dependency graph from `edges`.
2. Runs nodes with all parents satisfied.
3. Supports parallel execution of independent nodes.
4. Applies per-node retry policy and timeout.
5. Records lineage edges between steps.
6. Stores full execution state, metrics, and errors.

### 4.1 Retry policy

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_seconds": 1.0,
    "backoff_multiplier": 2.0,
    "timeout_seconds": 60
  }
}
```

### 4.2 Statuses

`pending`, `running`, `completed`, `failed`, `retrying`, `cancelled`, `paused`

---

## 5. Lineage

During execution the engine emits lineage edges (`workflows/lineage.py`) describing the provenance chain from source datasets through transformations to outputs.

Retrieve lineage for an execution:

```http
GET /api/workflows/executions/{execution_id}/lineage
```

---

## 6. Notification integration

After each execution, the triggering user receives an in-app notification with the execution status.

---

## 7. Python service usage

```python
from workflows.service import WorkflowService
from workflows.schemas import WorkflowDefinitionCreate

service = WorkflowService(db, current_user)
wf = service.create_definition(
    WorkflowDefinitionCreate(
        name="Daily Sales ETL",
        nodes=[...],
        edges=[...],
    )
)
version = service.publish_version(wf.id, wf.versions[0].id)
execution = service.execute_workflow(wf.id, WorkflowExecutionCreate())
```
