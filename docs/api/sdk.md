# SDK

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Planned  
> **Owner**: Backend Lead

---

## Purpose

SDK usage guide for programmatic API access.

## Scope

Official SDKs for Python and JavaScript.

## Audience

API consumers and developers.

---

> **⚠️ Planned**: Official SDKs are not yet implemented. This document describes the planned design.

## 1. Planned SDKs

| Language | Package | Status |
|----------|---------|--------|
| Python | `dataflow-python` | ⚠️ Planned |
| JavaScript/TypeScript | `dataflow-js` | ⚠️ Planned |

## 2. Python SDK (Planned)

```python
from dataflow import DataFlowClient

client = DataFlowClient(
    base_url="https://api.dataflow.io",
    api_key="df_abc123"  # Future: API key auth
)

# List users
users = client.users.list(page=1, page_size=20)

# Create invitation
client.invitations.create(
    email="invite@example.com",
    role_name="data_analyst"
)
```

## 3. JavaScript SDK (Planned)

```typescript
import { DataFlowClient } from 'dataflow-js';

const client = new DataFlowClient({
  baseUrl: 'https://api.dataflow.io',
  apiKey: 'df_abc123'
});

// List users
const users = await client.users.list({ page: 1, pageSize: 20 });

// Create invitation
await client.invitations.create({
  email: 'invite@example.com',
  roleName: 'data_analyst'
});
```

## 4. Current Alternative

Until SDKs are available, use direct HTTP requests:

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("https://api.dataflow.io/api/users", headers=headers)
```

## Related Documents

- [authentication.md](authentication.md) — API authentication
- [examples.md](examples.md) — API examples
- [openapi.md](openapi.md) — OpenAPI spec
