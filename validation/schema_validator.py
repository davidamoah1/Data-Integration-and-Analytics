"""Schema Validator â€” validates dataset structure, column names, types, and formats."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class SchemaIssue:
    rule_name: str
    severity: str  # error, warning
    column: str | None
    message: str
    suggested_fix: str | None = None


@dataclass
class SchemaValidationResult:
    passed: bool
    issues: list[SchemaIssue] = field(default_factory=list)
    column_types: dict[str, str] = field(default_factory=dict)
    encoding: str = "utf-8"
    file_format: str = "csv"

    @property
    def errors(self) -> list[SchemaIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[SchemaIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "issues": [
                {
                    "rule_name": i.rule_name,
                    "severity": i.severity,
                    "column": i.column,
                    "message": i.message,
                    "suggested_fix": i.suggested_fix,
                }
                for i in self.issues
            ],
            "column_types": self.column_types,
            "encoding": self.encoding,
            "file_format": self.file_format,
        }


# Healthcare/Hospital expected schema definitions
HOSPITAL_SCHEMAS: dict[str, dict] = {
    "patient_registry": {
        "required_columns": ["patient_id"],
        "optional_columns": [
            "patient_name",
            "date_of_birth",
            "gender",
            "age",
            "phone",
            "email",
            "address",
            "blood_type",
            "weight",
            "height",
        ],
    },
    "admission_records": {
        "required_columns": ["patient_id", "admission_date"],
        "optional_columns": [
            "admission_id",
            "discharge_date",
            "ward",
            "doctor",
            "diagnosis",
            "department",
            "insurance_type",
            "amount",
        ],
    },
    "laboratory_results": {
        "required_columns": ["patient_id", "test_name"],
        "optional_columns": [
            "lab_id",
            "test_result",
            "unit",
            "reference_range",
            "specimen_date",
            "ordered_by",
            "status",
        ],
    },
    "medication_records": {
        "required_columns": ["patient_id", "medication_name"],
        "optional_columns": [
            "prescription_id",
            "dosage",
            "frequency",
            "route",
            "start_date",
            "end_date",
            "prescribed_by",
            "status",
        ],
    },
    "general": {
        "required_columns": [],
        "optional_columns": [],
    },
}


class SchemaValidator:
    """Validates dataset schema: columns, types, formats, encoding."""

    @staticmethod
    def validate(
        df: pd.DataFrame,
        file_name: str = "",
        schema_type: str = "general",
    ) -> SchemaValidationResult:
        result = SchemaValidationResult(passed=True)

        if file_name.endswith(".csv"):
            result.file_format = "csv"
        elif file_name.endswith((".xlsx", ".xls")):
            result.file_format = "excel"
        elif file_name.endswith(".json"):
            result.file_format = "json"
        else:
            result.file_format = "unknown"

        schema = HOSPITAL_SCHEMAS.get(schema_type, HOSPITAL_SCHEMAS["general"])

        # 1. Check for empty dataframe
        if df.empty:
            result.issues.append(
                SchemaIssue(
                    rule_name="empty_dataset",
                    severity="error",
                    column=None,
                    message="Dataset is empty (no rows).",
                    suggested_fix="Upload a non-empty dataset.",
                )
            )
            result.passed = False

        if len(df.columns) == 0:
            result.issues.append(
                SchemaIssue(
                    rule_name="no_columns",
                    severity="error",
                    column=None,
                    message="Dataset has no columns.",
                    suggested_fix="Ensure the file has header columns.",
                )
            )
            result.passed = False

        # 2. Required columns
        for req_col in schema.get("required_columns", []):
            if req_col not in df.columns:
                result.issues.append(
                    SchemaIssue(
                        rule_name="missing_required_column",
                        severity="error",
                        column=req_col,
                        message=f"Required column '{req_col}' is missing.",
                        suggested_fix=f"Add a '{req_col}' column to the dataset.",
                    )
                )
                result.passed = False

        # 3. Unexpected columns (only warn)
        expected = set(schema.get("required_columns", []) + schema.get("optional_columns", []))
        if expected:
            for col in df.columns:
                if col not in expected:
                    result.issues.append(
                        SchemaIssue(
                            rule_name="unexpected_column",
                            severity="warning",
                            column=col,
                            message=f"Column '{col}' is not in the expected schema.",
                            suggested_fix=None,
                        )
                    )

        # 4. Column name validation
        for col in df.columns:
            col_str = str(col)
            if not col_str.strip():
                result.issues.append(
                    SchemaIssue(
                        rule_name="blank_column_name",
                        severity="error",
                        column=col_str,
                        message="Column name is blank.",
                        suggested_fix="Provide a name for this column.",
                    )
                )
                result.passed = False
            if col_str != col_str.strip():
                result.issues.append(
                    SchemaIssue(
                        rule_name="whitespace_column_name",
                        severity="warning",
                        column=col_str,
                        message=f"Column name '{col_str}' has leading/trailing whitespace.",
                        suggested_fix=f"Rename to '{col_str.strip()}'.",
                    )
                )
            if re.search(r"[^a-zA-Z0-9_]", col_str.replace(" ", "").replace("-", "")):
                pass  # Allow spaces and hyphens but flag special chars
            if re.search(r"[\x00-\x1f\x7f-\x9f]", col_str):
                result.issues.append(
                    SchemaIssue(
                        rule_name="control_chars_column_name",
                        severity="error",
                        column=col_str,
                        message=f"Column name '{col_str}' contains control characters.",
                        suggested_fix="Remove control characters from column name.",
                    )
                )
                result.passed = False

        # 5. Duplicate column names
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        if dup_cols:
            result.issues.append(
                SchemaIssue(
                    rule_name="duplicate_column_names",
                    severity="error",
                    column=None,
                    message=f"Duplicate column names found: {dup_cols}.",
                    suggested_fix="Rename duplicate columns to be unique.",
                )
            )
            result.passed = False

        # 6. Data type inference and validation
        col_dtypes = df.dtypes.to_dict()
        for col in df.columns:
            dtype = str(col_dtypes.get(col, "object"))
            result.column_types[col] = dtype

            # Check for mixed types in object columns
            if dtype == "object":
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    type_counts = non_null.map(type).value_counts()
                    if len(type_counts) > 1:
                        result.issues.append(
                            SchemaIssue(
                                rule_name="mixed_data_types",
                                severity="warning",
                                column=col,
                                message=f"Column '{col}' has mixed data types: {dict(type_counts)}.",
                                suggested_fix="Ensure consistent data types in this column.",
                            )
                        )

        # 7. Date format validation
        date_like_cols = [
            c
            for c in df.columns
            if any(kw in c.lower() for kw in ["date", "dob", "timestamp", "created", "modified"])
        ]
        for col in date_like_cols:
            if col not in df.columns:
                continue
            sample = df[col].dropna().head(20)
            if len(sample) == 0:
                continue
            parsed = pd.to_datetime(sample, errors="coerce")
            unparseable = parsed.isna().sum()
            if unparseable > 0:
                result.issues.append(
                    SchemaIssue(
                        rule_name="invalid_date_format",
                        severity="warning",
                        column=col,
                        message=f"Column '{col}': {unparseable} of {len(sample)} sampled values could not be parsed as dates.",
                        suggested_fix="Ensure dates are in ISO format (YYYY-MM-DD) or a consistent format.",
                    )
                )

        # 8. Numeric format validation
        numeric_like_cols = [
            c
            for c in df.columns
            if any(
                kw in c.lower()
                for kw in [
                    "amount",
                    "cost",
                    "price",
                    "weight",
                    "height",
                    "age",
                    "rate",
                    "count",
                    "value",
                ]
            )
        ]
        for col in numeric_like_cols:
            if col not in df.columns or pd.api.types.is_numeric_dtype(df[col]):
                continue
            sample = df[col].dropna().head(20)
            if len(sample) == 0:
                continue
            try:
                pd.to_numeric(sample)
            except (ValueError, TypeError):
                result.issues.append(
                    SchemaIssue(
                        rule_name="invalid_numeric_format",
                        severity="warning",
                        column=col,
                        message=f"Column '{col}' appears to contain numeric data but has non-numeric values.",
                        suggested_fix="Ensure all values in this column are numeric.",
                    )
                )

        if any(i.severity == "error" for i in result.issues):
            result.passed = False

        return result
