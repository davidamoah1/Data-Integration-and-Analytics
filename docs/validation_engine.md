# Hospital Data Validation & Quality Management Engine

## Overview

The Hospital Data Validation & Quality Management Engine is a mandatory pre-ETL validation pipeline for all hospital datasets uploaded to the AEDIP platform. It ensures data quality, clinical consistency, and regulatory compliance before any data is processed by the ETL pipeline.

## Architecture

```
Upload → Schema Validation → Data Profiling → Quality Rules
→ Business Rules → Clinical Consistency → Outlier Detection
→ Quality Scoring → Report Generation → User Review
→ Approval Workflow → ETL (gated)
```

## Components

### Core Engine (`validation/engine.py`)
- `ValidationEngine` — orchestrates the full validation pipeline
- `ValidationResult` — complete result with findings, scores, and status
- `ValidationStatus` — enum: `pending`, `passed`, `passed_with_warnings`, `failed`, `approved`, `rejected`

### Schema Validator (`validation/schema_validator.py`)
- Validates required columns, unexpected columns, column naming conventions
- Detects duplicate columns, whitespace in names, mixed data types
- Checks date and numeric format consistency
- Supports hospital-specific schemas: patient registry, admission records, labs, medications

### Quality Rules Engine (`validation/quality_rules.py`)
- Missing values detection (severity scales with percentage)
- Blank fields, empty columns, high null percentage
- Duplicate rows and duplicate IDs
- Invalid email, phone, gender, and ICD-10 diagnosis codes
- Negative values detection
- Constant columns detection

### Business Rules Engine (`validation/business_rules.py`)
- Unique patient ID enforcement
- DOB not in future
- Admission before discharge date sequence
- Realistic age range (0-150)
- No negative weight/height/lab values
- Male not pregnant (clinical impossibility)
- Visit requires patient (referential integrity)
- Diagnosis requires clinician
- Medication requires prescriber
- Lab result requires test order
- Child age pediatric classification

### Clinical Validation Engine (`validation/clinical_checks.py`)
- Blood pressure range validation (systolic 50-300, diastolic 20-200)
- Systolic > diastolic enforcement
- Temperature range (auto-detects Celsius/Fahrenheit)
- Pulse range (20-250 bpm)
- BMI range and consistency with weight/height
- Extreme age detection
- Impossible lab values (glucose, hemoglobin)
- Abnormal billing (negative, statistical outliers)

### Outlier Detector (`validation/outlier_detector.py`)
- IQR-based statistical outliers (3x IQR)
- Duplicate admissions (same patient, same date)
- Impossible dates (future, pre-1900)
- Duplicate insurance claims

### Data Profiler (`validation/profiler.py`)
- Per-column statistics: dtype, null count/percentage, unique count, uniqueness
- Numeric stats: min, max, mean, median, std
- Top values distribution
- Overall completeness, uniqueness, duplicate percentage

### Quality Score Engine (`validation/scoring.py`)
- Multi-dimensional scoring:
  - **Completeness** (25% weight) — missing data assessment
  - **Accuracy** (20%) — clinical/business rule errors
  - **Consistency** (15%) — data consistency checks
  - **Validity** (15%) — format and code validity
  - **Uniqueness** (15%) — duplicate detection
  - **Integrity** (10%) — referential integrity
- Traffic light indicators:
  - **Green** (≥85): Good quality, proceed
  - **Yellow** (60-84): Acceptable with warnings
  - **Red** (<60): Poor quality, blocked

### Report Generator (`validation/report_generator.py`)
- Structured summary with scores, findings by severity/category
- Export to CSV, Excel (multi-sheet), and PDF
- Includes recommendations and suggested fixes

### Approval Workflow (`validation/approval.py`)
- Role-based approval: reviewer, supervisor, data_manager, statistician, administrator
- Approve (allows ETL despite failures) or Reject (blocks ETL)
- Comments and timestamps tracked

### Audit Logger (`validation/audit.py`)
- Tracks: upload, validation, approval, rejection, correction, ETL start/finish
- Captures user, organization, session ID, timestamp, details

### AI Copilot Integration (`validation/ai_copilot.py`)
- Answers natural language questions about validation results
- Suggests corrections and explains failures
- Builds AI context from validation findings

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/validation/run` | Run validation on uploaded file |
| GET | `/validation/status/{id}` | Get validation status |
| GET | `/validation/report/{id}` | Get full validation report |
| GET | `/validation/report/{id}/export?format=csv\|excel\|pdf` | Export report |
| POST | `/validation/approve/{id}` | Approve validation session |
| POST | `/validation/reject/{id}` | Reject validation session |
| GET | `/validation/rules` | List all validation rules |
| POST | `/validation/rules/toggle` | Enable/disable a rule |
| GET | `/validation/history` | Get validation history |
| GET | `/validation/audit` | Get audit log entries |

## Streamlit Dashboard

The validation dashboard (`dashboard/validation_dashboard.py`) provides:
- Status banner with traffic light indicator
- KPI cards (overall score, errors, warnings, info)
- Quality score by dimension (bar chart)
- Findings by severity and category (charts)
- Detailed findings table with severity filtering
- Data profile table with column statistics
- Schema validation issues
- Recommendations with suggested fixes
- Export buttons (CSV, Excel, PDF)
- Approval workflow section for failed validations

## Integration Points

1. **Streamlit Upload Flow** (`dashboard/app.py`): Validation runs automatically on file upload, before semantic analysis. ETL is blocked until validation passes or is approved.
2. **FastAPI Application** (`api/main.py`): Validation router registered with all endpoints.
3. **Database Models** (`validation/models.py`): SQLAlchemy ORM models for persistence.
4. **AI Copilot**: Context builder and question answering for validation queries.

## Testing

72 tests covering:
- Schema validation (6 tests)
- Quality rules (8 tests)
- Business rules (8 tests)
- Clinical checks (5 tests)
- Outlier detection (3 tests)
- Profiler (3 tests)
- Scoring (4 tests)
- Engine integration (6 tests)
- Approval workflow (5 tests)
- Report generator (5 tests)
- Audit logger (5 tests)
- AI copilot (6 tests)
- Performance (1 test)
- API routes (7 tests)

```bash
# Run validation tests
$env:DB_TYPE="sqlite"; python -m pytest tests/test_validation.py -v
```

## File Structure

```
validation/
├── __init__.py              # Package exports
├── models.py                # SQLAlchemy ORM models
├── schema_validator.py      # Schema validation
├── quality_rules.py         # Data quality rules
├── business_rules.py        # Business rule engine
├── clinical_checks.py       # Clinical validation
├── outlier_detector.py      # Outlier detection
├── profiler.py              # Data profiling
├── scoring.py               # Quality score engine
├── engine.py                # Main validation engine
├── report_generator.py      # Report generation (CSV/Excel/PDF)
├── approval.py              # Approval workflow
├── audit.py                 # Audit logger
├── ai_copilot.py            # AI copilot integration
└── routes.py                # FastAPI REST API routes

dashboard/
└── validation_dashboard.py  # Streamlit dashboard

tests/
└── test_validation.py       # Comprehensive test suite
```
