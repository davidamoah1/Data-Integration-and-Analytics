# CI/CD

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Document the CI/CD pipeline configuration.

## Scope

Continuous integration and deployment setup.

## Audience

DevOps engineers and developers.

---

## 1. Current CI/CD

- **Platform**: GitHub + Vercel
- **Trigger**: Push to `main` branch
- **Frontend**: Vercel auto-deploys on push to `main`
- **Backend**: Deployed as Vercel serverless functions
- **Database**: External PostgreSQL (not auto-migrated)

## 2. Pipeline Stages

```mermaid
flowchart LR
    Push[Push to main] --> Build[Build frontend]
    Build --> Deploy[Deploy to Vercel]
    Deploy --> Health[Health check]
    Health --> Live[Live]
```

## 3. Planned CI/CD Improvements

> **⚠️ Planned**: The following are not yet implemented.

### GitHub Actions Workflow

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm install
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run type-check
      - run: cd frontend && npm run test:run
```

### Planned Stages

1. **Lint**: Python (ruff) + TypeScript (ESLint)
2. **Type check**: TypeScript compiler
3. **Unit tests**: Python (pytest) + Frontend (Vitest)
4. **Build**: Next.js production build
5. **Deploy**: Vercel auto-deploy
6. **Health check**: Verify deployment
7. **Documentation check**: Verify docs are updated (future)

## 4. Branch Strategy

| Branch | Purpose | Deploy Target |
|--------|---------|---------------|
| `main` | Production | Production Vercel |
| `develop` | Development | Staging Vercel (future) |
| Feature branches | Development | Not deployed |

## Related Documents

- [vercel.md](vercel.md) — Vercel deployment
- [production.md](production.md) — Production deployment
- [../testing/strategy.md](../testing/strategy.md) — Testing strategy
