# Workflow API — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-28

All endpoints are prefixed with `/api/workflows`.

---

## 1. Discovery

### List node types

```http
GET /api/workflows/node-types
```

Returns all available node types with category and description.

---

## 2. Workflow definitions

### Create workflow

```http
POST /api/workflows
```

Body:

```json
{
  "name": "Sales ETL",
  "description": "Daily sales processing",
  "category": "etl",
  "nodes": [
    {"id": "source", "type": "read_csv", "config": {"path": "s3://bucket/sales.csv"}},
    {"id": "validate", "type": "validate_data", "config": {"dataset": "{{source.data}}", "dataset_name": "sales"}}
  ],
  "edges": [
    {"source": "source", "target": "validate"}
  ],
  "config": {}
}
```

### List workflows

```http
GET /api/workflows?category=etl
```

### Get workflow

```http
GET /api/workflows/{workflow_id}
```

### Update workflow

```http
PUT /api/workflows/{workflow_id}
```

Body: partial `WorkflowDefinitionUpdate`.

### Delete workflow

```http
DELETE /api/workflows/{workflow_id}
```

Soft delete.

---

## 3. Versions

### List versions

```http
GET /api/workflows/{workflow_id}/versions
```

### Create new version

```http
POST /api/workflows/{workflow_id}/versions
```

Body: same shape as workflow create.

### Publish version

```http
POST /api/workflows/{workflow_id}/versions/{version_id}/publish
```

Publishes the version and archives any previously published version.

### Archive version

```http
POST /api/workflows/{workflow_id}/versions/{version_id}/archive
```

---

## 4. Execution

### Execute workflow

```http
POST /api/workflows/{workflow_id}/execute
```

Body:

```json
{
  "version_id": 123,
  "trigger_type": "manual",
  "inputs": {}
}
```

If `version_id` is omitted, the published version is used.

### Get execution

```http
GET /api/workflows/executions/{execution_id}
```

### Cancel execution

```http
POST /api/workflows/executions/{execution_id}/cancel
```

### List executions

```http
GET /api/workflows/executions
GET /api/workflows/{workflow_id}/executions
```

Query params: `status`, `trigger_type`, `limit`, `offset`.

---

## 5. Lineage

### Get execution lineage

```http
GET /api/workflows/executions/{execution_id}/lineage
```

---

## 6. Templates

### List templates

```http
GET /api/workflows/templates?category=etl
```

### Create template

```http
POST /api/workflows/templates
```

### Import template as workflow

```http
POST /api/workflows/templates/{template_id}/import
```

Body:

```json
{
  "name": "Imported Sales ETL",
  "description": "Imported from template"
}
```

---

## 7. Clone and export

### Clone workflow

```http
POST /api/workflows/{workflow_id}/clone
```

Body:

```json
{"name": "Copy of Sales ETL"}
```

### Export workflow

```http
GET /api/workflows/{workflow_id}/export
```

Returns the latest version nodes, edges, and config as JSON.

---

## 8. Job queue

### List jobs

```http
GET /api/workflows/jobs?status=pending
```

---

## 9. Permissions

| Endpoint | Required permission |
| :--- | :--- |
| `GET /api/workflows` | `workflows.read` |
| `POST /api/workflows` | `workflows.write` |
| `PUT /api/workflows/{id}` | `workflows.write` |
| `DELETE /api/workflows/{id}` | `workflows.delete` |
| `POST /api/workflows/{id}/execute` | `workflows.execute` |
| `POST /api/workflows/{id}/versions/{id}/publish` | `workflows.publish` |
| `GET /api/workflows/executions` | `workflows.read` |
| `POST /api/workflows/executions/{id}/cancel` | `workflows.execute` |

`super_admin` bypasses all permission checks.
