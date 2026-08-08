"""AI Copilot integration for the Hospital Data Validation Engine.

Allows the AI Copilot to answer questions about validation results,
findings, quality scores, and suggest corrections.
"""

from __future__ import annotations

from validation.engine import ValidationResult, ValidationStatus


class ValidationAICopilot:
    """Provides AI-friendly context and answers about validation results."""

    @staticmethod
    def build_context(result: ValidationResult) -> dict:
        """Build AI context from a validation result."""
        findings = result.all_findings
        error_findings = [f for f in findings if f.get("severity") == "error"]
        warning_findings = [f for f in findings if f.get("severity") == "warning"]

        # Group by rule
        by_rule: dict[str, list] = {}
        for f in findings:
            rule = f.get("rule_name", "unknown")
            by_rule.setdefault(rule, []).append(f)

        # Most failed rules
        rule_summary = [
            {
                "rule": rule,
                "count": len(items),
                "total_affected": sum(i.get("affected_rows", 0) for i in items),
                "severity": items[0].get("severity", "info"),
            }
            for rule, items in sorted(by_rule.items(), key=lambda x: -len(x[1]))
        ]

        # Column quality
        column_issues: dict[str, list] = {}
        for f in findings:
            col = f.get("column")
            if col:
                column_issues.setdefault(col, []).append(f.get("rule_name"))

        return {
            "validation_status": result.status.value,
            "quality_score": result.quality_score.to_dict() if result.quality_score else None,
            "total_errors": result.total_errors,
            "total_warnings": result.total_warnings,
            "total_info": result.total_info,
            "row_count": result.profile.row_count,
            "column_count": result.profile.column_count,
            "top_failed_rules": rule_summary[:10],
            "columns_with_issues": {col: list(set(rules)) for col, rules in column_issues.items()},
            "error_findings": [
                {
                    "rule": f.get("rule_name"),
                    "message": f.get("message"),
                    "column": f.get("column"),
                    "affected_rows": f.get("affected_rows"),
                    "fix": f.get("suggested_fix"),
                }
                for f in error_findings[:20]
            ],
            "warning_findings": [
                {
                    "rule": f.get("rule_name"),
                    "message": f.get("message"),
                    "column": f.get("column"),
                    "fix": f.get("suggested_fix"),
                }
                for f in warning_findings[:10]
            ],
        }

    @staticmethod
    def answer_question(question: str, result: ValidationResult) -> str:
        """Answer a natural language question about validation results."""
        q_lower = question.lower()
        findings = result.all_findings
        score = result.quality_score

        # Why did validation fail?
        if "why" in q_lower and ("fail" in q_lower or "failing" in q_lower):
            if result.status == ValidationStatus.PASSED:
                return "Validation passed successfully — no errors were found."
            if result.status == ValidationStatus.PASSED_WITH_WARNINGS:
                warnings = [f for f in findings if f.get("severity") == "warning"]
                return (
                    f"Validation passed with {len(warnings)} warnings. "
                    f"Top warnings: {', '.join(f.get('rule_name', '') for f in warnings[:5])}."
                )
            errors = [f for f in findings if f.get("severity") == "error"]
            reasons = [f"{f.get('rule_name')}: {f.get('message')}" for f in errors[:5]]
            return f"Validation failed with {len(errors)} errors.\n" f"Top reasons:\n" + "\n".join(
                f"  - {r}" for r in reasons
            )

        # Which records have errors?
        if "which" in q_lower and ("record" in q_lower or "row" in q_lower or "error" in q_lower):
            error_findings = [f for f in findings if f.get("severity") == "error"]
            if not error_findings:
                return "No error-level findings in the validation results."
            lines = []
            for f in error_findings[:10]:
                lines.append(
                    f"  - {f.get('rule_name')} (column: {f.get('column', 'N/A')}): "
                    f"{f.get('affected_rows', 0)} rows affected — {f.get('message', '')}"
                )
            return "Error findings:\n" + "\n".join(lines)

        # Which departments have poor data quality?
        if "department" in q_lower or "facility" in q_lower:
            dept_findings = [
                f
                for f in findings
                if "department" in f.get("column", "").lower()
                or "dept" in f.get("column", "").lower()
            ]
            if not dept_findings:
                return "No department-specific data quality issues were detected."
            lines = [f"  - {f.get('rule_name')}: {f.get('message')}" for f in dept_findings[:10]]
            return "Department-related findings:\n" + "\n".join(lines)

        # What should be corrected?
        if "correct" in q_lower or "fix" in q_lower or "should" in q_lower:
            fixable = [f for f in findings if f.get("suggested_fix")]
            if not fixable:
                return "No specific corrections are suggested — all checks passed."
            lines = []
            for f in fixable[:10]:
                lines.append(
                    f"  - [{f.get('severity', '').upper()}] {f.get('rule_name')}: {f.get('suggested_fix')}"
                )
            return "Suggested corrections:\n" + "\n".join(lines)

        # Which rules failed most?
        if "rule" in q_lower and ("fail" in q_lower or "most" in q_lower):
            rule_counts: dict[str, int] = {}
            for f in findings:
                rule = f.get("rule_name", "unknown")
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
            sorted_rules = sorted(rule_counts.items(), key=lambda x: -x[1])
            if not sorted_rules:
                return "No rules failed — all checks passed."
            lines = [f"  - {rule}: {count} findings" for rule, count in sorted_rules[:10]]
            return "Most failed rules:\n" + "\n".join(lines)

        # Quality score
        if "score" in q_lower or "quality" in q_lower:
            if not score:
                return "No quality score available."
            return (
                f"Overall Quality Score: {score.overall:.1f}/100 ({score.traffic_light}).\n"
                f"  Completeness: {score.completeness:.1f}\n"
                f"  Accuracy: {score.accuracy:.1f}\n"
                f"  Consistency: {score.consistency:.1f}\n"
                f"  Validity: {score.validity:.1f}\n"
                f"  Uniqueness: {score.uniqueness:.1f}\n"
                f"  Integrity: {score.integrity:.1f}"
            )

        # Suggest automatic corrections
        if "suggest" in q_lower or "automatic" in q_lower or "auto" in q_lower:
            auto_fixes = []
            for f in findings:
                fix = f.get("suggested_fix", "")
                if any(
                    kw in fix.lower()
                    for kw in ["remove", "replace", "correct", "fill", "rename", "ensure"]
                ):
                    auto_fixes.append(f"  - {f.get('rule_name')}: {fix}")
            if not auto_fixes:
                return "No safe automatic corrections are available."
            return "Safe automatic corrections:\n" + "\n".join(auto_fixes[:10])

        # Default
        return (
            f"Validation status: {result.status.value}. "
            f"Quality score: {score.overall:.1f}/100 ({score.traffic_light}). "
            f"Errors: {result.total_errors}, Warnings: {result.total_warnings}. "
            f"Ask about: why validation failed, which records have errors, "
            f"what to correct, which rules failed most, or quality score."
        )
