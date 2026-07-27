# Dataset Intelligence API

## Base URL

```
http://localhost:8000/dataset-workflow
```

## Endpoints

### POST `/run`

Upload a dataset and run the full intelligence workflow.

**Parameters:**
- `file` (form, required): CSV or Excel file
- `admin_confirmed` (query, optional): Whether admin confirmed industry detection (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "uuid",
    "dataset_name": "dataset.csv",
    "current_stage": "analysis_complete",
    "is_complete": true,
    "has_errors": false,
    "stages": {
      "uploaded": { "stage": "uploaded", "status": "completed", "duration_seconds": 0.001, "result": { "row_count": 1000, "column_count": 15 } },
      "validated": { "stage": "validated", "status": "completed", "result": { "is_valid": true, "issues": [] } },
      "profiled": { "stage": "profiled", "status": "completed", "result": { "row_count": 1000, "overall_quality_score": 85.2, "columns": [...] } },
      "quality_checked": { "stage": "quality_checked", "status": "completed", "result": { "score": { "overall": 85.2, "grade": "B" }, "findings": [...] } },
      "industry_identified": { "stage": "industry_identified", "status": "completed", "result": { "industry": "healthcare", "confidence": 92.5 } },
      "insights_generated": { "stage": "insights_generated", "status": "completed", "result": { "total_insights": 8, "executive_summary": "..." } },
      "dashboard_ready": { "stage": "dashboard_ready", "status": "completed", "result": { "recommended": true, "recommended_charts": [...] } }
    }
  }
}
```

### GET `/{workflow_id}/status`

Get the current workflow status.

### GET `/{workflow_id}/profile`

Get the dataset profile (column stats, correlations, sensitive data, PK candidates).

### GET `/{workflow_id}/quality`

Get the quality report (score, findings, recommendations).

### GET `/{workflow_id}/semantic`

Get the semantic analysis (column-to-entity mappings).

### GET `/{workflow_id}/industry`

Get the industry detection result.

**Response:**
```json
{
  "success": true,
  "data": {
    "industry": "healthcare",
    "confidence": 92.5,
    "detected_entities": ["patient", "doctor", "diagnosis", "ward"],
    "alternative_candidates": [{ "industry": "banking", "votes": 3.0 }],
    "needs_confirmation": false
  }
}
```

### GET `/{workflow_id}/metadata`

Get the generated table metadata.

### GET `/{workflow_id}/knowledge`

Get the extracted business knowledge (knowledge graph, KPIs).

### GET `/{workflow_id}/insights`

Get the AI-generated insights.

**Response:**
```json
{
  "success": true,
  "data": {
    "insights": [
      {
        "type": "trend",
        "severity": "positive",
        "title": "Billing Amount is increasing",
        "description": "Billing Amount shows a 45.2% increasing trend...",
        "recommendation": "Monitor billing trend and adjust strategy accordingly."
      }
    ],
    "executive_summary": "Dataset contains 1,000 records...",
    "total_insights": 8
  }
}
```

### GET `/{workflow_id}/dashboard`

Get the dashboard recommendations.

**Response:**
```json
{
  "success": true,
  "data": {
    "recommended": true,
    "industry": "healthcare",
    "industry_confidence": 92.5,
    "reasoning": "Industry detected as 'Healthcare' with 93% confidence...",
    "available_measures": [{ "column": "billing_amount", "display": "Billing" }],
    "available_dimensions": [{ "column": "ward", "display": "Ward" }],
    "recommended_charts": [
      { "type": "line_chart", "title": "Billing over time", "reasoning": "Track billing trends" },
      { "type": "kpi_card", "title": "Total Billing", "reasoning": "Key metric: Billing" }
    ],
    "actions": {
      "accept": "Accept the recommended dashboard as-is",
      "customize": "Customize which charts and KPIs to include",
      "reject": "Reject and build dashboard manually"
    }
  }
}
```

### GET `/{workflow_id}/summary`

Get the final analysis summary.

### POST `/{workflow_id}/retry/{stage}`

Retry a failed workflow stage.

**Path Parameters:**
- `workflow_id`: Workflow UUID
- `stage`: Stage name (e.g., `profiled`, `quality_checked`)

## Error Responses

```json
{
  "detail": "Workflow not found"
}
```

```json
{
  "detail": "Failed to read file: Invalid CSV format"
}
```
