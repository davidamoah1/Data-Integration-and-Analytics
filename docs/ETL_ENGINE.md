# Phase 5 — ETL Engine Documentation

## Overview

Phase 5 transforms DataFlow into an enterprise-grade ETL platform with pluggable data connectors, automated profiling, data quality checks, reusable transformations, pipeline versioning, lineage tracking, and AI-ready hooks.

## Module Structure

```
etl/
├── __init__.py
├── models.py              # SQLAlchemy ORM models (10 tables)
├── schemas.py             # Pydantic API schemas
├── routes.py              # FastAPI REST endpoints (30+ routes)
├── pipeline_builder.py    # Pipeline CRUD, versioning, execution, job monitoring
├── ai_hooks.py            # Abstract interfaces for future AI integration
├── file_security.py       # Upload validation (MIME, size, structure)
├── logging_config.py      # Centralized logger
├── connectors/
│   ├── __init__.py
│   ├── base.py            # BaseConnector abstract class
│   └── connectors.py      # CSV, Excel, JSON, XML, MySQL, REST + registry
├── profiling/
│   └── __init__.py        # DataProfiler — stats, quality score, column analysis
├── quality/
│   └── __init__.py        # DataQualityEngine — checks, scoring, fixes, recommendations
├── transformations/
│   └── __init__.py        # TransformationEngine — 12 transformation types
├── load_engine/
│   └── __init__.py        # LoadEngine — insert/update/upsert/incremental/batch
├── lineage/
│   └── __init__.py        # LineageTracker — source→destination tracking, graph
└── reports/
    └── __init__.py        # ReportGenerator — import, quality, pipeline, execution
```

## Database Tables

| Table | Purpose |
|------|---------|
| `etl_pipelines` | Reusable pipeline definitions |
| `etl_pipeline_versions` | Versioned step configurations |
| `etl_pipeline_steps` | Per-step execution records |
| `etl_jobs` | Job/run tracking with metrics |
| `etl_import_templates` | Saved import configurations |
| `etl_data_profiles` | Profiling results storage |
| `etl_quality_reports` | Quality assessment results |
| `etl_data_lineage` | Source→destination lineage records |
| `etl_schedules` | Pipeline execution schedules |
| `etl_transformations` | Reusable transformation templates |

## API Endpoints

### Import
| Method | Path | Description |
|--------|------|-------------|
| POST | `/etl/import/upload` | Upload & validate a file |
| POST | `/etl/import/preview` | Preview data from a source |
| POST | `/etl/import/execute` | Full import with profiling & quality |

### Profiling
| Method | Path | Description |
|--------|------|-------------|
| POST | `/etl/profile` | Profile a data source |
| GET | `/etl/profiles/{job_id}` | Get saved profile |

### Quality
| Method | Path | Description |
|--------|------|-------------|
| POST | `/etl/quality/check` | Run quality checks |
| POST | `/etl/quality/fix` | Apply fixes for failed checks |
| GET | `/etl/quality/reports/{job_id}` | Get saved quality report |

### Transformations
| Method | Path | Description |
|--------|------|-------------|
| POST | `/etl/transform` | Apply transformations to a source |
| POST | `/etl/transformations/templates` | Create reusable template |
| GET | `/etl/transformations/templates` | List templates |

### Pipelines
| Method | Path | Description |
|--------|------|-------------|
| POST | `/etl/pipelines` | Create pipeline |
| GET | `/etl/pipelines` | List pipelines |
| GET | `/etl/pipelines/{id}` | Get pipeline details |
| PUT | `/etl/pipelines/{id}` | Update (creates new version) |
| GET | `/etl/pipelines/{id}/versions` | Version history |
| POST | `/etl/pipelines/{id}/rollback` | Rollback to version |
| POST | `/etl/pipelines/{id}/execute` | Execute pipeline |

### Jobs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/etl/jobs` | List jobs |
| GET | `/etl/jobs/stats` | Job statistics |
| GET | `/etl/jobs/{id}` | Get job details |
| GET | `/etl/jobs/{id}/steps` | Get step-level details |

