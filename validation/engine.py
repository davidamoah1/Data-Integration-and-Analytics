"""Main Validation Engine â€” orchestrates the full validation pipeline."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from validation.business_rules import BusinessRuleEngine, BusinessRuleFinding
from validation.clinical_checks import ClinicalValidationEngine
from validation.outlier_detector import OutlierDetector
from validation.profiler import DataProfileResult, ValidationProfiler
from validation.quality_rules import QualityFinding, QualityRulesEngine
from validation.schema_validator import SchemaValidationResult, SchemaValidator
from validation.scoring import QualityScore, QualityScoreEngine

logger = logging.getLogger(__name__)


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ValidationResult:
    """Complete result of a validation run."""

    dataset_name: str
    status: ValidationStatus
    schema_result: SchemaValidationResult
    profile: DataProfileResult
    quality_findings: list[QualityFinding] = field(default_factory=list)
    business_rule_findings: list[BusinessRuleFinding] = field(default_factory=list)
    clinical_findings: list[BusinessRuleFinding] = field(default_factory=list)
    outlier_findings: list[BusinessRuleFinding] = field(default_factory=list)
    quality_score: QualityScore | None = None
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    validated_at: str = ""

    @property
    def all_findings(self) -> list[dict]:
        all_f = []
        for f in self.quality_findings:
            all_f.append(
                {"source": "quality", **f.__dict__}
                if hasattr(f, "__dict__")
                else {
                    "source": "quality",
                    "rule_name": f.rule_name,
                    "category": f.category,
                    "severity": f.severity,
                    "column": f.column,
                    "affected_rows": f.affected_rows,
                    "message": f.message,
                    "suggested_fix": f.suggested_fix,
                    "business_impact": f.business_impact,
                }
            )
        for f in self.business_rule_findings + self.clinical_findings + self.outlier_findings:
            all_f.append(
                {
                    "source": "rule",
                    "rule_name": f.rule_name,
                    "category": f.category,
                    "severity": f.severity,
                    "column": f.column,
                    "affected_rows": f.affected_rows,
                    "message": f.message,
                    "suggested_fix": f.suggested_fix,
                    "business_impact": f.business_impact,
                }
            )
        return all_f

    def to_dict(self) -> dict:
        return {
            "dataset_name": self.dataset_name,
            "status": self.status.value,
            "schema": self.schema_result.to_dict(),
            "profile": self.profile.to_dict(),
            "quality_score": self.quality_score.to_dict() if self.quality_score else None,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_info": self.total_info,
            "total_findings": self.total_errors + self.total_warnings + self.total_info,
            "validated_at": self.validated_at,
            "findings": self.all_findings,
        }

    @property
    def can_proceed_to_etl(self) -> bool:
        """Whether ETL can proceed (passed, passed_with_warnings, or approved)."""
        return self.status in (
            ValidationStatus.PASSED,
            ValidationStatus.PASSED_WITH_WARNINGS,
            ValidationStatus.APPROVED,
        )


class ValidationEngine:
    """Orchestrates the full hospital data validation pipeline."""

    def __init__(self):
        self.business_rules = BusinessRuleEngine()

    def validate(
        self,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        schema_type: str = "general",
        skip_schema: bool = False,
    ) -> ValidationResult:
        """Run the full validation pipeline on a DataFrame.

        Pipeline:
        1. Schema Validation
        2. Data Profiling
        3. Data Quality Rules
        4. Business Rule Validation
        5. Duplicate Detection (in quality rules)
        6. Missing Data Analysis (in quality rules)
        7. Outlier Detection
        8. Clinical Consistency Checks
        9. Data Quality Score
        """
        logger.info(f"ValidationEngine: Starting validation for '{dataset_name}' ({len(df)} rows)")

        # 1. Schema validation
        schema_result = SchemaValidator.validate(df, dataset_name, schema_type)

        # 2. Data profiling
        profile = ValidationProfiler.profile(df)

        # 3. Quality rules
        quality_findings = QualityRulesEngine.run(df)

        # 4. Business rules
        business_findings = self.business_rules.run(df)

        # 5. Clinical checks
        clinical_findings = ClinicalValidationEngine.run(df)

        # 6. Outlier detection
        outlier_findings = OutlierDetector.run(df)

        # 7. Quality score
        all_findings_as_br = []
        for qf in quality_findings:
            all_findings_as_br.append(
                BusinessRuleFinding(
                    rule_name=qf.rule_name,
                    category=qf.category,
                    severity=qf.severity,
                    column=qf.column,
                    affected_rows=qf.affected_rows,
                    message=qf.message,
                    suggested_fix=qf.suggested_fix,
                    business_impact=qf.business_impact,
                )
            )
        all_findings_as_br.extend(business_findings)
        all_findings_as_br.extend(clinical_findings)
        all_findings_as_br.extend(outlier_findings)

        quality_score = QualityScoreEngine.compute(df, all_findings_as_br, profile)

        # 8. Determine status
        total_errors = sum(1 for f in all_findings_as_br if f.severity == "error")
        total_errors += len(schema_result.errors)
        total_warnings = sum(1 for f in all_findings_as_br if f.severity == "warning")
        total_warnings += len(schema_result.warnings)
        total_info = sum(1 for f in all_findings_as_br if f.severity == "info")

        if total_errors == 0 and total_warnings == 0:
            status = ValidationStatus.PASSED
        elif total_errors == 0:
            status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            status = ValidationStatus.FAILED

        result = ValidationResult(
            dataset_name=dataset_name,
            status=status,
            schema_result=schema_result,
            profile=profile,
            quality_findings=quality_findings,
            business_rule_findings=business_findings,
            clinical_findings=clinical_findings,
            outlier_findings=outlier_findings,
            quality_score=quality_score,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info=total_info,
            validated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"ValidationEngine: Completed â€” status={status.value}, "
            f"errors={total_errors}, warnings={total_warnings}, "
            f"score={quality_score.overall:.1f} ({quality_score.traffic_light})"
        )

        return result
