# Data Lineage — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-28

---

## 1. Overview

Data lineage captures the complete provenance of data as it moves through the platform: from ingestion, through validation, transformation, AI analysis, semantic mapping, dashboards, reports, and exports.

Lineage records are created automatically during workflow execution by `workflows/lineage.py`.

---

## 2. Lineage model

Each lineage edge is stored in `workflow_lineage`:

| Field | Description |
| :--- | :--- |
| `execution_id` | Workflow execution that produced the edge |
| `organization_id` | Tenant scope |
| `source_type` | Type of source entity: `dataset`, `execution_step`, etc. |
| `source_id` | Identifier of the source entity |
| `target_type` | Type of target entity: `dataset`, `dashboard`, `report`, `export` |
| `target_id` | Identifier of the target entity |
| `transformation` | Operation that produced the edge |
| `meta` | Additional metadata (JSON) |

---

## 3. Provenance chain

A typical workflow produces the following lineage:

```
source:read_csv  ──► execution_step:source
execution_step:source ──► dataset:{exec}:source
dataset:{exec}:source ──► execution_step:validate
execution_step:validate ──► dataset:{exec}:validate
...
dataset:{exec}:export ──► export:csv
```

---

## 4. API

Retrieve lineage for an execution:

```http
GET /api/workflows/executions/{execution_id}/lineage
```

Response:

```json
[
  {
    "id": 1,
    "execution_id": "uuid",
    "source_type": "execution_step",
    "source_id": "read_csv",
    "target_type": "dataset",
    "target_id": "uuid:read_csv",
    "transformation": "read_csv",
    "meta": {},
    "created_at": "2026-07-28T00:00:00"
  }
]
```

---

## 5. Visualization

A frontend lineage graph can be built by treating `source_id` and `target_id` as vertices and records as directed edges. Transformations become edge labels.

---

## 6. Extending lineage

Custom nodes can call the lineage builder directly through the `WorkflowContext` if the context is extended to expose it, or by emitting standard output metadata that the engine translates into edges.
