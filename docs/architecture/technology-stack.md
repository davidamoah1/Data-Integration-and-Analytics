# Technology Stack

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architect

---

## Purpose

Complete technology stack with versions and rationale.

## Scope

All technologies used in the platform.

## Audience

Developers, architects, and new team members.

---

## 1. Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Primary language |
| FastAPI | Latest | Web framework / API server |
| SQLAlchemy | 2.0+ | ORM and database abstraction |
| Pydantic | 2.0+ | Data validation and schemas |
| PyJWT | Latest | JWT token creation and verification |
| bcrypt | Latest | Password hashing |
| APScheduler | Latest | Background job scheduling |
| Uvicorn | Latest | ASGI server |
| Psycopg2 | Latest | PostgreSQL adapter |

## 2. Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | >=20.0.0 | JavaScript runtime |
| Next.js | 14.2.5 | React framework (App Router) |
| React | 18.3.1 | UI library |
| TypeScript | 5.5.4 | Type-safe JavaScript |
| Tailwind CSS | 3.4.7 | Utility-first CSS framework |
| Zustand | 4.5.4 | State management |
| Lucide React | 0.417.0 | Icon library |
| React Dropzone | 14.2.3 | File upload component |
| Sonner | 1.5.0 | Toast notifications |
| Workbox | 7.4.1 | PWA service worker |
| next-pwa | 10.2.9 | PWA plugin for Next.js |
| Vitest | 1.6.0 | Unit testing framework |
| ESLint | 8.57.0 | Code linting |

## 3. Database

| Technology | Purpose |
|------------|---------|
| PostgreSQL | Primary relational database |

## 4. Infrastructure

| Technology | Purpose |
|------------|---------|
| Vercel | Frontend hosting + serverless API |
| Git | Version control |
| GitHub | Repository hosting |

## 5. Development Tools

| Tool | Purpose |
|------|---------|
| pip | Python package management |
| npm | Node.js package management |
| ruff | Python linter/formatter |
| ESLint | JavaScript/TypeScript linter |

## 6. Middleware Stack

| Middleware | Purpose |
|------------|---------|
| CORS Middleware | Cross-origin request support |
| GZip Middleware | Response compression |
| Security Headers Middleware | CSP, HSTS, X-Frame-Options |
| Rate Limit Middleware | Per-IP rate limiting (120 RPM) |
| Request Logging Middleware | Structured request logging |
| Tenant Isolation Middleware | Cross-tenant access logging |
| Request Context Middleware | Request ID and correlation ID |
| Request Size Limit Middleware | Max request body size (50MB) |

## Related Documents

- [system-design.md](system-design.md) — System design
- [overview.md](overview.md) — Architecture overview
- [../deployment/](../deployment/) — Deployment documentation
