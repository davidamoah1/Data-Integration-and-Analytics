# Certificate Data Intelligence Module

## Overview

The Certificate Intelligence module transforms unstructured certificate documents (PDF, JPG, JPEG, PNG) into structured, searchable, validated, and analyzable data. It builds on the existing Smart Data Capture platform, adding certificate-specific document types, field extraction, validation, verification, search, export, and analytics.

## Architecture

```
Upload (PDF/JPG/PNG)
   ↓
File Validation (extension, MIME, size)
   ↓
Storage (existing FileService — local/R2/S3/Supabase)
   ↓
Preprocessing (deskew, denoise, contrast, sharpen)
   ↓
OCR (Tesseract + PyMuPDF)
   ↓
Classification (keyword scoring → certificate type)
   ↓
Field Extraction (label-anchored + pattern-based)
   ↓
Normalization (raw_value + normalized value preserved)
   ↓
Validation (dates, GPA range, expiry > issue)
   ↓
Confidence Scoring (field-level + document-level)
   ↓
Quality Assessment
   ↓
Duplicate Detection (certificate_number + name + institution)
   ↓
Human Review (three-panel: original + OCR + fields)
   ↓
Approval / Rejection
   ↓
MySQL Persistence (organization-isolated)
   ↓
Search / Export / Analytics / Dashboard / Report / Presentation
```

## Supported Certificate Types

| Key | Label | Required Fields |
|-----|-------|-----------------|
| `academic_certificate` | Academic Certificate | full_name, qualification, institution |
| `degree_certificate` | Degree Certificate | full_name, degree, institution |
| `diploma` | Diploma | full_name, qualification, institution |
| `professional_certificate` | Professional Certificate | full_name, qualification, institution |
| `training_certificate` | Training Certificate | full_name, course, institution |
| `certificate_of_completion` | Certificate of Completion | full_name, course, institution |
| `certificate_of_attendance` | Certificate of Attendance | full_name, event, institution |
| `membership_certificate` | Membership Certificate | full_name, institution |
| `license_certification` | License/Certification | full_name, license_type, institution |

## Extracted Fields

### Certificate Holder
- `full_name` (required)
- `date_of_birth`
- `student_id`
- `employee_id`
- `member_id`
- `registration_number`

### Qualification
- `qualification` / `degree` / `diploma`
- `programme` / `course` / `major`
- `grade` / `class` / `gpa` / `cgpa`
- `credits`
- `department`

### Dates
- `date_awarded`
- `date_issued`
- `graduation_date`
- `expiry_date`

### Certificate Identifiers
- `certificate_number`
- `license_number`
- `serial_number`
- `registration_number`
- `credential_id`
- `verification_code`

### Issuing Organization
- `institution`
- `country`
- `department`

## Confidence Scoring

Every extracted field has:
- **Field confidence** (0-1): based on OCR word confidence for the extracted value
- **Document confidence**: aggregate of field confidences
- **Classification confidence**: how confident the classifier is about the certificate type
- **OCR confidence**: mean Tesseract confidence across all words

Fields below `CAPTURE_LOW_CONFIDENCE_THRESHOLD` (default 0.75) are flagged as `is_low_confidence` and routed to human review.

## Verification Model

Verification is distinct from extraction:
- **Extraction** means "this is what the certificate appears to say"
- **Verification** means "an authoritative source confirms this certificate"

Verification statuses:
| Status | Meaning |
|--------|---------|
| `not_verified` | Default — no verification attempted |
| `extraction_complete` | OCR + extraction done, no verification |
| `verification_pending` | Verification in progress |
| `verified` | Authoritative source confirmed |
| `verification_failed` | Authoritative source could not confirm |

The system **never** auto-sets a certificate to "verified" — only an explicit verification action by an authorized user can do that.

## Database Model

### `capture_documents` (existing table, extended)
Added columns:
- `verification_status` VARCHAR(30) DEFAULT 'not_verified'
- `verification_method` VARCHAR(100) NULL
- `verified_at` TIMESTAMP NULL
- `verified_by` BIGINT NULL

### `certificate_verifications` (new table)
Records of each verification attempt:
- `id`, `organization_id`, `document_id`
- `method` (qr_scan, institution_api, manual_check)
- `status` (pending, verified, failed, inconclusive)
- `verified_by`, `verification_source`, `reference_number`
- `notes`, `verified_fields` (JSON)
- `created_at`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/certificates/types` | List all certificate types and their fields |
| POST | `/api/certificates/upload` | Upload multiple certificates (max 50 per batch) |
| GET | `/api/certificates/search` | Search certificates with filters |
| GET | `/api/certificates/dashboard` | Certificate dashboard analytics |
| GET | `/api/certificates/export/csv` | Export certificate data as CSV |
| GET | `/api/certificates/export/xlsx` | Export certificate data as XLSX |
| POST | `/api/certificates/{id}/verify` | Record a verification attempt |
| GET | `/api/certificates/{id}/verifications` | List all verification attempts |
| POST | `/api/certificates/to-dataset` | Export approved certificates to analytics dataset |

## Batch Processing

- **Normal batch**: up to 50 files per request (`CERTIFICATE_MAX_BATCH_SIZE`)
- **Large batch**: ZIP upload via existing `/api/capture/batches/upload-zip` with background processing
- **Future enterprise**: architecture supports 1,000+ via the existing job queue system

## RBAC

The certificate module uses the existing platform RBAC:
- All endpoints require authentication (`get_current_user`)
- All data is organization-isolated (`get_current_organization_id`)
- Super admins can access any organization
- Organization users can only access their own organization's certificates

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `CERTIFICATE_MAX_BATCH_SIZE` | 50 | Maximum files per upload batch |
| `CAPTURE_MAX_FILE_SIZE_MB` | 25 | Maximum file size per certificate |
| `CAPTURE_LOW_CONFIDENCE_THRESHOLD` | 0.75 | Confidence threshold for review |
| `CAPTURE_RETENTION_DAYS` | 365 | Document retention period |
| `TESSERACT_CMD` | (system PATH) | Path to Tesseract binary |

## System Dependencies

- **Tesseract OCR**: Required for text extraction. Install from https://github.com/tesseract-ocr/tesseract
- **PyMuPDF (fitz)**: For PDF rasterization. `pip install PyMuPDF`
- **Pillow**: For image preprocessing. `pip install Pillow`
- **openpyxl**: For XLSX export. `pip install openpyxl`

## Files

### Backend
- `certificates/__init__.py` — Module init
- `certificates/routes.py` — Certificate API routes
- `capture/document_types.py` — Certificate document type definitions (9 types)
- `capture/validators.py` — Certificate-specific validation (GPA, dates)
- `capture/models.py` — CertificateVerification model + verification columns
- `alembic/versions/eb32b7fc465a_add_certificate_verification.py` — Migration
- `config.py` — `CERTIFICATE_MAX_BATCH_SIZE` setting
- `api/main.py` — Router registration

### Frontend
- `frontend/services/certificates/certificateService.ts` — API client
- `frontend/app/(app)/certificates/page.tsx` — Certificate Intelligence page
- `frontend/lib/navigation.ts` — Sidebar navigation entry

### Tests
- `tests/test_certificates.py` — 20 unit tests covering types, validation, classification, routes

## Analytics Integration

Approved certificate data can be exported to a dataset via `POST /api/certificates/to-dataset`. This creates a CSV file that can be used with the existing Data-to-Decision workflow:

```
Certificates → to-dataset → Data-to-Decision → Analysis → Dashboard → Report → Presentation
```

This bridges certificate data into the full analytics pipeline without creating a separate visualization system.
