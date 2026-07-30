# Troubleshooting

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Common issues and their solutions.

## Scope

Frequently encountered problems and resolution steps.

## Audience

All developers and operations team.

---

## 1. Common Issues

### Database Connection Failed

**Symptom**: `Database engine creation failed` in logs

**Solutions**:
1. Verify `DATABASE_URL` is correct
2. Check PostgreSQL is running
3. Verify network connectivity
4. Check connection pool limits

### Tables Not Created

**Symptom**: API returns 500, tables missing

**Solutions**:
1. Check if running in serverless mode (`VERCEL=1`)
2. Run `Base.metadata.create_all(engine)` manually
3. Check database permissions

### JWT Authentication Failed

**Symptom**: 401 Unauthorized on all requests

**Solutions**:
1. Verify `JWT_SECRET_KEY` is set and consistent
2. Check token has not expired
3. Verify token is in `Authorization: Bearer <token>` header
4. Check user is active (`is_active = 1`)

### CORS Errors

**Symptom**: Browser shows CORS error

**Solutions**:
1. Add frontend URL to `CORS_ORIGINS`
2. If `CORS_ORIGINS` not set, only localhost allowed
3. Verify `allow_credentials=True` in CORS middleware

### Rate Limiting

**Symptom**: 429 Too Many Requests

**Solutions**:
1. Increase `RATE_LIMIT_RPM` environment variable
2. Check if `PYTEST_RUNNING` is set (disables rate limiting)
3. Identify if a single client is making too many requests

### Permission Denied (403)

**Symptom**: 403 Forbidden on API call

**Solutions**:
1. Verify user has the required permission
2. Check if user is super_admin (bypasses all checks)
3. Verify `require_organization_access` is not blocking cross-org access
4. Check if user's org matches the resource's org

### Invitation Not Working

**Symptom**: Invitation acceptance fails

**Solutions**:
1. Check invitation status is `pending`
2. Check invitation has not expired (7-day limit)
3. Verify email matches the invitation email
4. Check if user with that email already exists

## 2. Debug Mode

Enable debug mode for detailed error messages:

```bash
export DEBUG=1
```

This returns actual exception messages in 500 responses instead of generic "Internal server error".

## 3. Log Analysis

Check logs for:
- `ERROR` level messages in application logs
- `RequestLoggingMiddleware` output for request patterns
- `AuditLog` table for user action history
- `SecurityLog` table for security events

## Related Documents

- [../backend/error-handling.md](../backend/error-handling.md) — Error handling
- [../backend/logging.md](../backend/logging.md) — Logging
- [monitoring.md](monitoring.md) — Monitoring
- [incident-response.md](incident-response.md) — Incident response
