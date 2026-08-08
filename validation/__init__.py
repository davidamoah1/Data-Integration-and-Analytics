"""Hospital Data Validation & Quality Management Engine.

A mandatory pre-ETL validation stage for all hospital datasets.

Pipeline:
    Upload → Schema Validation → Structural Validation → Data Profiling
    → Data Quality Rules → Business Rule Validation → Duplicate Detection
    → Missing Data Analysis → Outlier Detection → Clinical Consistency Checks
    → Data Quality Score → Validation Report → User Review → Approval
    → ETL → Metadata → Semantic Layer → Knowledge Graph → KPIs
    → Dashboards → Reports → AI Insights
"""

from validation.ai_copilot import ValidationAICopilot
from validation.approval import ApprovalDecision, ApprovalWorkflow
from validation.audit import ValidationAuditLogger
from validation.business_rules import BusinessRule, BusinessRuleEngine
from validation.clinical_checks import ClinicalValidationEngine
from validation.engine import ValidationEngine, ValidationResult, ValidationStatus
from validation.models import (
    RuleSeverity,
    RuleStatus,
    ValidationFinding,
    ValidationRule,
    ValidationSession,
)
from validation.outlier_detector import OutlierDetector
from validation.profiler import ValidationProfiler
from validation.quality_rules import QualityRulesEngine
from validation.report_generator import ValidationReportGenerator
from validation.routes import router as validation_router
from validation.schema_validator import SchemaValidationResult, SchemaValidator
from validation.scoring import QualityScore, QualityScoreEngine

__all__ = [
    "ValidationEngine",
    "ValidationResult",
    "ValidationStatus",
    "SchemaValidator",
    "SchemaValidationResult",
    "QualityRulesEngine",
    "BusinessRuleEngine",
    "BusinessRule",
    "ClinicalValidationEngine",
    "OutlierDetector",
    "ValidationProfiler",
    "QualityScoreEngine",
    "QualityScore",
    "ValidationReportGenerator",
    "ApprovalWorkflow",
    "ApprovalDecision",
    "ValidationAuditLogger",
    "ValidationAICopilot",
    "ValidationSession",
    "ValidationFinding",
    "ValidationRule",
    "RuleSeverity",
    "RuleStatus",
    "validation_router",
]
