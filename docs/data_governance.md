# Data Governance Guide — DataFlow Enterprise Platform

**Version:** 1.0  
**Last updated:** 2026-07-27

---

## 1. Governance Objectives

- Ensure datasets are owned, classified, and approved before publishing.
- Detect sensitive data before it reaches dashboards or exports.
- Provide a clear lifecycle from upload to archive.
- Maintain an audit trail for all governance actions.

---

## 2. Dataset Lifecycle

```
Uploaded
   ↓
Validated
   ↓
Approved
   ↓
Published
   ↓
Archived
```

Allowed transitions are enforced by `governance.classification.can_transition()`:

- `uploaded` → `validated`, `archived`
- `validated` → `approved`, `archived`
- `approved` → `published`, `archived`
- `published` → `approved`, `archived`
- `archived` → `uploaded`

---

## 3. Data Classification Levels

| Level | Description | Example |
| :--- | :--- | :--- |
| `public` | Safe to share externally | Aggregate KPIs |
| `internal` | Organization-only | Sales by region |
| `confidential` | Restricted within the organization | Customer emails, revenue |
| `sensitive` | Highly restricted; may have legal/regulatory impact | SSN, health records, financial account numbers |

Classification is derived automatically by scanning column names and sampled values for:

- Names
- Emails
- Phone numbers
- Addresses
- Government IDs
- Financial data
- Health data
- Location/GPS coordinates

---

## 4. Governance API

```python
from governance import classify_dataset

result = classify_dataset(df, lifecycle=DatasetLifecycle.APPROVED)
print(result.classification)        # 'sensitive'
print(result.sensitive_columns)     # {'ssn': ['government_id'], ...}
print(result.warnings)              # ['Sensitive datasets cannot be published...']
print(result.blocked_actions)       # ['publishing']
```

---

## 5. Warnings and Blocking Rules

- Confidential or sensitive columns trigger a warning before publish or export.
- Sensitive datasets cannot transition to `published` without explicit organization-admin approval.
- PII columns should be masked or removed before dashboards are shared externally.

---

## 6. Metadata

Each dataset should carry metadata:

- `owner_id`
- `organization_id`
- `department_id`
- `description`
- `source`
- `refresh_frequency`
- `data_steward`
- `classification`
- `lifecycle`

These fields are stored in the database and audited on change.

---

## 7. Best Practices

- Classify datasets at upload time.
- Review warnings before publishing dashboards.
- Do not store raw sensitive data in dashboards; aggregate or mask it.
- Archive datasets that are no longer active.
- Retain audit logs for at least one year.
