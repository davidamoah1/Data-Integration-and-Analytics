# Release Process

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Step-by-step release process for deploying new versions.

## Scope

From code freeze to post-deployment verification.

## Audience

DevOps engineers and developers.

---

## 1. Pre-Release Checklist

### Code

- [ ] All features for the release are merged to `main`
- [ ] All tests pass (backend + frontend)
- [ ] Linting passes (ruff for Python, ESLint for TypeScript)
- [ ] Type checking passes (`tsc --noEmit`)
- [ ] No `console.log` or debug code in production paths
- [ ] `DEBUG` environment variable is not set in production

### Documentation

- [ ] [CHANGELOG.md](CHANGELOG.md) updated with new version
- [ ] [version-history.md](version-history.md) updated
- [ ] All new features documented in relevant `/docs` sections
- [ ] [CROSS_REFERENCE_MAP.md](../CROSS_REFERENCE_MAP.md) updated
- [ ] [CONTRIBUTOR_CHECKLIST.md](../CONTRIBUTOR_CHECKLIST.md) reviewed

### Database

- [ ] No breaking schema changes (or migration plan documented)
- [ ] Seed data updated if new roles/permissions added
- [ ] Backup taken before deployment

### Security

- [ ] No secrets in code
- [ ] No hardcoded credentials
- [ ] Security review completed for new features
- [ ] New endpoints have permission checks

## 2. Release Steps

1. **Update version number**
   - `package.json` (root)
   - `frontend/package.json`
   - `docs/README.md` version header
   - `docs/release-notes/CHANGELOG.md`

2. **Create release commit**
   ```bash
   git add -A
   git commit -m "release: v1.x.0"
   ```

3. **Tag the release**
   ```bash
   git tag v1.x.0
   git push origin main --tags
   ```

4. **Deploy**
   - Vercel auto-deploys on push to `main`
   - Monitor deployment in Vercel dashboard

5. **Post-deployment verification**
   - [ ] Health check passes (`GET /api/health`)
   - [ ] Login works
   - [ ] Key user flows tested
   - [ ] No errors in logs

6. **Notify stakeholders**
   - Update status page
   - Notify users of new features
   - Send release notes

## 3. Hotfix Process

1. Create hotfix branch from `main`
2. Fix the issue
3. Test the fix
4. Merge to `main` with PATCH version increment
5. Deploy immediately
6. Update CHANGELOG with hotfix entry

## 4. Rollback Process

### Vercel

1. Go to Vercel dashboard
2. Select the project
3. Go to Deployments
4. Click "Instant Rollback" on previous deployment
5. Verify health check

### Database

If database changes were made:
1. Restore from pre-deployment backup
2. Update `DATABASE_URL` if needed
3. Restart application

## Related Documents

- [CHANGELOG.md](CHANGELOG.md) — Changelog
- [version-history.md](version-history.md) — Version history
- [../deployment/production.md](../deployment/production.md) — Production deployment
- [../deployment/ci-cd.md](../deployment/ci-cd.md) — CI/CD pipeline
