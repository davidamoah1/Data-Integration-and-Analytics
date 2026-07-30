# Caching

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Backend Lead

---

## Purpose

Document the caching strategy (current and planned).

## Scope

All caching layers and mechanisms.

## Audience

Backend developers and architects.

---

## 1. Current State

> **⚠️ No caching layer implemented yet.**

Currently, every API request:
- Decodes JWT to get user info
- Queries database for user's roles
- Queries database for user's permissions
- Queries database for the requested resource

This results in multiple database queries per request.

## 2. Planned Caching

### Redis (Planned)

| Cache Key | TTL | Purpose |
|-----------|-----|---------|
| `user:{id}:roles` | 5 min | Role lookup per request |
| `user:{id}:permissions` | 5 min | Permission lookup per request |
| `org:{id}:settings` | 10 min | Organization settings |
| `dashboard:{id}:data` | 1 min | Dashboard query results |
| `session:{token}` | Until expiry | Session validation |

### JWT Claims (Current)

JWT tokens include `roles` and `permissions` claims, reducing some database queries. However, the backend still loads fresh data from the database for security.

## 3. Frontend Caching

- Next.js built-in caching for static pages and API routes
- SWR or React Query not currently used
- localStorage for auth tokens and user preferences

## Related Documents

- [../architecture/scalability.md](../architecture/scalability.md) — Scalability strategy
- [../database/optimization.md](../database/optimization.md) — Database optimization
- [services.md](services.md) — Service layer
