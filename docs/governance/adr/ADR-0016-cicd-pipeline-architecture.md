# ADR-0016: CI/CD Pipeline Architecture

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-01 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0013 (Multi-Env Config), ADR-0014 (Production DB Hardening) |

## Context

The platform's initial CI/CD was a basic GitHub Actions workflow with lint, test, and Docker build stages. As the platform matured, it needed:

- A structured pipeline with clear stage progression
- Security scanning integrated into the pipeline
- Separate workflows for PRs (fast feedback) and main branch (full pipeline)
- Automated dependency checking and Dependabot configuration
- Build verification for Docker, frontend, and backend
- Automated deployment with health checks

## Decision

Implement a multi-workflow CI/CD architecture:

1. **CI Pipeline** (`ci.yml`): 6-stage pipeline — Lint → Security Scan → Unit Tests → Integration Tests → Build → Deploy
2. **PR Checks** (`pr-checks.yml`): Fast feedback on PRs — Quick Lint → Quick Tests → PR Build Check
3. **Build Verification** (`build-verify.yml`): Deep build checks — Backend imports, Frontend build, Docker build + health check
4. **Dependency Check** (`dependency-check.yml`): Weekly scheduled — pip-audit, npm audit, auto-issue creation
5. **Dependabot** (`dependabot.yml`): Weekly PRs for pip, npm, and GitHub Actions

### Pipeline Design Principles

- **Stage dependencies**: Each stage depends on the previous (except security-scan which runs in parallel)
- **Fast fail**: PR workflow uses `-x --maxfail=5` for quick feedback
- **Conditional deploy**: Deploy only on `main` branch, requires `production` environment approval
- **Caching**: pip, npm, and Docker layer caching via GitHub Actions cache
- **Security first**: Security scan runs in parallel with lint, deploy waits for both build and security

## Alternatives Considered

1. **Single monolithic workflow**: Rejected — too slow for PR feedback
2. **External CI (CircleCI, Jenkins)**: Rejected — GitHub Actions is sufficient and integrated
3. **GitLab CI**: Rejected — project is on GitHub
4. **No PR workflow**: Rejected — PR feedback is critical for developer experience

## Consequences

**Positive:**
- Clear pipeline progression prevents broken code from reaching production
- PR workflow provides fast feedback (< 5 minutes typically)
- Security scanning is automated and continuous
- Dependency management is automated via Dependabot
- Build verification catches integration issues early
- Deployment is gated by health checks

**Negative:**
- Multiple workflow files to maintain
- GitHub Actions minutes consumed (mitigated by caching)
- Deploy requires manual approval (intentional, but adds latency)
- Integration tests require MySQL service container (slower than unit tests)

## Implementation Notes

- All workflows use `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`
- Docker build uses `docker/build-push-action@v6` with GHA cache backend
- Trivy SARIF results uploaded to GitHub Security tab
- Dependabot PRs are labeled and assigned to repository owner
- Deploy uses `amondnet/vercel-action@v25` for Vercel deployment
- Post-deploy health check retries 10 times with 10-second intervals

## Future Considerations

- Staging environment deployment (on `develop` branch)
- Blue-green deployment strategy
- Automated rollback on health check failure
- Parallel test execution for faster CI
- Custom GitHub Actions for reusable steps
