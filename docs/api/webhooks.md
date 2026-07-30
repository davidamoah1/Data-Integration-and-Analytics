# Webhooks

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Webhook events and configuration.

## Scope

Outbound webhook events and subscription management.

## Audience

API consumers and integration developers.

---

## 1. Overview

DataFlow supports outbound webhooks for event notifications. When configured events occur, the platform sends HTTP POST requests to registered webhook URLs.

## 2. Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `user.created` | New user created | User object |
| `user.deleted` | User soft-deleted | User ID |
| `organization.created` | New org created | Organization object |
| `invitation.accepted` | Invitation accepted | User + invitation |
| `dataset.uploaded` | Dataset uploaded | Dataset object |
| `report.generated` | Report generated | Report object |

## 3. Webhook Configuration

Webhooks are managed via the Ecosystem module:

| Endpoint | Permission | Description |
|----------|------------|-------------|
| `GET /api/webhooks` | Authenticated | List webhooks |
| `POST /api/webhooks` | Authenticated | Register webhook |
| `PUT /api/webhooks/{id}` | Authenticated | Update webhook |
| `DELETE /api/webhooks/{id}` | Authenticated | Delete webhook |

## 4. Webhook Payload

```json
{
  "event": "user.created",
  "timestamp": "2026-07-30T12:00:00Z",
  "organization_id": 123,
  "data": {
    "id": 456,
    "email": "newuser@example.com",
    "full_name": "New User"
  }
}
```

## 5. Security

- Webhook URLs must be HTTPS
- Payloads signed with HMAC (future)
- Retry on failure (3 attempts with backoff)
- Timeout: 10 seconds

## Related Documents

- [authentication.md](authentication.md) — API authentication
- [../architecture/integrations.md](../architecture/integrations.md) — Integrations
- [../integrations/future-integrations.md](../integrations/future-integrations.md) — Future integrations
