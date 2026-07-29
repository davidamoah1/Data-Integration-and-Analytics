# Integration Framework

## Overview

The DataFlow Integration Framework provides a plugin-based architecture for connecting external data sources to the platform.

## Architecture

```
ConnectorRegistry (singleton)
├── Database Connectors: PostgreSQL, MySQL, SQL Server, Oracle, MongoDB
├── File Connectors: CSV, Excel, JSON, XML, Parquet
├── Cloud Storage: Amazon S3, Google Drive, OneDrive, Dropbox
├── API Connectors: REST, GraphQL, Webhook
└── Africa-First: Mobile Money, Bank API, Hospital System, Student Info System, Gov Open Data
```

## Creating a Connector

### 1. Implement BaseConnector

```python
from connectors.base import BaseConnector, ConnectorRegistry

@ConnectorRegistry.register
class MyConnector(BaseConnector):
    type_code = "my_connector"
    display_name = "My Connector"
    category = "api"
    description = "Connect to my custom API"

    def test_connection(self) -> dict:
        return {"success": True, "message": "OK"}

    def extract_data(self, query=None) -> pd.DataFrame:
        return pd.DataFrame()
```

### 2. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/connectors/types` | List all connector types |
| GET | `/connectors/types/africa` | List Africa-first connectors |
| GET | `/connectors` | List org connectors |
| POST | `/connectors` | Create connector instance |
| GET | `/connectors/{id}` | Get connector details |
| PUT | `/connectors/{id}` | Update connector |
| DELETE | `/connectors/{id}` | Delete connector |
| POST | `/connectors/{id}/test` | Test connection |
| POST | `/connectors/{id}/extract` | Extract data |
| GET | `/connectors/{id}/executions` | Execution history |

## Organization Isolation

All connector operations are scoped to the authenticated user's organization.
