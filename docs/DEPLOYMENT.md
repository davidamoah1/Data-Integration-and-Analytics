# Deployment Guide

## Prerequisites

- Docker 24.0+ and Docker Compose 2.20+
- MySQL 8.0 (or use the included docker-compose MySQL service)
- Python 3.10+ (for local development)

## Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd etl_project
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your production secrets
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   ```

## Environment Variables

### Required for Production

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_TYPE` | Database type | `mysql` |
| `MYSQL_HOST` | MySQL host | `db` |
| `MYSQL_DATABASE` | Database name | `etl_db` |
| `MYSQL_USER` | Database user | `etl_user` |
| `MYSQL_PASSWORD` | Database password | (strong password) |
| `JWT_SECRET_KEY` | JWT signing secret | (32+ char random string) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:8501` |
| `API_KEY` | API key for legacy endpoints | (strong random key) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_RPM` | 120 | Requests per minute per IP |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | text | `text` or `json` |
| `AI_DEFAULT_PROVIDER` | openai | Default AI provider |
| `AI_CACHE_ENABLED` | true | Enable AI response caching |

## Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment**
   ```bash
   # .env file
   DB_TYPE=sqlite
   SQLITE_DB_PATH=database/etl_database.db
   JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
   CORS_ORIGINS=*
   ```

3. **Run the API**
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run the dashboard**
   ```bash
   streamlit run dashboard/app.py --server.port 8501
   ```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **Lint** — `ruff check .`
2. **Format** — `black --check .`
3. **Tests** — `pytest -q` with SQLite

## Backup Strategy

- **Database**: Use MySQL's `mysqldump` or volume snapshots
- **Logs**: Rotating file handler (5MB x 5 files) in `logs/`
- **Configuration**: `.env` file should be backed up securely

## Rollback Procedure

1. **Application**: `git checkout <previous-tag> && docker-compose up -d --build`
2. **Database**: Restore from `mysqldump` backup
3. **Verify**: Check `/health` and `/ready` endpoints

## Health Checks

| Endpoint | Purpose | Expected Status |
|----------|---------|-----------------|
| `/health` | Liveness probe | 200 (always if process is up) |
| `/ready` | Readiness probe | 200 (all subsystems ready) or 503 |
| `/metrics` | Platform metrics | 200 with JSON metrics |

## Production Deployment Checklist

### Pre-Deployment

- [ ] Set `DB_TYPE=mysql` (not SQLite for production)
- [ ] Set strong `JWT_SECRET_KEY` (32+ random characters)
- [ ] Set strong `API_KEY`
- [ ] Configure `CORS_ORIGINS` to only allow your dashboard URL
- [ ] Set `RATE_LIMIT_RPM` appropriately (default: 120)
- [ ] Configure AI provider API keys
- [ ] Set up MySQL with automated backups
- [ ] Configure HTTPS reverse proxy (nginx, Caddy, or Traefik)
- [ ] Set up log rotation and monitoring
- [ ] Create super admin account: `python init_super_admin.py`

### Post-Deployment

- [ ] Verify `/health` returns 200
- [ ] Verify `/ready` returns 200
- [ ] Verify dashboard loads at the configured URL
- [ ] Test login with demo credentials
- [ ] Seed demo data: `POST /platform/demo/seed`
- [ ] Verify subscription auto-created for demo org
- [ ] Test data upload (CSV)
- [ ] Test AI Copilot
- [ ] Test each industry pack dashboard
- [ ] Verify audit logs are recording
- [ ] Set up regular database backups
- [ ] Configure monitoring alerts

### Scaling Considerations

- **Database**: Use MySQL with connection pooling for production
- **API**: Run multiple API instances behind a load balancer
- **Dashboard**: Streamlit Community Cloud or self-hosted with sticky sessions
- **File Storage**: Use S3 or similar for uploaded files in production
- **AI**: Consider caching AI responses to reduce API costs
- **Rate Limiting**: Adjust `RATE_LIMIT_RPM` based on your user count
