"""Quality Intelligence Engine.

Orchestrates all quality checks, drift detection, and schema monitoring
into a single composite quality score with recommendations.

Produces a QualityIntelligenceResult containing:
  - All quality findings (from checks)
  - Drift detection results (if reference data available)
  - Schema change results (if baseline available)
  - Composite quality score (0-100) with traffic light
  - Summary and recommendations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from data_quality.checks import QualityCheckEngine, QualityFinding, Severity
from data_quality.drift_detector import DriftDetector, DriftResult
from data_quality.schema_monitor import SchemaChangeResult, SchemaMonitor


@dataclass
class QualityScore:
    """Multi-dimensional quality score."""

    completeness: float  # 0-100
    validity: float
    uniqueness: float
    consistency: float
    timeliness: float  # Based on drift
    overall: float
    traffic_light: str  # green, yellow, red
    grade: str  # A, B, C, D, F

    def to_dict(self) -> dict:
        return {
            "completeness": round(self.completeness, 1),
            "validity": round(self.validity, 1),
            "uniqueness": round(self.uniqueness, 1),
            "consistency": round(self.consistency, 1),
            "timeliness": round(self.timeliness, 1),
            "overall": round(self.overall, 1),
            "traffic_light": self.traffic_light,
            "grade": self.grade,
        }


@dataclass
class QualityIntelligenceResult:
    """Complete result of quality intelligence analysis."""

    findings: list[QualityFinding] = field(default_factory=list)
    drift_result: DriftResult | None = None
    schema_result: SchemaChangeResult | None = None
    score: QualityScore | None = None
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    checked_at: str = ""

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity in (Severity.ERROR, Severity.CRITICAL))

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    def to_dict(self) -> dict:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "drift": self.drift_result.to_dict() if self.drift_result else None,
            "schema_changes": self.schema_result.to_dict() if self.schema_result else None,
            "score": self.score.to_dict() if self.score else None,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "checked_at": self.checked_at,
        }


class QualityEngine:
    """Orchestrates all data quality intelligence checks."""

    def __init__(
        self,
        reference_df: pd.DataFrame | None = None,
        baseline_schema: pd.DataFrame | None = None,
    ):
        """Initialize the quality engine.

        Args:
            reference_df: Reference dataset for drift detection. If None,
                          time-based drift is used instead.
            baseline_schema: Baseline DataFrame for schema change detection.
        """
        self.reference_df = reference_df
        self.baseline_schema = baseline_schema

    def run(
        self,
        df: pd.DataFrame,
        col_mapping: dict[str, str] | None = None,
        detect_drift: bool = True,
        detect_schema_changes: bool = True,
    ) -> QualityIntelligenceResult:
        """Run full quality intelligence analysis.

        Args:
            df: DataFrame to analyze.
            col_mapping: Column-to-entity mapping (optional).
            detect_drift: Whether to run drift detection.
            detect_schema_changes: Whether to run schema change detection.

        Returns:
            QualityIntelligenceResult with all findings, scores, and recommendations.
        """
        # 1. Run quality checks
        findings = QualityCheckEngine.run(df, col_mapping)

        # 2. Drift detection
        drift_result = None
        if detect_drift:
            if self.reference_df is not None:
                drift_result = DriftDetector.detect(self.reference_df, df)
            else:
                # Try time-based drift
                date_col = None
                for c in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[c]):
                        date_col = c
                        break
                if date_col is None and col_mapping:
                    for col, entity in col_mapping.items():
                        if entity == "date" and col in df.columns:
                            date_col = col
                            break
                if date_col:
                    drift_result = DriftDetector.detect_time_drift(df, date_col)

        # 3. Schema change detection
        schema_result = None
        if detect_schema_changes and self.baseline_schema is not None:
            schema_result = SchemaMonitor.compare(self.baseline_schema, df)

        # 4. Compute quality score
        score = self._compute_score(df, findings, drift_result, schema_result)

        # 5. Generate recommendations
        recommendations = self._generate_recommendations(findings, drift_result, schema_result)

        # 6. Generate summary
        summary = self._generate_summary(findings, drift_result, schema_result, score)

        return QualityIntelligenceResult(
            findings=findings,
            drift_result=drift_result,
            schema_result=schema_result,
            score=score,
            summary=summary,
            recommendations=recommendations,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _compute_score(
        df: pd.DataFrame,
        findings: list[QualityFinding],
        drift_result: DriftResult | None,
        schema_result: SchemaChangeResult | None,
    ) -> QualityScore:
        """Compute multi-dimensional quality score."""
        total_rows = max(len(df), 1)
        total_cells = total_rows * max(len(df.columns), 1)

        # Completeness: based on missing values
        missing_findings = [
            f
            for f in findings
            if f.check_name in ("missing_values", "blank_fields", "empty_column")
        ]
        missing_cells = sum(f.affected_rows for f in missing_findings)
        completeness = max(0, 100 - (missing_cells / max(total_cells, 1)) * 100)

        # Validity: based on invalid/sentinel/out-of-range findings
        validity_findings = [f for f in findings if f.category == "validity"]
        validity_errors = sum(
            f.affected_rows
            for f in validity_findings
            if f.severity in (Severity.ERROR, Severity.CRITICAL, Severity.WARNING)
        )
        validity = max(0, 100 - (validity_errors / total_rows) * 50)

        # Uniqueness: based on duplicates
        dup_findings = [f for f in findings if "duplicate" in f.check_name]
        dup_rows = sum(f.affected_rows for f in dup_findings)
        uniqueness = max(0, 100 - (dup_rows / total_rows) * 100)

        # Consistency: based on consistency findings
        consistency_findings = [f for f in findings if f.category == "consistency"]
        consistency_penalty = sum(
            min(f.affected_rows / total_rows, 1) * 15 for f in consistency_findings
        )
        consistency = max(0, 100 - consistency_penalty)

        # Timeliness: based on drift
        if drift_result:
            drift_penalty = min(drift_result.drift_score * 100, 50)
            timeliness = max(0, 100 - drift_penalty)
        else:
            timeliness = 100.0

        # Schema change penalty
        if schema_result and schema_result.changes_detected:
            schema_penalty = sum(
                10 if c.severity == "error" else 5 if c.severity == "warning" else 2
                for c in schema_result.changes
            )
            consistency = max(0, consistency - schema_penalty)

        # Overall: weighted average
        overall = (
            completeness * 0.25
            + validity * 0.20
            + uniqueness * 0.20
            + consistency * 0.20
            + timeliness * 0.15
        )

        # Traffic light
        if overall >= 85:
            traffic_light = "green"
        elif overall >= 60:
            traffic_light = "yellow"
        else:
            traffic_light = "red"

        # Grade
        if overall >= 90:
            grade = "A"
        elif overall >= 80:
            grade = "B"
        elif overall >= 70:
            grade = "C"
        elif overall >= 60:
            grade = "D"
        else:
            grade = "F"

        return QualityScore(
            completeness=completeness,
            validity=validity,
            uniqueness=uniqueness,
            consistency=consistency,
            timeliness=timeliness,
            overall=overall,
            traffic_light=traffic_light,
            grade=grade,
        )

    @staticmethod
    def _generate_recommendations(
        findings: list[QualityFinding],
        drift_result: DriftResult | None,
        schema_result: SchemaChangeResult | None,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations: list[str] = []

        # From findings
        for f in findings:
            if f.severity in (Severity.CRITICAL, Severity.ERROR):
                recommendations.append(
                    f"[{f.severity.value.upper()}] {f.message} — {f.suggested_fix}"
                )

        # From drift
        if drift_result and drift_result.drift_detected:
            drifted = [c for c in drift_result.drifted_columns if c.drift_detected]
            for c in drifted[:3]:
                recommendations.append(
                    f"[DRIFT] {c.message} — Investigate upstream data source changes."
                )

        # From schema changes
        if schema_result and schema_result.changes_detected:
            for c in schema_result.changes:
                if c.severity == "error":
                    recommendations.append(f"[SCHEMA] {c.message} — {c.impact}")

        # Deduplicate
        seen = set()
        unique = []
        for r in recommendations:
            if r not in seen:
                seen.add(r)
                unique.append(r)

        return unique[:15]

    @staticmethod
    def _generate_summary(
        findings: list[QualityFinding],
        drift_result: DriftResult | None,
        schema_result: SchemaChangeResult | None,
        score: QualityScore,
    ) -> str:
        """Generate a human-readable quality summary."""
        errors = sum(1 for f in findings if f.severity in (Severity.ERROR, Severity.CRITICAL))
        warnings = sum(1 for f in findings if f.severity == Severity.WARNING)
        infos = sum(1 for f in findings if f.severity == Severity.INFO)

        parts = [
            f"Data Quality Score: {score.overall:.1f}/100 ({score.traffic_light} — Grade {score.grade})",
            f"Findings: {errors} error(s), {warnings} warning(s), {infos} info(s)",
        ]

        if drift_result:
            if drift_result.drift_detected:
                drifted_count = sum(1 for c in drift_result.drifted_columns if c.drift_detected)
                parts.append(f"Data drift: detected in {drifted_count} column(s)")
            else:
                parts.append("Data drift: none detected")

        if schema_result:
            if schema_result.changes_detected:
                parts.append(f"Schema changes: {len(schema_result.changes)} detected")
            else:
                parts.append("Schema changes: none detected")

        return " | ".join(parts)
