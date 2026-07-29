# DataFlow SDK Reference

## Python SDK

```python
from dataflow_sdk import DataFlowClient

client = DataFlowClient(api_key="dfk_...", base_url="http://localhost:8080")

# Datasets
result = client.datasets.upload("data.csv")
datasets = client.datasets.list()

# Analytics
dashboards = client.analytics.list_dashboards()
kpis = client.analytics.list_kpis()

# AI
answer = client.ai.ask("What are the top trends?")

# Workflows
workflows = client.workflows.list()

# Reports
reports = client.reports.list()
```

## JavaScript SDK

```javascript
const { DataFlowClient } = require('./dataflow-sdk');

const client = new DataFlowClient({
  apiKey: 'dfk_...',
  baseUrl: 'http://localhost:8080'
});

// Datasets
const result = await client.datasets.upload(file);
const datasets = await client.datasets.list();

// Analytics
const dashboards = await client.analytics.listDashboards();
const kpis = await client.analytics.listKpis();

// AI
const answer = await client.ai.ask('What are the top trends?');
```

## PHP SDK

```php
<?php
require 'dataflow-sdk.php';

$client = new DataFlowClient([
  'api_key' => 'dfk_...',
  'base_url' => 'http://localhost:8080'
]);

// Datasets
$result = $client->datasets->upload('/path/to/data.csv');
$datasets = $client->datasets->list();

// Analytics
$dashboards = $client->analytics->listDashboards();
$kpis = $client->analytics->listKpis();

// AI
$answer = $client->ai->ask('What are the top trends?');
```

## Environment Variables

All SDKs support environment variables:

| Variable | Description |
|----------|-------------|
| `DATAFLOW_API_KEY` | API key |
| `DATAFLOW_BASE_URL` | Base URL (default: http://localhost:8080) |
