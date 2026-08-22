# Certificate & Document Intelligence Engine

## Overview

The Certificate Intelligence Engine extends the existing DataFlow Smart Data Capture platform with certificate-specific analysis, normalization, reporting, and verification capabilities. It builds on the existing capture pipeline (upload → OCR → classify → extract → validate → review → approve) without replacing any existing functionality.

## Architecture

```
Upload → Checksum Duplicate Check → Storage → Background OCR Job
    → Classification → Field Extraction → Normalization → Validation
    → Duplicate Detection (field-level) → Ready for Review
    → Human Review/Correction → Approve/Reject
    → Analysis (completeness, consistency, anomalies, recommendations)
    → Report / PowerPoint Generation
    → Verification
    → Export to Dataset
```

## New Modules

### `certificates/analysis.py`
Certificate analysis engine providing:
- **Completeness assessment** — required vs optional fields filled, percentage scoring
- **Consistency checks** — cross-field validation (date_awarded vs graduation_date, expiry vs issue, GPA range, name format, certificate number presence)
- **Academic performance summary** — GPA, grade, qualification, programme extraction
- **Anomaly detection** — low confidence fields, validation failures, consistency errors, duplicates, low classification confidence, missing required fields
- **Recommendations** — actionable, priority-ranked suggestions (review missing fields, verify low confidence, fix validation, initiate verification, approve)
- **Batch analytics** — aggregate metrics across multiple certificates (by type, verification, completeness tier, institution, qualification, anomaly summary)

### `certificates/normalizer.py`
Field normalization module that standardizes extracted values without fabricating data:
- **Name normalization** — title-case for all-upper/all-lower, preserves mixed-case (McDonald, O'Brien)
- **Date normalization** — converts multiple formats to ISO 8601 (YYYY-MM-DD)
- **GPA normalization** — extracts and formats to 2 decimal places
- **Certificate number normalization** — uppercase, strips surrounding punctuation
- **Grade normalization** — maps to canonical forms (First Class, Distinction, etc.)
- **Dispatch table** — `normalize_field(field_name, raw_value)` routes to the correct normalizer

Original OCR values are always preserved in `CaptureField.raw_value`; normalized values are stored in `CaptureField.value`.

## API Endpoints

All endpoints are under `/api/certificates` and require authentication + organization isolation.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload multiple certificate files (up to 50 per batch) |
| GET | `/search` | Search certificates with filters (type, status, verification, institution, year) |
| GET | `/dashboard` | Dashboard analytics (counts, by type, by status, by verification, by institution, by year) |
| GET | `/export/csv` | Export certificate data as CSV |
| GET | `/export/xlsx` | Export certificate data as XLSX |
| GET | `/types` | List all supported certificate types and their field specs |
| POST | `/{document_id}/verify` | Verify a certificate (method, status, reference, notes) |
| GET | `/{document_id}/verifications` | List verification history for a certificate |
| POST | `/to-dataset` | Export approved certificates to a dataset for analytics |
| **GET** | **`/{document_id}/detail`** | **Full certificate detail with intelligence analysis** |
| **GET** | **`/batch/{batch_id}/analytics`** | **Batch-level aggregate analytics** |
| **PATCH** | **`/{document_id}/fields/{field_id}`** | **Correct a field value during human review** |
| **GET** | **`/report`** | **Generate structured JSON report with analytics** |
| **GET** | **`/presentation`** | **Generate PowerPoint presentation with charts** |

**Bold** = new endpoints added by the Certificate Intelligence Engine.

## Database Changes

### Migration: `f1a2b3c4d5e6_add_file_checksum_to_capture_documents`

Adds `file_checksum` column (VARCHAR(64), indexed) to `capture_documents` table for SHA-256 checksum-based duplicate detection.

### Checksum-Based Duplicate Detection

On upload, a SHA-256 hash of the file content is computed. If a document with the same checksum already exists in the same organization (and is not rejected), the upload is detected as a duplicate and the existing document is returned instead of creating a new one. This prevents re-processing the same file.

## Security

- **Authentication**: All endpoints require `get_current_user` dependency
- **Organization isolation**: All queries filter by `organization_id` from `get_current_organization_id`
- **Audit logging**: All actions (upload, correct, verify, report, presentation) are logged via `log_audit_event`
- **Field correction audit trail**: Corrections create `CaptureCorrection` records with old/new values and corrector user ID
- **File access control**: Documents are only accessible within the same organization

## Frontend

The certificates page (`/certificates`) provides:
- Drag-and-drop upload area with progress indication
- Dashboard with stat cards and distribution charts
- Searchable, filterable certificate table with clickable rows
- **Certificate detail modal** with:
  - Completeness and confidence metrics
  - Academic performance summary
  - Consistency check results (pass/fail with severity)
  - Anomaly list with descriptions
  - Priority-ranked recommendations
  - Extracted fields table with inline editing and correction
  - Original vs corrected value display (strikethrough for original)
- Export buttons (CSV, XLSX, PPTX)

## Testing

### `tests/test_certificate_intelligence.py` (58 tests)

- **Normalization tests** (22): name, date, GPA, certificate number, grade, dispatch
- **Completeness tests** (4): all required filled, missing required, no spec, empty fields
- **Consistency check tests** (6): date comparison, expiry before issue, GPA range, name format, certificate number presence
- **Academic performance tests** (3): full data, no data, partial data
- **Anomaly detection tests** (5): low confidence, validation failure, duplicate, low classification, missing required
- **Recommendation tests** (3): missing required, not verified, all good
- **Full analysis tests** (3): well-formed certificate, with duplicate, no type
- **Batch analytics tests** (2): empty batch, multiple certificates
- **Migration test** (1): checksum migration file exists and is correct

### `tests/test_certificates.py` (20 tests, pre-existing)

All pre-existing tests continue to pass — no regressions.

## Running Tests

```bash
# Certificate intelligence tests
python -m pytest tests/test_certificate_intelligence.py -v

# Existing certificate tests (regression check)
python -m pytest tests/test_certificates.py -v

# Both together
python -m pytest tests/test_certificate_intelligence.py tests/test_certificates.py -v
```

## Dependencies

- `python-pptx` — Required for PowerPoint generation (`/presentation` endpoint)
- `pytesseract` — Required for OCR (existing dependency)
- `PyMuPDF` (fitz) — Required for PDF text extraction (existing dependency)

## File Inventory

| File | Description |
|------|-------------|
| `certificates/analysis.py` | Certificate analysis engine (completeness, consistency, anomalies, recommendations, batch analytics) |
| `certificates/normalizer.py` | Field normalization (names, dates, GPA, certificate numbers, grades) |
| `certificates/routes.py` | API routes (existing + new detail, analytics, correction, report, presentation endpoints) |
| `capture/models.py` | Added `file_checksum` column to `CaptureDocument` |
| `capture/service.py` | Added checksum computation, duplicate detection, and field normalization integration |
| `alembic/versions/f1a2b3c4d5e6_add_file_checksum_to_capture_documents.py` | Migration for checksum column |
| `tests/test_certificate_intelligence.py` | 58 tests covering all new functionality |
| `frontend/services/certificates/certificateService.ts` | Added getDetail, getBatchAnalytics, correctField, getReport, downloadPresentation |
| `frontend/app/(app)/certificates/page.tsx` | Added detail modal with analysis, field correction, PPTX download |