### Lineage
| Method | Path | Description |
|--------|------|-------------|
| GET | `/etl/lineage` | Lineage graph (nodes + edges) |
| GET | `/etl/lineage/entries` | Lineage entries list |

### Schedules
| Method | Path | Description |
|--------|------|-------------|
| GET | `/etl/schedules` | List schedules |
| POST | `/etl/schedules` | Create schedule |

### Templates
| Method | Path | Description |
|--------|------|-------------|
| GET | `/etl/templates` | List import templates |

### Dashboard & AI
| Method | Path | Description |
|--------|------|-------------|
| GET | `/etl/dashboard` | ETL dashboard metrics |
| GET | `/etl/ai/hooks` | List available AI hooks |

## Connectors

All connectors implement `BaseConnector` with `connect()`, `extract()`, `get_schema()`, `close()`, and `preview()`.

| Type | Config Keys |
|------|------------|
| `csv` | `file_path`, `delimiter`, `encoding` |
| `excel` | `file_path`, `sheet_name` |
| `json` | `file_path`, `records_path` |
| `xml` | `file_path`, `record_tag`, `root_path`, `encoding` |
| `mysql` | `connection_string` or `host`/`port`/`user`/`password`/`database`/`query` |
| `api` | `url`, `method`, `headers`, `params`, `body`, `records_path` |

Custom connectors can be registered via `register_connector(type, Class)`.

## Transformation Types

`rename`, `drop`, `filter`, `fill`, `convert`, `calculate`, `join`, `split`, `merge`, `sort`, `deduplicate`, `standardize`

## Quality Checks (Built-in)

- **missing_values** — Detects null cells
- **duplicate_rows** — Detects exact duplicates
- **empty_columns** — Detects fully-null columns
- **invalid_emails** — Validates email format
- **invalid_phone_numbers** — Validates phone format
- **negative_numeric_values** — Detects negative values in non-ID columns
- **high_null_percentage** — Warns on columns with >50% nulls

Custom checks can be added via `engine.add_check(QualityCheck(...))`.

## Load Modes

| Mode | Description |
|------|-------------|
| `insert` | Append all rows |
| `update` | Update existing rows by key |
| `upsert` | Insert new, update existing |
| `incremental` | Only insert rows not already present |
| `full` | Replace all data (truncate + insert) |
| `batch` | Batch insert with configurable size |

## AI Hooks Architecture

Abstract interfaces defined for future AI integration:

- `AICleaningHook` — Suggest cleaning operations
- `AIColumnMappingHook` — Auto-map source to target columns
- `AITransformationHook` — Recommend transformations
- `AIAnomalyDetectionHook` — Detect data anomalies
- `AIDataQualityHook` — AI-powered quality assessment

Each hook has `name`, `description`, `is_available()`, and `execute()` methods. Implementations can be registered without modifying core engine code.

## File Security

- MIME type validation (magic bytes)
- File extension whitelist: `csv`, `xlsx`, `xls`, `json`, `xml`
- Max file size: 50 MB
- Basic structure scanning (readable, non-empty)

## Testing

```bash
# Run all ETL tests
python -m pytest tests/test_etl_*.py -v

# Run specific module
python -m pytest tests/test_etl_connectors.py -v

# Run all tests (Phase 4 + Phase 5)
python -m pytest tests/ -v
```

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_etl_connectors.py` | 15 | CSV, JSON, XML connectors, registry |
| `test_etl_profiling.py` | 9 | Stats, null %, duplicates, outliers, quality score |
| `test_etl_quality.py` | 11 | All checks, fixes, custom checks, scoring |
| `test_etl_transformations.py` | 15 | All 12 transformation types, chaining |
| `test_etl_pipeline.py` | 8 | CRUD, versioning, rollback, job monitor |
| `test_etl_lineage_reports.py` | 11 | Lineage tracking, graph, all report types |
| `test_etl_api.py` | 23 | All API endpoints, auth, upload |
| **Total** | **88** | **All passing** |

## Alembic Migration

```bash
# Apply Phase 5 migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migration: `alembic/versions/0002_phase5_etl.py`
