# Public API Platform

## Overview

The Public API Platform allows external developers to programmatically access DataFlow features via API keys.

## Authentication

All public API requests require an API key via the `X-API-Key` header:

```
X-API-Key: dfk_your_api_key_here
```

## API Key Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/platform/api-keys` | Create API key |
| GET | `/platform/api-keys` | List API keys |
| DELETE | `/platform/api-keys/{id}` | Revoke API key |
| POST | `/platform/api-keys/{id}/rotate` | Rotate API key |
| GET | `/platform/usage` | Usage statistics |
| GET | `/platform/usage/by-key` | Usage by API key |

## Scopes

| Scope | Access |
|-------|--------|
| `datasets` | Dataset upload and listing |
| `analytics` | Dashboards and KPIs |
| `ai` | AI Copilot |
| `workflows` | Workflow management |

## Public API Endpoints

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| POST | `/public/datasets/upload` | datasets | Upload dataset |
| GET | `/public/datasets` | datasets | List datasets |
| GET | `/public/analytics/dashboards` | analytics | List dashboards |
| GET | `/public/analytics/kpis` | analytics | List KPIs |
| POST | `/public/ai/ask` | ai | Ask AI Copilot |
| GET | `/public/workflows` | workflows | List workflows |
| GET | `/public/reports` | analytics | List reports |

## Rate Limiting

- Default: 1000 requests/hour per key
- Configurable per key
- Organization-level quotas

## Usage Tracking

All API calls are logged with:
- API key ID
- Organization ID
- Endpoint and method
- Response time
- Status code
- IP address
