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

Users can be managed via the **Administration → Users** page in the dashboard, or through the API:

```bash
# Create a new user (admin only)
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!", "full_name": "New User"}'
```

### Roles & Permissions

| Role | Description |
|------|-------------|
| `super_admin` | Full system access, bypasses all permission checks |
| `admin` | Organization management, user management, settings, branding |
| `analyst` | Data analysis, dashboard creation, ETL management, AI Copilot |
| `viewer` | Read-only access to dashboards and reports |

### User Management via Dashboard

Navigate to **Administration → Users** to:
- View all users in your organization
- Invite new users by email
- Assign roles (admin, analyst, viewer)
- View last login timestamps
- Deactivate users

## Subscription Management

### Plans

| Plan | Price Tier | Users | Dashboards | Pipelines | AI Queries/mo | Upload |
|------|-----------|-------|------------|-----------|----------------|--------|
| Free Trial | Free (14 days) | 5 | 10 | 5 | 100 | 50MB |
| Starter | Entry | 10 | 25 | 10 | 500 | 200MB |
| Professional | Mid | 50 | 100 | 50 | 5,000 | 1GB |
| Enterprise | Premium | 500 | 1,000 | 500 | 50,000 | 10GB |
| Government | Special | 1,000 | 2,000 | 1,000 | 100,000 | 50GB |

### Managing Subscriptions

Via the dashboard:
1. Navigate to **Administration → Organization → Subscription Status**
2. View current plan, limits, and trial end date
3. Click "Upgrade" to change plans

Via the API:
```bash
# View current subscription
curl -H "Authorization: Bearer <token>" http://localhost:8000/platform/subscription/current

# Upgrade plan
curl -X POST -H "Authorization: Bearer <token>" "http://localhost:8000/platform/subscription/upgrade?plan=professional"

# Cancel subscription
curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/platform/subscription/cancel

# Check feature access
curl -H "Authorization: Bearer <token>" "http://localhost:8000/platform/subscription/feature-check?feature=ai_copilot"

# Set feature flag override
curl -X PUT -H "Authorization: Bearer <token>" "http://localhost:8000/platform/subscription/feature-flag?feature=sso&enabled=true"
```

### Feature Flags

Admins can override feature access per organization:
- Enable features not in the current plan (e.g., for pilot customers)
- Disable features temporarily
- Feature flags take precedence over plan features

## Organization Branding

Navigate to **Administration → Branding** to customize:
- **Primary, Secondary, Accent Colors** — Used in charts and UI elements
- **Theme Mode** — Dark or Light
- **Company Name & Tagline** — Shown in reports and headers
- **Logo** — Upload PNG/SVG (displayed in dashboard header)
- **Report Header/Footer Text** — Custom text on generated reports
- **Custom CSS** — Advanced styling overrides

Via the API:
```bash
# Set branding
curl -X PUT -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8000/platform/branding \
  -d '{"primary_color": "#6366f1", "company_name": "My Org", "theme_mode": "dark"}'
```

## Audit Logs

### Viewing Audit Logs

Navigate to **Administration → Audit Logs** or use the API:

```bash
# View audit logs
curl -H "Authorization: Bearer <token>" "http://localhost:8000/audit/logs?pageSize=50"

# View security events
curl -H "Authorization: Bearer <token>" "http://localhost:8000/audit/security-logs?pageSize=50"

# View system logs
curl -H "Authorization: Bearer <token>" "http://localhost:8000/audit/system-logs?pageSize=50"
```

### Audit Log Types

| Log Type | Description |
|----------|-------------|
| Audit Log | User actions (login, data access, config changes) |
| Security Log | Security events (failed logins, lockouts, permission changes) |
| System Log | System events (startup, errors, pipeline status) |

## Observability

Navigate to **Observability** in the dashboard to monitor:
- **API Status** — Health check, record count, subsystem status
- **Login Activity** — Daily login trends over time
- **Audit Activity** — Recent user actions
- **Security Events** — Recent security incidents
- **System Logs** — Recent system messages

## Support Tools

Navigate to **Support** in the dashboard for:
- **Submit Ticket** — General feedback or contact support
- **Bug Report** — Structured bug reporting with reproduction steps
- **Feature Request** — Submit and track feature requests
- **Diagnostics** — Real-time system health (CPU, memory, disk, API status)

## Environment Variables

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
