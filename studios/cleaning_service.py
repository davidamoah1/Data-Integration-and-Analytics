"""AI Data Cleaning Engine — automatic detection and transformation of data issues."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import CleaningJob


# Country name normalization map
COUNTRY_NORMALIZATION = {
    "usa": "United States",
    "us": "United States",
    "u.s.a": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k": "United Kingdom",
    "great britain": "United Kingdom",
    "gh": "Ghana",
    "nga": "Nigeria",
    "ng": "Nigeria",
    "ke": "Kenya",
    "za": "South Africa",
    "sa": "South Africa",
}

# Common category normalizations
CATEGORY_NORMALIZATION = {
    "y": "Yes",
    "n": "No",
    "t": "True",
    "f": "False",
    "na": "N/A",
    "n/a": "N/A",
    "null": "N/A",
    "none": "N/A",
    "": "N/A",
}


class DataCleaningService:
    """AI-powered data cleaning engine."""

    def __init__(self, db: DbSession):
        self.db = db

    def create_job(self, org_id: int, dataset_id: int, user_id: int) -> CleaningJob:
        job = CleaningJob(
            organization_id=org_id,
            dataset_id=dataset_id,
            created_by=user_id,
            status="pending",
        )
        self.db.add(job)
        self.db.flush()
        self.db.commit()
        return job

    def analyze_dataset(self, df: pd.DataFrame) -> dict:
        """Analyze a dataset and detect all data quality issues.

        Returns a structured report of issues found.
        """
        issues = []

        for col in df.columns:
            col_data = df[col]

            # 1. Missing values
            missing_count = col_data.isna().sum()
            if missing_count > 0:
                issues.append({
                    "column": col,
                    "issue_type": "missing_values",
                    "count": int(missing_count),
                    "percentage": round(missing_count / len(df) * 100, 2),
                    "suggestion": "Fill with mean (numeric) or mode (categorical)",
                    "severity": "high" if missing_count / len(df) > 0.3 else "medium",
                })

            # 2. Duplicates
            dup_count = col_data.duplicated().sum()
            if dup_count > 0 and col_data.dtype == "object":
                issues.append({
                    "column": col,
                    "issue_type": "duplicates",
                    "count": int(dup_count),
                    "suggestion": "Review for potential duplicate records",
                    "severity": "low",
                })

            # 3. Wrong formats / inconsistent categories
            if col_data.dtype == "object":
                unique_vals = col_data.dropna().unique()
                if len(unique_vals) <= 20:
                    # Check for inconsistent categories
                    normalized = [self._normalize_category(v) for v in unique_vals]
                    if len(set(normalized)) < len(set(unique_vals)):
                        issues.append({
                            "column": col,
                            "issue_type": "inconsistent_categories",
                            "count": len(unique_vals) - len(set(normalized)),
                            "examples": list(unique_vals[:10]),
                            "suggestion": "Standardize category names",
                            "severity": "medium",
                        })

                    # Check for country name inconsistencies
                    if any(str(v).lower().strip() in COUNTRY_NORMALIZATION for v in unique_vals):
                        issues.append({
                            "column": col,
                            "issue_type": "inconsistent_country_names",
                            "count": sum(1 for v in unique_vals if str(v).lower().strip() in COUNTRY_NORMALIZATION),
                            "examples": list(unique_vals[:10]),
                            "suggestion": "Normalize country names to standard format",
                            "severity": "medium",
                        })

            # 4. Invalid dates
            if col_data.dtype == "object":
                date_like = col_data.apply(lambda x: self._is_date(str(x)) if pd.notna(x) else False)
                if date_like.sum() > len(df) * 0.5:
                    invalid_dates = col_data[~date_like & col_data.notna()]
                    if len(invalid_dates) > 0:
                        issues.append({
                            "column": col,
                            "issue_type": "invalid_dates",
                            "count": len(invalid_dates),
                            "suggestion": "Parse as datetime and fix invalid entries",
                            "severity": "high",
                        })

            # 5. Incorrect data types
            if col_data.dtype == "object":
                numeric_like = col_data.apply(lambda x: self._is_numeric(str(x)) if pd.notna(x) else False)
                if numeric_like.sum() > len(df) * 0.8:
                    issues.append({
                        "column": col,
                        "issue_type": "wrong_data_type",
                        "current_type": "string",
                        "suggested_type": "numeric",
                        "count": int(numeric_like.sum()),
                        "suggestion": "Convert to numeric type",
                        "severity": "medium",
                    })

            # 6. Outliers (numeric only)
            if col_data.dtype in ("int64", "float64"):
                outliers = self._detect_outliers(col_data)
                if len(outliers) > 0:
                    issues.append({
                        "column": col,
                        "issue_type": "outliers",
                        "count": len(outliers),
                        "indices": outliers[:20].tolist(),
                        "suggestion": "Review using IQR or Z-score method",
                        "severity": "medium",
                    })

        return {
            "total_issues": len(issues),
            "issues_by_severity": {
                "high": sum(1 for i in issues if i["severity"] == "high"),
                "medium": sum(1 for i in issues if i["severity"] == "medium"),
                "low": sum(1 for i in issues if i["severity"] == "low"),
            },
            "issues": issues,
        }

    def propose_transformations(self, df: pd.DataFrame, issues: list[dict]) -> list[dict]:
        """Generate transformation proposals for detected issues."""
        transformations = []

        for issue in issues:
            col = issue["column"]
            issue_type = issue["issue_type"]

            if issue_type == "missing_values":
                if df[col].dtype in ("int64", "float64"):
                    fill_value = float(df[col].mean())
                    transformations.append({
                        "column": col,
                        "action": "fill_missing",
                        "method": "mean",
                        "value": round(fill_value, 2),
                        "reason": f"Fill {issue['count']} missing values with mean ({round(fill_value, 2)})",
                    })
                else:
                    mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
                    transformations.append({
                        "column": col,
                        "action": "fill_missing",
                        "method": "mode",
                        "value": str(mode_val),
                        "reason": f"Fill {issue['count']} missing values with mode ('{mode_val}')",
                    })

            elif issue_type == "inconsistent_country_names":
                transformations.append({
                    "column": col,
                    "action": "normalize_countries",
                    "mapping": COUNTRY_NORMALIZATION,
                    "reason": "Standardize country names (e.g., USA → United States)",
                })

            elif issue_type == "inconsistent_categories":
                transformations.append({
                    "column": col,
                    "action": "normalize_categories",
                    "mapping": CATEGORY_NORMALIZATION,
                    "reason": "Standardize category values (e.g., y → Yes, n → No)",
                })

            elif issue_type == "wrong_data_type":
                transformations.append({
                    "column": col,
                    "action": "convert_type",
                    "target_type": "numeric",
                    "reason": f"Convert {col} from string to numeric",
                })

            elif issue_type == "invalid_dates":
                transformations.append({
                    "column": col,
                    "action": "parse_dates",
                    "reason": f"Parse {col} as datetime, flag invalid entries",
                })

            elif issue_type == "outliers":
                transformations.append({
                    "column": col,
                    "action": "flag_outliers",
                    "method": "iqr",
                    "reason": f"Flag {issue['count']} outliers in {col} for review",
                })

        return transformations

    def apply_transformations(
        self,
        df: pd.DataFrame,
        approved_transformations: list[dict],
    ) -> tuple[pd.DataFrame, dict]:
        """Apply user-approved transformations and return cleaned data + summary."""
        original_shape = df.shape
        changes_log = []

        for t in approved_transformations:
            col = t["column"]
            action = t["action"]

            if action == "fill_missing":
                if t["method"] == "mean":
                    before = df[col].isna().sum()
                    df[col] = df[col].fillna(t["value"])
                    changes_log.append(f"Filled {before} missing values in '{col}' with mean {t['value']}")
                elif t["method"] == "mode":
                    before = df[col].isna().sum()
                    df[col] = df[col].fillna(t["value"])
                    changes_log.append(f"Filled {before} missing values in '{col}' with mode '{t['value']}'")

            elif action == "normalize_countries":
                mapping = {k.lower().strip(): v for k, v in t["mapping"].items()}
                before = df[col].copy()
                df[col] = df[col].apply(lambda x: mapping.get(str(x).lower().strip(), x) if pd.notna(x) else x)
                changed = (before != df[col]).sum()
                changes_log.append(f"Normalized {changed} country names in '{col}'")

            elif action == "normalize_categories":
                mapping = {k.lower().strip(): v for k, v in t["mapping"].items()}
                before = df[col].copy()
                df[col] = df[col].apply(lambda x: mapping.get(str(x).lower().strip(), x) if pd.notna(x) else x)
                changed = (before != df[col]).sum()
                changes_log.append(f"Standardized {changed} category values in '{col}'")

            elif action == "convert_type":
                df[col] = pd.to_numeric(df[col], errors="coerce")
                changes_log.append(f"Converted '{col}' to numeric type")

            elif action == "parse_dates":
                df[col] = pd.to_datetime(df[col], errors="coerce")
                changes_log.append(f"Parsed '{col}' as datetime")

            elif action == "flag_outliers":
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                df[f"{col}_is_outlier"] = (df[col] < lower) | (df[col] > upper)
                count = df[f"{col}_is_outlier"].sum()
                changes_log.append(f"Flagged {count} outliers in '{col}'")

        summary = {
            "original_shape": list(original_shape),
            "final_shape": list(df.shape),
            "changes": changes_log,
            "total_changes": len(changes_log),
        }
        return df, summary

    def get_job(self, job_id: int, org_id: int) -> CleaningJob | None:
        return self.db.execute(
            select(CleaningJob).where(
                CleaningJob.id == job_id,
                CleaningJob.organization_id == org_id,
            )
        ).scalar_one_or_none()

    def list_jobs(self, org_id: int) -> list[CleaningJob]:
        return self.db.execute(
            select(CleaningJob)
            .where(CleaningJob.organization_id == org_id)
            .order_by(CleaningJob.created_at.desc())
        ).scalars().all()

    def update_job(self, job_id: int, **kwargs) -> CleaningJob:
        job = self.db.execute(
            select(CleaningJob).where(CleaningJob.id == job_id)
        ).scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")
        for k, v in kwargs.items():
            setattr(job, k, v)
        self.db.commit()
        return job

    # ─── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _is_date(value: str) -> bool:
        try:
            pd.to_datetime(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_numeric(value: str) -> bool:
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _normalize_category(value: str) -> str:
        return CATEGORY_NORMALIZATION.get(value.lower().strip(), value)

    @staticmethod
    def _detect_outliers(series: pd.Series) -> pd.Index:
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return series[(series < lower) | (series > upper)].index
