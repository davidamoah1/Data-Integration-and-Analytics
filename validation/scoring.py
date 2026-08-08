"""Quality Score Engine — computes multi-dimensional data quality scores with traffic lights."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from validation.business_rules import BusinessRuleFinding
from validation.profiler import DataProfileResult


@dataclass
class QualityScore:
    completeness: float  # 0-100
    accuracy: float
    consistency: float
    validity: float
    uniqueness: float
    integrity: float
    overall: float
    traffic_light: str  # green, yellow, red

    def to_dict(self) -> dict:
        return {
            "completeness": round(self.completeness, 1),
            "accuracy": round(self.accuracy, 1),
            "consistency": round(self.consistency, 1),
            "validity": round(self.validity, 1),
            "uniqueness": round(self.uniqueness, 1),
            "integrity": round(self.integrity, 1),
            "overall": round(self.overall, 1),
            "traffic_light": self.traffic_light,
        }


class QualityScoreEngine:
    """Computes quality scores from findings and profile data."""

    @staticmethod
    def compute(
        df: pd.DataFrame,
        findings: list[BusinessRuleFinding],
        profile: DataProfileResult,
    ) -> QualityScore:
        total_rows = max(len(df), 1)
        total_cells = total_rows * max(len(df.columns), 1)

        # Completeness: based on missing values
        total_missing = sum(
            f.affected_rows
            for f in findings
            if f.rule_name in ("missing_values", "blank_fields", "empty_column")
        )
        completeness = max(0, 100 - (total_missing / max(total_cells, 1)) * 100)

        # Accuracy: based on clinical/business rule errors
        accuracy_findings = [
            f for f in findings if f.category in ("clinical", "business") and f.severity == "error"
        ]
        accuracy_errors = sum(f.affected_rows for f in accuracy_findings)
        accuracy = max(0, 100 - (accuracy_errors / total_rows) * 100)

        # Consistency: based on consistency-related findings
        consistency_findings = [
            f
            for f in findings
            if f.rule_name in ("constant_column", "mixed_data_types", "bmi_consistency")
        ]
        consistency_penalty = sum(
            min(f.affected_rows / total_rows, 1) * 10 for f in consistency_findings
        )
        consistency = max(0, 100 - consistency_penalty)

        # Validity: based on format/invalid findings
        validity_findings = [
            f for f in findings if f.category == "validity" or "invalid" in f.rule_name
        ]
        validity_errors = sum(f.affected_rows for f in validity_findings)
        validity = max(0, 100 - (validity_errors / total_rows) * 100)

        # Uniqueness: based on duplicates
        dup_findings = [f for f in findings if "duplicate" in f.rule_name]
        dup_rows = sum(f.affected_rows for f in dup_findings)
        uniqueness = max(0, 100 - (dup_rows / total_rows) * 100)

        # Integrity: based on relationship/referential findings
        integrity_findings = [
            f
            for f in findings
            if f.rule_name
            in (
                "visit_requires_patient",
                "diagnosis_requires_clinician",
                "medication_requires_prescription",
                "lab_result_requires_order",
                "admission_before_discharge",
                "bp_systolic_gt_diastolic",
            )
        ]
        integrity_errors = sum(f.affected_rows for f in integrity_findings)
        integrity = max(0, 100 - (integrity_errors / total_rows) * 100)

        # Overall: weighted average
        overall = (
            completeness * 0.25
            + accuracy * 0.20
            + consistency * 0.15
            + validity * 0.15
            + uniqueness * 0.15
            + integrity * 0.10
        )

        # Traffic light
        if overall >= 85:
            traffic_light = "green"
        elif overall >= 60:
            traffic_light = "yellow"
        else:
            traffic_light = "red"

        return QualityScore(
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency,
            validity=validity,
            uniqueness=uniqueness,
            integrity=integrity,
            overall=overall,
            traffic_light=traffic_light,
        )
