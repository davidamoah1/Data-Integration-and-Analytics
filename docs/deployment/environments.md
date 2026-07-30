# Environments

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Document environment configuration for dev, staging, and production.

## Scope

All environment variables and configuration per environment.

## Audience

DevOps engineers and developers.

---

## 1. Environment Matrix

| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `DATABASE_URL` | `localhost:5432/dataflow` | Staging DB URL | Production DB URL |
| `JWT_SECRET_KEY` | Dev secret | Staging secret | Strong production secret |
| `CORS_ORIGINS` | `http://localhost:3000` | Staging URL | Production URL |
| `SEED_DEMO_DATA` | `true` (optional) | `true` (optional) | `false` |
| `DEBUG` | `1` | Not set | Not set |
| `VERCEL` | Not set | `1` (if on Vercel) | `1` (if on Vercel) |
| `RATE_LIMIT_RPM` | Not set | `120` | `120` |
| `MAX_REQUEST_BODY_BYTES` | Not set | `52428800` | `52428800` |

## 2. All Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | — | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | — | Yes | JWT signing secret |
| `CORS_ORIGINS` | `localhost` regex | No | Comma-separated allowed origins |
| `SEED_DEMO_DATA` | `false` | No | Enable demo data seeding |
| `VERCEL` | — | No | Set to `1` on Vercel |
| `DISABLE_STARTUP_TASKS` | — | No | Skip heavy startup tasks |
| `RATE_LIMIT_RPM` | `120` | No | Rate limit per minute |
| `MAX_REQUEST_BODY_BYTES` | `52428800` | No | Max request body (50MB) |
| `DEBUG` | — | No | Show detailed error messages |
| `PYTEST_RUNNING` | — | No | Disable rate limiting in tests |

## 3. Environment Setup

### Development
- Local PostgreSQL
- `DEBUG=1` for detailed errors
- `SEED_DEMO_DATA=true` for sample data
- No rate limiting during tests (`PYTEST_RUNNING=1`)

### Staging
- External or managed PostgreSQL
- Same configuration as production but with staging URLs
- `SEED_DEMO_DATA=true` for testing
- No `DEBUG` flag

### Production
- Managed PostgreSQL with backups
- Strong `JWT_SECRET_KEY`
- `SEED_DEMO_DATA=false`
- No `DEBUG` flag
- CORS restricted to production domains

## Related Documents

- [local-development.md](local-development.md) — Local development
- [production.md](production.md) — Production deployment
- [vercel.md](vercel.md) — Vercel deployment
