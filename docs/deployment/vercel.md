# Vercel Deployment

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Guide for deploying DataFlow on Vercel.

## Scope

Vercel serverless deployment configuration.

## Audience

DevOps engineers and developers.

---

## 1. Architecture on Vercel

- **Frontend**: Next.js deployed as Vercel static/SSR pages
- **Backend**: FastAPI deployed as Vercel serverless functions
- **Database**: External PostgreSQL (Vercel Postgres, Supabase, or external)
- **Root config**: `vercel.json` in repository root

## 2. Serverless Mode

When `VERCEL=1`, the application skips:
- Database table creation (`Base.metadata.create_all`)
- Default data seeding (`seed_default_data`)
- Demo data seeding
- Background scheduler startup
- Subscription initialization

These must be handled separately:
- Run `seed_default_data()` manually after database creation
- Use Vercel Cron Jobs for scheduled tasks
- Use external backup solution

## 3. Environment Variables (Vercel)

| Variable | Value | Notes |
|----------|-------|-------|
| `VERCEL` | `1` | Auto-set by Vercel |
| `DATABASE_URL` | External PostgreSQL URL | Required |
| `JWT_SECRET_KEY` | Strong secret | Required |
| `CORS_ORIGINS` | Frontend URL | Comma-separated |
| `DISABLE_STARTUP_TASKS` | `1` | Optional, skip heavy tasks |

## 4. Deployment Steps

1. Connect repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy
4. Run database seeding manually:
   ```bash
   # After first deploy, run seed script
   python -c "from authentication.services import seed_default_data; ..."
   ```

## 5. Limitations

- No background scheduler (use Vercel Cron)
- No persistent processes
- 50MB request body limit (Vercel default)
- Function timeout limits (10s on hobby, 60s on pro)

## Related Documents

- [local-development.md](local-development.md) — Local development
- [production.md](production.md) — Production checklist
- [environments.md](environments.md) — Environment configuration
- [../architecture/deployment-architecture.md](../architecture/deployment-architecture.md) — Deployment architecture
