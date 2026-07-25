# AEDIP Data Management & Dataset Library Documentation

## Overview

AEDIP enforces strict separation between **Production**, **Demo**, and **Test** data. Production environments never automatically use demo or test datasets. All data sources are registered in the Enterprise Dataset Library with full metadata.

## Data Tiers

### Production Data
- **Source**: User-uploaded files, connected databases, ETL pipeline outputs
- **Usage**: Dashboards, AI insights, reports, analytics — all production features
- **Registration**: Via Dataset Library API (`POST /datasets/production/upload`, `POST /datasets/production/database`) or automatically on file upload
- **Access**: Always available in production mode
- **Metadata**: Source, description, industry, license, version, tags, schema, quality score

### Demo Data
- **Source**: Curated demo datasets in `demo_datasets/` directory (12 industries, 200 rows each)
- **Usage**: Onboarding, training, demo dashboards — **opt-in only**
- **Access**: Only when `SEED_DEMO_DATA=true` is set in environment
- **Production**: Demo data is **never** auto-loaded in production. Admin can explicitly seed via `POST /platform/demo/seed` (requires admin role)
- **Files**: `demo_datasets/*.csv`, `scripts/generate_demo_datasets.py`

### Test Data
- **Source**: Test fixtures in `tests/` directory, synthetic data generators
- **Usage**: Unit tests, integration tests — **never available in production**
- **Access**: Only when `PYTEST_RUNNING=1` environment variable is set
- **Files**: `tests/conftest.py`, `tests/test_*.py`, `dataset/generate_sector_data.py`

## Dataset Library

### Supported Industries
1. Healthcare
2. Education
3. Government
4. Retail
5. Church
6. NGO
7. Manufacturing
8. Agriculture
9. Insurance
10. Hospitality
11. Telecommunications

### Dataset Metadata
Every dataset in the library contains:
- **Source**: Where the data originated (user_upload, database, generated_demo)
- **Description**: Human-readable description
- **Industry**: Industry classification
- **License**: Data license terms
- **Version**: Dataset version
- **Tags**: Searchable tags
- **Schema**: Column definitions (name, dtype, description, nullable, unique, sample values)
- **Quality Score**: Data quality assessment (0-100)

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/datasets/` | List all datasets (filter by tier, industry, search) |
| GET | `/datasets/{id}` | Get dataset metadata |
| GET | `/datasets/{id}/preview` | Preview first N rows |
| GET | `/datasets/{id}/schema` | Get dataset schema |
| POST | `/datasets/production/upload` | Register uploaded production dataset |
| POST | `/datasets/production/database` | Register connected database |
| DELETE | `/datasets/{id}` | Remove dataset (demo datasets protected) |
| GET | `/datasets/industries/list` | List supported industries |
| GET | `/datasets/tiers/list` | List data tiers |

### Data Source Resolver

The `DataSourceResolver` (`dataset_library/resolver.py`) enforces tier-based access:

- **Production mode** (default): Only PRODUCTION tier datasets accessible
- **Demo mode** (`SEED_DEMO_DATA=true`): PRODUCTION + approved DEMO datasets
- **Test mode** (`PYTEST_RUNNING=1`): All tiers accessible

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAW_DATA_PATH` | (empty) | Path to raw data file for ETL. **No default sample data.** |
| `SEED_DEMO_DATA` | `false` | Set to `true` for pilot/demo deployments only |
| `DEMO_DATASETS_DIR` | `demo_datasets` | Directory containing demo datasets |
| `SUPER_ADMIN_EMAIL` | `admin@dataflow.io` | Super admin email (configurable) |
| `SUPER_ADMIN_PASSWORD` | `change-this-in-production` | Super admin password (configure for production) |
| `AUTH_ADMIN_PASSWORD` | (empty) | Dashboard admin password (env-var only, no hardcoded default) |
| `AUTH_VIEWER_PASSWORD` | (empty) | Dashboard viewer password (env-var only, no hardcoded default) |

## Dashboard Data Policy

Dashboards only use:
1. **Uploaded datasets** — files uploaded via the Streamlit UI
2. **Connected databases** — data loaded via ETL pipelines or database connections
3. **Approved demo datasets** — only when `SEED_DEMO_DATA=true` and dataset is marked `approved_for_demo`

Dashboards **never** use hidden mock data, hardcoded KPIs, or synthetic analytics.

## AI Data Policy

AI features (Copilot, insights, reports) only use:
1. **Uploaded data** — passed via semantic dataset context
2. **Connected database tables** — dynamically discovered via SQLAlchemy inspector
3. **Semantic layer metadata** — entity library, industry knowledge
4. **Knowledge graph** — semantic relationships

AI **never** generates answers from fake, mock, or demo datasets.

## Files Structure

```
dataset_library/
├── __init__.py          # DatasetLibrary, DatasetEntry, DatasetMetadata, ColumnSchema
├── routes.py            # REST API routes for dataset library
└── resolver.py          # DataSourceResolver for tier enforcement

demo_datasets/           # Demo CSV files (12 industries)
├── healthcare_demo.csv
├── education_demo.csv
├── ...
└── telecommunications_demo.csv

dataset/                 # Test/demo sector data
├── generate_sector_data.py  # Synthetic data generator (test tooling)
├── industries/              # Industry CSV files (test fixtures)
└── *.csv                    # Sector data files (test fixtures)

scripts/
└── generate_demo_datasets.py  # Demo dataset generator (demo tooling)
```
