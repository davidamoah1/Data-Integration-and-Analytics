# Docker Deployment

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Guide for deploying DataFlow with Docker.

## Scope

Docker containerization for backend, frontend, and database.

## Audience

DevOps engineers and developers.

---

## 1. Docker Compose

> **⚠️ Note**: Docker configuration should be created if not present. The following is the recommended setup.

### docker-compose.yml

```yaml
version: '3.8'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: dataflow
      POSTGRES_USER: dataflow
      POSTGRES_PASSWORD: dataflow
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql://dataflow:dataflow@db:5432/dataflow
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CORS_ORIGINS: http://localhost:3000
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    command: npm start
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

## 2. Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 3. Dockerfile (Frontend)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 4. Commands

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Related Documents

- [local-development.md](local-development.md) — Local development
- [vercel.md](vercel.md) — Vercel deployment
- [production.md](production.md) — Production deployment
