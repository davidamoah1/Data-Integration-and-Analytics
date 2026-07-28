# Workflow Designer — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-28

---

## 1. Overview

The Workflow Designer is the visual user interface for building DataFlow workflows. Although the current backend phase focuses on the engine and API, the backend is designed to support a drag-and-drop canvas where users can compose nodes into a directed graph.

---

## 2. Data Model for the Canvas

A workflow version is stored as JSON nodes and edges:

```json
{
  "nodes": [
    {
      "id": "source-1",
      "type": "read_csv",
      "label": "Upload Sales CSV",
      "config": {"path": "/uploads/sales.csv"},
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "validate-1",
      "type": "validate_data",
      "label": "Validate",
      "config": {"dataset": "{{source-1.data}}"},
      "position": {"x": 300, "y": 100}
    }
  ],
  "edges": [
    {"source": "source-1", "target": "validate-1"}
  ]
}
```

---

## 3. Supported interactions

- **Drag nodes** from a palette onto the canvas.
- **Connect nodes** by dragging from an output handle to an input handle.
- **Branch logic** by connecting one source node to multiple target nodes.
- **Merge branches** by connecting multiple sources to one target node.
- **Conditional execution** by adding an `edge.condition` expression evaluated against the execution context.
- **Parallel execution** is automatic for independent nodes.
- **Loop execution** is not yet supported; planned for future iterations.

---

## 4. Node palette categories

| Category | Examples |
| :--- | :--- |
| Sources | Read CSV, Excel, SQL, REST, SFTP |
| Processing | Validate, Clean, Transform, Aggregate, Merge, SQL, Python |
| Intelligence | AI Analysis, Semantic Mapping, Metadata, Dashboard, Report |
| Export | Export CSV/Excel/PDF, Save Dataset, Archive |
| Notification | Email, SMS, Webhook |
| Control | Approval Step, Manual Review |

---

## 5. Validation

Before publishing, the designer should validate:

- All node ids are unique.
- Edges reference existing node ids.
- The graph has no cycles.
- Required node config fields are present.
- Every non-source node has at least one incoming edge.

The backend can expose `POST /api/workflows/{id}/versions/{version_id}/validate` if needed.

---

## 6. Execution feedback

When an execution runs, the UI can poll `GET /api/workflows/executions/{execution_id}` and color nodes by status:

- Grey: pending
- Blue: running
- Green: completed
- Red: failed
- Yellow: retrying
- Orange: paused / pending approval

Each node result includes `duration_seconds`, `rows_processed`, and `errors`.

---

## 7. Templates

The designer can seed new workflows from `WorkflowTemplate` records via `GET /api/workflows/templates` and `POST /api/workflows/templates/{id}/import`.
