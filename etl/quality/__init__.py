"""Data quality engine â€” detects issues and generates quality reports with recommendations."""

import re

import pandas as pd


class QualityCheck:
    """A single quality check."""

    def __init__(self, name: str, severity: str, check_fn, fix_fn=None):
        self.name = name
        self.severity = severity  # error, warning, info
        self.check_fn = check_fn
        self.fix_fn = fix_fn

    def run(self, df: pd.DataFrame) -> dict:
        result = self.check_fn(df)
        return {
            "check": self.name,
            "severity": self.severity,
            "passed": bool(result.get("passed", True)),
            "affected_rows": int(result.get("affected_rows", 0)),
            "message": str(result.get("message", "")),
            "fixable": self.fix_fn is not None,
        }

    def apply_fix(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.fix_fn:
            return self.fix_fn(df)
        return df


class DataQualityEngine:
    """Runs quality checks against a DataFrame and produces a report."""

    def __init__(self):
        self._checks: list[QualityCheck] = []
        self._register_builtin_checks()

    def add_check(self, check: QualityCheck):
        self._checks.append(check)

    def run_checks(self, df: pd.DataFrame, source_name: str = "unknown") -> dict:
        results = [check.run(df) for check in self._checks]
        passed = sum(1 for r in results if r["passed"])
        failed = sum(1 for r in results if not r["passed"] and r["severity"] == "error")
        warnings = sum(1 for r in results if not r["passed"] and r["severity"] == "warning")
        score = self._compute_score(results)
        recommendations = self._generate_recommendations(results)

        return {
            "source_name": source_name,
            "overall_score": score,
            "checks_passed": passed,
            "checks_failed": failed,
            "checks_warning": warnings,
            "total_checks": len(results),
            "checks": results,
            "recommendations": recommendations,
        }

    def apply_fixes(self, df: pd.DataFrame, check_names: list[str] | None = None) -> pd.DataFrame:
        for check in self._checks:
            if check_names and check.name not in check_names:
                continue
            result = check.run(df)
            if not result["passed"] and check.fix_fn:
                df = check.apply_fix(df)
        return df

    def _compute_score(self, results: list[dict]) -> int:
        if not results:
            return 100
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        errors = sum(1 for r in results if not r["passed"] and r["severity"] == "error")
        warnings = sum(1 for r in results if not r["passed"] and r["severity"] == "warning")
        score = (
            (passed / total) * 70
            + (1 - errors / max(total, 1)) * 20
            + (1 - warnings / max(total, 1)) * 10
        )
        return round(score)

    def _generate_recommendations(self, results: list[dict]) -> list[str]:
        recs = []
        for r in results:
            if not r["passed"]:
                if r["fixable"]:
                    recs.append(
                        f"[{r['severity'].upper()}] {r['check']}: {r['message']} â€” Auto-fix available."
                    )
                else:
                    recs.append(
                        f"[{r['severity'].upper()}] {r['check']}: {r['message']} â€” Manual review required."
                    )
        return recs

    def _register_builtin_checks(self):
        self.add_check(
            QualityCheck(
                "missing_values",
                "warning",
                lambda df: {
                    "passed": df.isnull().sum().sum() == 0,
                    "affected_rows": int(df.isnull().any(axis=1).sum()),
                    "message": f"{int(df.isnull().sum().sum())} null cells found across {int(df.isnull().any().sum())} columns",
                },
                fix_fn=lambda df: df.dropna(subset=[c for c in df.columns if df[c].isnull().all()]),
            )
        )
        self.add_check(
            QualityCheck(
                "duplicate_rows",
                "warning",
                lambda df: {
                    "passed": df.duplicated().sum() == 0,
                    "affected_rows": int(df.duplicated().sum()),
                    "message": f"{int(df.duplicated().sum())} duplicate rows found",
                },
                fix_fn=lambda df: df.drop_duplicates(),
            )
        )
        self.add_check(
            QualityCheck(
                "empty_columns",
                "error",
                lambda df: {
                    "passed": not any(df[c].isnull().all() for c in df.columns),
                    "affected_rows": sum(1 for c in df.columns if df[c].isnull().all()),
                    "message": f"{sum(1 for c in df.columns if df[c].isnull().all())} columns are entirely empty",
                },
            )
        )
        self.add_check(
            QualityCheck(
                "invalid_emails",
                "warning",
                self._check_emails,
            )
        )
        self.add_check(
            QualityCheck(
                "invalid_phone_numbers",
                "info",
                self._check_phones,
            )
        )
        self.add_check(
            QualityCheck(
                "negative_numeric_values",
                "warning",
                lambda df: {
                    "passed": not any(
                        pd.api.types.is_numeric_dtype(df[c]) and (df[c] < 0).any()
                        for c in df.columns
                        if "id" not in c.lower()
                    ),
                    "affected_rows": int(
                        sum(
                            (df[c] < 0).sum()
                            for c in df.columns
                            if pd.api.types.is_numeric_dtype(df[c]) and "id" not in c.lower()
                        )
                    ),
                    "message": "Negative values found in non-ID numeric columns",
                },
            )
        )
        self.add_check(
            QualityCheck(
                "high_null_percentage",
                "warning",
                lambda df: {
                    "passed": len(
                        [c for c in df.columns if (df[c].isnull().sum() / max(len(df), 1)) > 0.5]
                    )
                    == 0,
                    "affected_rows": len(
                        [c for c in df.columns if (df[c].isnull().sum() / max(len(df), 1)) > 0.5]
                    ),
                    "message": f"{len([c for c in df.columns if (df[c].isnull().sum() / max(len(df), 1)) > 0.5])} columns have >50% null values",
                },
            )
        )

    def _check_emails(self, df: pd.DataFrame) -> dict:
        email_cols = [c for c in df.columns if "email" in c.lower()]
        if not email_cols:
            return {"passed": True, "affected_rows": 0, "message": "No email columns found"}
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        invalid = 0
        for col in email_cols:
            valid = df[col].dropna().astype(str).str.match(pattern)
            invalid += int((~valid).sum())
        return {
            "passed": invalid == 0,
            "affected_rows": invalid,
            "message": f"{invalid} invalid email addresses found",
        }

    def _check_phones(self, df: pd.DataFrame) -> dict:
        phone_cols = [c for c in df.columns if "phone" in c.lower()]
        if not phone_cols:
            return {"passed": True, "affected_rows": 0, "message": "No phone columns found"}
        pattern = re.compile(r"^[\d\s\+\-\(\)]{7,20}$")
        invalid = 0
        for col in phone_cols:
            valid = df[col].dropna().astype(str).str.match(pattern)
            invalid += int((~valid).sum())
        return {
            "passed": invalid == 0,
            "affected_rows": invalid,
            "message": f"{invalid} invalid phone numbers found",
        }
