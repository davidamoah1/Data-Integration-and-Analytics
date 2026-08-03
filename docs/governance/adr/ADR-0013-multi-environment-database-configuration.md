# ADR-0013: Multi-Environment Database Configuration

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-08-01 |
| **Decision Maker** | Enterprise Architecture Board |
| **Related ADRs** | ADR-0001 (Multi-tenant), ADR-0014 (Production DB), ADR-0015 (Slow Query Logging) |

## Context

The platform initially used a single database configuration for all environments. As the platform matured, the need for environment-specific configurations became critical:

- Development uses SQLite for simplicity and zero-config startup
- Testing requires isolated, in-memory or ephemeral databases
- Production requires MySQL with connection pooling, encryption, and strict validation

A single configuration approach led to development settings leaking into production and production requirements blocking development.

## Decision

Implement environment-aware configuration using the `APP_ENV` environment variable with three distinct modes:

1. **development** (default): SQLite, small pool, debug logging, demo data optional
2. **testing**: SQLite in-memory, minimal pool, config validation bypassed
3. **production**: MySQL required, large pool, strict validation, encryption mandatory

Each environment has:
- Dedicated `.env.example` file (`.env.dev.example`, `.env.test.example`, `.env.prod.example`)
- Specific connection pool sizing
- Environment-specific validation rules
- Different security requirements

## Alternatives Considered

1. **Single config with feature flags**: Rejected — too easy to misconfigure production
2. **Separate config files per environment**: Rejected — Python imports make this fragile
3. **External config service**: Rejected — over-engineered for current scale

## Consequences

**Positive:**
- Clear separation of concerns between environments
- Production validation prevents misconfiguration
- Developers can run locally with zero config
- Test environment is fully isolated

**Negative:**
- Three example files to maintain
- Configuration logic is more complex
- New developers must understand which env file to copy

## Implementation Notes

- `APP_ENV` is read in `config.py` and sets `IS_PRODUCTION` and `IS_TESTING` flags
- `validate_config()` enforces production requirements (MySQL, encryption key, absolute backup path)
- `DISABLE_CONFIG_VALIDATION` env var bypasses validation for CI/CD pipelines
- Connection pool tuning is applied in `shared/database.py` based on `IS_PRODUCTION`

## Future Considerations

- Staging environment configuration (between testing and production)
- Dynamic configuration reloading without restart
- Configuration schema validation using Pydantic
