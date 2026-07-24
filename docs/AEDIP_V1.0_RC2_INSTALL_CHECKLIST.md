# AEDIP v1.0.0 RC2 — Production Installation Checklist

Use this checklist when deploying AEDIP to production for the first time.

## Pre-Deployment

- [ ] Provision a Linux server (Ubuntu 22.04 LTS recommended) with at least 4 CPU cores and 8 GB RAM.
- [ ] Install Docker Engine 24+ and Docker Compose v2.
- [ ] Open ports 80 and 443 in the firewall.
- [ ] Register a domain name and point DNS A/AAAA records to the server.
- [ ] Create a strong JWT secret: `openssl rand -hex 32`.
- [ ] Generate dashboard admin and viewer passwords.

## Configuration

- [ ] Copy `.env.example` to `.env`.
- [ ] Set `DB_TYPE=mysql`.
- [ ] Fill in MySQL credentials (`MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`).
- [ ] Set `JWT_SECRET_KEY` to the generated secret.
- [ ] Set `API_KEY` to a strong random value for legacy integrations.
- [ ] Set `CORS_ORIGINS` to your dashboard and frontend domains (no `*` in production).
- [ ] Set `REDIS_URL=redis://redis:6379/0` for the production stack.
- [ ] Set `BACKUP_PATH=/app/backups` (already defaulted in `docker-compose.prod.yml`).
- [ ] Configure SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`).
- [ ] (Optional) Configure SMS, WhatsApp, or push notification providers.
- [ ] Update `deployment/nginx.conf`:
  - [ ] Replace `example.com` with your domain in the `server_name` directives.
  - [ ] Replace SSL certificate paths with your actual Let's Encrypt paths.

## SSL Certificates

- [ ] For first-time cert issuance, uncomment and run the certbot command in `docker-compose.prod.yml`.
- [ ] Ensure certificates exist at `./deployment/certbot-data/cert/live/<your-domain>/`.
- [ ] Restart nginx after certificates are in place.

## Deploy

- [ ] Run `docker compose -f docker-compose.prod.yml up -d`.
- [ ] Wait for all services to become healthy (`docker compose -f docker-compose.prod.yml ps`).
- [ ] Verify `https://<your-domain>/health` returns HTTP 200.
- [ ] Verify `https://<your-domain>/ready` returns HTTP 200.
- [ ] Verify `https://<your-domain>/health/detailed` shows all subsystems.

## First-Time Setup

- [ ] Access the dashboard at `https://<your-domain>/`.
- [ ] Log in with the seeded super admin credentials or create the first organization/admin via `/auth/signup`.
- [ ] Create the first organization.
- [ ] Upload the first dataset.
- [ ] Confirm metadata extraction, semantic mapping, KPIs, dashboards, and reports generate successfully.
- [ ] Trigger an on-demand backup via `POST /platform/backups` and verify it appears in `GET /platform/backups`.

## Post-Deployment

- [ ] Configure automated off-site backup replication (S3-compatible bucket or rsync).
- [ ] Set up log shipping and alerting for the API, dashboard, and database containers.
- [ ] Review and adjust `RATE_LIMIT_RPM` based on expected load.
- [ ] Schedule periodic disaster-recovery drills using backup restore verification.
- [ ] Keep Docker images and base images patched regularly.
