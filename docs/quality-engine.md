# AI Data Quality Engine

## Overview

The Quality Engine produces a multi-dimensional quality score (0-100) with detailed findings, business impact, and recommended fixes.

## Architecture

### Components

| Component | File | Purpose |
|-----------|------|---------|
| `QualityCheckEngine` | `data_quality/checks.py` | Runs individual quality checks |
| `QualityIntelligenceEngine` | `data_quality/quality_engine.py` | Orchestrates checks, drift, schema, scoring |
| `DriftDetector` | `data_quality/drift_detector.py` | Detects data drift between datasets |
| `SchemaMonitor` | `data_quality/schema_monitor.py` | Detects schema changes |

## Quality Checks

### Completeness
- **Missing values** — null detection per column
- **Blank fields** — empty string detection
- **Empty columns** — entirely null columns
- **High null percentage** — columns with >50% nulls

### Uniqueness
- **Duplicate rows** — exact duplicate detection
- **Duplicate IDs** — duplicate values in ID columns

### Validity
- **Sentinel values** — placeholder values (999, -1, "N/A", "UNKNOWN")
- **Out of range** — values outside expected ranges (age 0-120, BMI 10-80, etc.)
- **Invalid formats** — emails, phone numbers, ICD-10 codes
- **Invalid dates** — values that cannot be parsed as dates (added in Phase 12.2)
- **Invalid numeric** — non-numeric values in numeric-like columns (added in Phase 12.2)
- **Negative values** — negative values in columns that shouldn't be negative

### Consistency
- **Type mismatches** — mixed data types within a column
- **Constant columns** — columns with only one unique value
- **Mixed case** — same values in different cases (e.g., "Active" vs "active")

## Quality Score

### Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Completeness | 25% | Based on missing/null values |
| Validity | 20% | Based on invalid/sentinel/out-of-range values |
| Uniqueness | 20% | Based on duplicate records |
| Consistency | 20% | Based on type/case consistency |
| Timeliness | 15% | Based on data drift detection |

### Traffic Light

| Score | Light | Grade |
|-------|-------|-------|
| ≥ 85 | 🟢 Green | A/B |
| 60-84 | 🟡 Yellow | C/D |
| < 60 | 🔴 Red | F |

## Findings

Each finding includes:

```json
{
  "check_name": "missing_values",
  "category": "completeness",
  "severity": "critical",
  "column": "email",
  "affected_rows": 150,
  "affected_pct": 15.0,
  "message": "Column 'email' has 150 missing values (15.0%).",
  "suggested_fix": "Fill or remove missing values in 'email'. Consider imputation.",
  "business_impact": "Missing data leads to incomplete analytics and biased results.",
  "sample_values": []
}
```

## Recommendations

The engine generates actionable recommendations from:
- Critical/error findings
- Drift detection results
- Schema change detection

## Never Modifies Data

The quality engine **never** modifies data automatically. It only reports issues and recommends fixes. User confirmation is always required before any data changes.
