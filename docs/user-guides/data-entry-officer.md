# Data Entry Officer Guide

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Technical Writer

---

## Purpose

Guide for Data Entry Officers (data_entry_officer role).

## Scope

Smart Data Capture, document upload, and data correction.

## Audience

Data entry officers.

---

## 1. Overview

As a Data Entry Officer, you use Smart Data Capture to digitize paper documents quickly and accurately using OCR technology.

## 2. Key Capabilities

- Upload documents (PDF, images)
- Automatic OCR text extraction
- Review extracted data with confidence scores
- Correct low-confidence fields
- Submit verified data as datasets

## 3. Smart Data Capture Workflow

1. Navigate to `/capture`
2. Upload a document (PDF or image)
3. System processes with OCR
4. Review extracted fields:
   - 🟢 Green (80-100%): Likely correct
   - 🟡 Yellow (50-79%): Review recommended
   - 🔴 Red (0-49%): Manual correction required
5. Correct any low-confidence fields
6. Click "Submit" to save as a dataset

## 4. Tips for Best Results

- Ensure document is clear and well-lit
- Use high-resolution images (300 DPI+)
- Avoid skewed or rotated documents
- Check red fields carefully
- Verify dates and numbers

## Related Documents

- [../governance/roles.md](../governance/roles.md) — Role definitions
- [../workflows/user-journeys.md](../workflows/user-journeys.md) — Data Entry Officer journey
- [../studios/smart-data-capture.md](../studios/smart-data-capture.md) — Smart Data Capture
