# AEDIP Administrator Guide

## Overview

This guide covers administration tasks for the AEDIP Enterprise Data & Decision Intelligence Platform.

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8.0+ (or SQLite for development)
- Docker & Docker Compose (for containerized deployment)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd etl_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Start the dashboard (separate terminal)
streamlit run dashboard/app.py
```

### Docker Deployment

```bash
docker-compose up -d
```

Services:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8501
- **MySQL**: localhost:3306

## User Management

### Creating Users

Users are managed through the authentication API:

```bash
# Create a new user (admin only)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!", "full_name": "New User"}'
```

### Roles & Permissions

| Role | Description |
|------|-------------|
| `super_admin` | Full system access, bypasses all permission checks |
| `admin` | Organization management, user management, settings |
| `analyst` | Data analysis, dashboard creation, ETL management |
| `viewer` | Read-only access to dashboards and reports |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_TYPE` | Database type (`mysql` or `sqlite`) | `sqlite` |
| `DB_URL` | Database connection URL | - |
| `JWT_SECRET_KEY` | JWT signing secret | Required in production |
| `API_KEY` | API key for external access | Required |
| `RATE_LIMIT_RPM` | Rate limit (requests per minute) | `60` |
| `AUTH_ADMIN_PASSWORD` | Admin dashboard password | `admin123` |
| `AUTH_VIEWER_PASSWORD` | Viewer dashboard password | `viewer123` |

## ETL Pipeline Management

### Creating a Pipeline

1. Navigate to the ETL section in the API
2. Define source, transformations, and destination
3. Schedule or trigger manually

### Monitoring Jobs

- **API**: `GET /api/v1/etl/jobs`
- **Dashboard**: View job status in the ETL monitoring panel

## AI Provider Configuration

1. Navigate to `Settings > AI Providers` (API: `/ai/providers`)
2. Add provider credentials (API keys are encrypted at rest)
3. Set default provider and model
4. Test connectivity

## Security Checklist

- [ ] Change default admin/viewer passwords
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Set strong `API_KEY`
- [ ] Enable HTTPS (reverse proxy)
- [ ] Configure CORS origins
- [ ] Review rate limiting settings
- [ ] Enable audit logging
- [ ] Set up database backups

## Backup & Recovery

### Database Backup

```bash
# MySQL
mysqldump -u root -p aedip_db > backup_$(date +%Y%m%d).sql

# Restore
mysql -u root -p aedip_db < backup_20260101.sql
```

### Application Backup

- Export `.env` configuration
- Backup uploaded files in `data/raw/`
- Backup AI conversation history if needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check `DB_URL` and network connectivity |
| JWT errors | Verify `JWT_SECRET_KEY` is set and consistent |
| AI provider errors | Check API keys in provider settings |
| ETL pipeline failures | Check logs at `logs/` directory |
| Dashboard not loading | Verify API is running and accessible |
