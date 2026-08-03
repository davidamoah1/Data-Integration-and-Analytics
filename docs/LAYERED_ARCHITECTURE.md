# Backend Layered Architecture

## Architecture Overview

```
API Routes (Controller)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database (SQLAlchemy ORM Models)
```

## Layer Responsibilities

### 1. API Layer (`routes.py`, `shared/controllers.py`)
- HTTP request/response handling
- Request parsing and validation
- Dependency injection (auth, db session)
- Exception → HTTP status translation
- Response serialization
- **No business logic, no database queries**

### 2. Service Layer (`service.py`, `shared/services.py`)
- Business rules and orchestration
- Cross-cutting concerns (logging, audit)
- Validation beyond schema (e.g., "can this document be approved?")
- Coordinates multiple repositories
- Raises domain exceptions
- **No direct SQLAlchemy queries**

### 3. Repository Layer (`repositories.py`, `shared/repositories.py`)
- All database CRUD operations
- Query construction and optimization
- Filtering, pagination, sorting
- Bulk operations
- **No business logic, no HTTP awareness**

### 4. Database Layer (`models.py`, `shared/database.py`)
- ORM model definitions
- Table schema
- Engine/session management
- Migrations

## Base Classes

### BaseRepository (`shared/repositories.py`)
Generic CRUD repository providing:
- `get_by_id`, `get_by_field`, `list`, `count`, `list_paginated`, `exists`
- `create`, `create_from_model`, `bulk_create`
- `update`, `update_instance`, `bulk_update`
- `delete`, `delete_hard`
- `commit`, `refresh`

### BaseService (`shared/services.py`)
Business logic base providing:
- Repository injection via `repository_class`
- `_get_or_404` — fetch or raise NotFoundError
- `_validate_required` — validate required fields
- Standard CRUD passthrough (overridable)
- `commit` — transaction control

### BaseController (`shared/controllers.py`)
Thin API controller providing:
- Service injection via `service_class`
- `org_id` / `user_id` properties (tenant-scoped)
- `ok`, `created`, `deleted` response helpers
- `handle_error` — exception → HTTP translation
- `get_controller()` — FastAPI dependency factory

## Reference Implementation: Capture Module

```
capture/
├── routes.py              # API layer — thin endpoints
├── service.py             # Service layer — pipeline orchestration
├── repositories.py        # Repository layer — all DB access
├── models.py              # ORM models
├── document_types.py      # Domain config (document type specs)
├── ocr_engine.py          # External service (OCR)
├── classifier.py          # Business logic (classification)
├── extractors.py          # Business logic (field extraction)
├── validators.py          # Business logic (validation)
├── preprocessing.py       # Utility (image processing)
└── template_service.py    # Business logic (template learning)
```

### Flow Example: Approve Document

```python
# routes.py (API layer) — thin, no logic
@router.post("/documents/{document_id}/approve")
async def approve_document(document_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    org_id = get_current_organization_id(current_user, db)
    svc = CaptureService(db)
    doc = svc.approve_document(document_id, org_id, current_user["id"])
    return _serialize_document(doc)

# service.py (Service layer) — business rules
def approve_document(self, document_id, organization_id, user_id):
    doc = self.get_document(document_id, organization_id)  # uses doc_repo
    if not doc:
        raise CaptureError("Document not found.")
    if doc.status not in ("ready_for_review", "draft"):
        raise CaptureError(f"Cannot approve from status '{doc.status}'.")
    doc.status = "approved"
    doc.approved_by = user_id
    # ... audit logging via audit_repo
    self.db.commit()
    return doc

# repositories.py (Repository layer) — data access only
class CaptureDocumentRepository(BaseRepository[CaptureDocument]):
    model = CaptureDocument

    def get_by_org(self, document_id, organization_id):
        return self.db.execute(
            select(CaptureDocument).where(
                CaptureDocument.id == document_id,
                CaptureDocument.organization_id == organization_id,
            )
        ).scalar_one_or_none()
```

## Migration Guide for Other Modules

To refactor an existing module to the layered pattern:

1. **Create `repositories.py`** — Extract all `db.query()` calls from the service into repository methods. Inherit from `BaseRepository` with `model = YourModel`.

2. **Update `service.py`** — Replace `self.db.query()` calls with `self.repo.method()` calls. Initialize repositories in `__init__`.

3. **Update `routes.py`** — Remove any direct `db.query()` calls. All data access goes through the service.

4. **Test** — Verify all endpoints still work. The service's public API shouldn't change.

### Existing Repository Patterns
- `authentication/repositories.py` — Already follows this pattern (UserRepository, RoleRepository, etc.)
- `database/repositories.py` — Sales data repository (engine-based, not session-based)
- `capture/repositories.py` — New, follows BaseRepository pattern

## Key Principles

1. **Services never import `select` or `query`** — They call repository methods
2. **Repositories never raise HTTP exceptions** — They return `None` or empty lists
3. **Routes never contain business logic** — They parse, delegate, and serialize
4. **One repository per aggregate root** — Document, Field, Batch, AuditLog each have their own
5. **Repositories are stateless** — They receive the session via constructor, no caching
