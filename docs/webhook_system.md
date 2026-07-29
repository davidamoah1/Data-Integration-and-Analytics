# Webhook Event System

## Overview

The Webhook Event System delivers real-time event notifications to external endpoints.

## Supported Events

| Event | Description |
|-------|-------------|
| `dataset.uploaded` | Dataset uploaded |
| `pipeline.completed` | ETL pipeline completed |
| `pipeline.failed` | ETL pipeline failed |
| `workflow.failed` | Workflow execution failed |
| `dashboard.generated` | Dashboard auto-generated |
| `model.trained` | ML model trained |
| `report.exported` | Report exported |
| `alert.created` | Alert triggered |
| `connector.connected` | Connector connected |
| `api_key.created` | API key created |
| `api_key.revoked` | API key revoked |

## Webhook Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/webhooks/events` | List supported events |
| POST | `/webhooks` | Create subscription |
| GET | `/webhooks` | List subscriptions |
| DELETE | `/webhooks/{id}` | Delete subscription |
| GET | `/webhooks/{id}/deliveries` | Delivery history |
| POST | `/webhooks/{id}/redeliver/{delivery_id}` | Redeliver |

## Payload Signing

Every webhook delivery includes an `X-Webhook-Signature` header containing an HMAC-SHA256 signature:

```python
import hmac, hashlib

signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

## Delivery & Retry

- Maximum 3 delivery attempts
- Retry delays: 1min, 5min, 15min
- Delivery status: `pending`, `delivered`, `failed`, `retry`
- Full delivery history with response body and status code
