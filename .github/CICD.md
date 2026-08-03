# CI/CD Pipeline Documentation

## Overview

The AEDIP project uses GitHub Actions for continuous integration and deployment.
The pipeline follows a strict stage-based flow ensuring code quality, security,
and reliability before any code reaches production.

## Pipeline Architecture

```
Push Code
    │
    ├──► Lint (Python: Ruff + Black | Frontend: ESLint + TypeScript)
    │
    ├──► Security Scan (pip-audit, Bandit, npm audit, Trivy)
    │
    ├──► Unit Tests (Python: pytest + coverage | Frontend: vitest)
    │         ▲ depends on Lint
    │
    ├──► Integration Tests (MySQL + Redis services, Alembic migrations)
    │         ▲ depends on Unit Tests
    │
    ├──► Build (Backend import check, Alembic verify, Frontend build, Docker build)
    │         ▲ depends on Integration Tests
    │
    └──► Deploy (Vercel production + health check)
              ▲ depends on Build + Security Scan
              ▲ only on main branch
```

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers**: Push to `main` or `develop`, manual dispatch

**Stages**:
- **Lint**: Ruff + Black (Python), ESLint + tsc (Frontend)
- **Security Scan**: pip-audit, Bandit, npm audit, Trivy filesystem scan with SARIF upload
- **Unit Tests**: pytest with coverage report, vitest for frontend
- **Integration Tests**: MySQL 8.0 + Redis 7 service containers, Alembic migrations, full test suite
- **Build**: Backend import verification, Alembic migration check, frontend Next.js build, Docker image build with GHA cache
- **Deploy**: Vercel production deployment (main branch only) with post-deploy health check

### 2. PR Checks (`.github/workflows/pr-checks.yml`)

**Triggers**: Pull request to `main` or `develop`

**Stages**:
- **Quick Lint**: Ruff on changed Python files only, TypeScript type check
- **Quick Tests**: pytest with fast-fail (`-x --maxfail=5`), vitest
- **PR Build Check**: Backend import verification, frontend build
- **PR Summary**: Aggregated results in GitHub Step Summary

### 3. Build Verification (`.github/workflows/build-verify.yml`)

**Triggers**: Push affecting `Dockerfile`, `docker-compose*.yml`, `frontend/**`, `api/**`, `requirements.txt`, `pyproject.toml`

**Stages**:
- **Backend Build**: All module imports, Alembic migration verification, database CLI verification
- **Frontend Build**: Next.js production build, output verification, compilation error check
- **Docker Build**: Docker image build with Buildx, container health check on port 8001, docker-compose config validation
- **Build Summary**: Aggregated pass/fail report

### 4. Dependency Check (`.github/workflows/dependency-check.yml`)

**Triggers**: Weekly schedule (Monday 9:00 UTC), manual dispatch

**Stages**:
- **Python Dependency Audit**: pip-audit on requirements.txt and pyproject.toml, outdated package check, auto-creates GitHub issue on vulnerabilities
- **Frontend Dependency Audit**: npm audit, outdated package check, auto-creates GitHub issue on vulnerabilities

### 5. Dependabot (`.github/dependabot.yml`)

**Ecosystems**: pip, npm (frontend), GitHub Actions

**Schedule**: Weekly on Monday at 09:00 UTC

**Configuration**:
- 5 open PRs limit per ecosystem
- Auto-labeled with `dependencies` + ecosystem tag
- Commit prefix: `deps(python)`, `deps(frontend)`, `deps(ci)`

## Required Secrets

Configure these in GitHub repository settings → Secrets and variables → Actions:

| Secret | Description | Required for |
|--------|-------------|--------------|
| `VERCEL_TOKEN` | Vercel deployment token | Deploy stage |
| `VERCEL_ORG_ID` | Vercel organization ID | Deploy stage |
| `VERCEL_PROJECT_ID` | Vercel project ID | Deploy stage |

## Required GitHub Settings

### Branch Protection (main)
- Require status checks to pass before merging
- Required checks: `Lint`, `Unit Tests`, `PR Build Check`
- Require branches to be up to date before merging
- Require pull request reviews (at least 1)
- Dismiss stale reviews when new commits are pushed

### Environments
- Create `production` environment for deploy stage
- Add required reviewers for production deployments
- Set deployment branch to `main`

## Local Testing

Run the same checks locally before pushing:

```bash
# Python lint
ruff check .
black --check .

# Python tests
pytest tests/ --tb=short -v

# Frontend lint
cd frontend && npx next lint

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend tests
cd frontend && npx vitest run

# Frontend build
cd frontend && npm run build

# Docker build
docker build -t aedip-local .

# Docker health check
docker run -d --name aedip-test -p 8000:8000 \
  -e DB_TYPE=sqlite -e SQLITE_DB_PATH=/tmp/test.db \
  -e JWT_SECRET_KEY=local-test-secret-key-32chars-min \
  -e DISABLE_CONFIG_VALIDATION=1 \
  aedip-local
sleep 10
curl -f http://localhost:8000/health
docker stop aedip-test
```

## Caching

The pipeline uses GitHub Actions caching for:
- **pip**: Python packages cached by `requirements.txt` hash
- **npm**: Node modules cached by `package-lock.json` hash
- **Docker**: Buildx cache via `type=gha` (GitHub Actions cache backend)

## Security Scanning

| Tool | Scope | Severity |
|------|-------|----------|
| pip-audit | Python dependencies | All vulnerabilities |
| Bandit | Python source code | Medium+ (SAST) |
| npm audit | Frontend dependencies | High+ |
| Trivy | Full filesystem | HIGH, CRITICAL |

Trivy SARIF results are uploaded to GitHub Security tab for tracking.
