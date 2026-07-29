# Production Deployment Guide

## Prerequisites

- Hostinger VPS with MySQL 8.0+
- Python 3.12+
- Node.js 18+
- Vercel account (for frontend)
- Domain name with DNS access

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=mysql+pymysql://user:password@localhost/dataflow
JWT_SECRET_KEY=<generate-secure-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_RPM=120
MAX_REQUEST_BODY_BYTES=52428800
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Database Setup

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE dataflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations (tables auto-created on first startup)
python -c "from shared.database import Base, get_engine; Base.metadata.create_all(get_engine())"

# Seed initial data
python -c "
from shared.database import get_engine
from sqlalchemy.orm import Session
from authentication.services import seed_default_roles_and_permissions
engine = get_engine()
db = Session(engine)
seed_default_roles_and_permissions(db)
db.close()
"
```

## Backend Deployment (Hostinger VPS)

```bash
# Clone repository
git clone https://github.com/davidamoah1/Data-Integration-and-Analytics.git
cd Data-Integration-and-Analytics

# Install dependencies
pip install -r requirements.txt

# Start with Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080

# Or use systemd service
sudo systemctl start dataflow
sudo systemctl enable dataflow
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL with Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

## Frontend Deployment (Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        run: ssh user@vps "cd /app && git pull && pip install -r requirements.txt && sudo systemctl restart dataflow"

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        run: cd frontend && npx vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
```

## Rollback Procedure

### Backend

```bash
# Stop service
sudo systemctl stop dataflow

# Revert to previous commit
git log --oneline -5
git checkout <previous-commit-hash>

# Restart
sudo systemctl start dataflow
```

### Frontend

```bash
# Vercel dashboard → Deployments → Promote previous deployment
# Or via CLI:
vercel ls
vercel promote <deployment-url>
```

### Database

```bash
# Restore from backup
mysql -u root -p dataflow < backup_YYYYMMDD.sql
```

## Health Checks

- Backend: `GET /health` → `{"status": "healthy"}`
- Frontend: `GET /` → HTTP 200
- Database: `SELECT 1`
