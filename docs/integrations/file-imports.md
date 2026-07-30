# File Imports

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Solution Architect

---

## Purpose

Document supported file formats and the import process.

## Scope

All file types supported for dataset upload.

## Audience

Data engineers and analysts.

---

## 1. Supported Formats

| Format | Extension | Max Size | Status |
|--------|-----------|----------|--------|
| CSV | `.csv` | 50MB | ✅ Active |
| Excel | `.xlsx` | 50MB | ✅ Active |
| JSON | `.json` | 50MB | ⚠️ Planned |
| Parquet | `.parquet` | 50MB | ⚠️ Planned |

## 2. Import Process

1. User selects file via upload component (React Dropzone)
2. Client-side validation (file type, size)
3. POST to `/api/datasets` with file
4. Server-side validation and parsing
5. Data stored in database (org-scoped)
6. Audit log created

## 3. CSV Parsing

- Header row required
- Automatic type inference (int, float, string, date)
- Handles quoted fields and commas
- Encoding: UTF-8

## 4. Excel Parsing

- First sheet used by default
- Header row required
- Cell types preserved
- Multiple sheets: future enhancement

## Related Documents

- [database-connectors.md](database-connectors.md) — Database connectors
- [../workflows/dataset-upload.md](../workflows/dataset-upload.md) — Upload workflow
- [cloud-storage.md](cloud-storage.md) — Cloud storage (planned)
