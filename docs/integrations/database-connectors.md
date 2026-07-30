# Database Connectors

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Solution Architect

---

## Purpose

Document database connector types and configuration.

## Scope

All supported database connectors for data import.

## Audience

Data engineers and solution architects.

---

## 1. Supported Connectors

| Connector | Status | Description |
|-----------|--------|-------------|
| PostgreSQL | ✅ Active | Direct connection via SQLAlchemy |
| CSV File | ✅ Active | File upload and parsing |
| Excel File | ✅ Active | `.xlsx` file upload and parsing |
| MySQL | ⚠️ Planned | Future connector |
| SQL Server | ⚠️ Planned | Future connector |
| MongoDB | ⚠️ Planned | Future connector |

## 2. Connector Configuration

Connectors are managed via the Connectors module:

| Endpoint | Permission | Description |
|----------|------------|-------------|
| `GET /api/connectors` | Authenticated | List connectors |
| `POST /api/connectors` | Authenticated | Create connector |
| `GET /api/connectors/{id}` | Authenticated | Get connector |
| `PUT /api/connectors/{id}` | Authenticated | Update connector |
| `DELETE /api/connectors/{id}` | Authenticated | Delete connector |

## 3. Key Files

| File | Purpose |
|------|---------|
| `connectors/models.py` | Connector data models |
| `connectors/routes.py` | Connector API routes |
| `connectors/services.py` | Connector services |

## Related Documents

- [file-imports.md](file-imports.md) — File import formats
- [../architecture/integrations.md](../architecture/integrations.md) — Architecture integrations
- [future-integrations.md](future-integrations.md) — Planned integrations
