"""AI Data Quality Engine â€” AI-powered data quality analysis.

Uses the existing ETL quality engine for detection, then applies AI
to generate recommendations, risk assessments, and fix suggestions.
"""

import json
import logging

from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from etl.connectors.connectors import get_connector
from etl.profiling import DataProfiler
from etl.quality import DataQualityEngine

logger = logging.getLogger(__name__)


class AIDataQualityEngine:
    """AI-enhanced data quality analysis."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)
        self.quality_engine = DataQualityEngine()
        self.profiler = DataProfiler()

    def analyze(
        self,
        source_type: str,
        source_config: dict,
        auto_fix: bool = False,
        user_id: int | None = None,
        permissions: list[str] | None = None,
    ) -> dict:
        """Analyze data quality with AI enhancement.

        Returns:
            Dict with quality_score, risk_level, issues_found,
            recommendations, fix_suggestions, auto_fixes_applied.
        """
        # Extract data
        connector = get_connector(source_type, source_config)
        with connector:
            df = connector.extract()

        # Run standard quality checks
        quality_result = self.quality_engine.run_checks(df, source_name=source_type)

        # Profile the data
        profile = self.profiler.profile(df, source_name=source_config.get("file_path", source_type))

        # Use AI to enhance the analysis
        quality_summary = json.dumps(
            {
                "overall_score": quality_result["overall_score"],
                "checks_passed": quality_result["checks_passed"],
                "checks_failed": quality_result["checks_failed"],
                "issues": [
                    {
                        "check": c["check"],
                        "passed": c["passed"],
                        "message": c["message"],
                        "severity": c["severity"],
                        "affected_rows": c["affected_rows"],
                    }
                    for c in quality_result["checks"]
                    if not c["passed"]
                ],
                "profile": {
                    "row_count": profile["row_count"],
                    "column_count": profile["column_count"],
                    "duplicate_rows": profile["duplicate_rows"],
                    "columns": [
                        {
                            "name": name,
                            "null_percentage": info.get("null_percentage", 0),
                            "unique_count": info.get("unique_count", 0),
                        }
                        for name, info in profile.get("columns", {}).items()
                    ],
                },
            },
            default=str,
        )

        result = self.gateway.chat(
            user_message=(
                f"Analyze this data quality report and provide AI-enhanced insights:\n{quality_summary}\n\n"
                f"Respond with JSON:\n"
                f'{{"risk_level": "low|medium|high|critical", '
                f'"issues_found": [{{"issue": "...", "severity": "...", "affected_columns": [...], '
                f'"description": "..."}}], '
                f'"recommendations": ["..."], '
                f'"fix_suggestions": [{{"action": "...", "column": "...", "description": "...", '
                f'"confidence": 0.0}}]}}'
            ),
            assistant_type="quality_copilot",
            user_id=user_id,
            permissions=permissions,
        )

        ai_analysis = self._extract_analysis(result["response"])

        # Apply auto-fixes if requested
        auto_fixes_applied = []
        if auto_fix:
            fixed_df = self.quality_engine.apply_fixes(df)
            fixes = []
            for check in self.quality_engine._checks:
                if check.fix_fn:
                    before_result = check.run(df)
                    after_result = check.run(fixed_df)
                    if not before_result["passed"] and after_result["passed"]:
                        fixes.append(
                            {
                                "check": check.name,
                                "description": f"Fixed: {before_result['message']}",
                            }
                        )
            auto_fixes_applied = fixes

        return {
            "quality_score": quality_result["overall_score"],
            "risk_level": ai_analysis.get("risk_level", "medium"),
            "issues_found": ai_analysis.get("issues_found", []),
            "recommendations": ai_analysis.get(
                "recommendations", quality_result.get("recommendations", [])
            ),
            "fix_suggestions": ai_analysis.get("fix_suggestions", []),
            "auto_fixes_applied": auto_fixes_applied if auto_fix else None,
        }

    def _extract_analysis(self, response: str) -> dict:
        """Extract AI analysis from response."""
        import re

        try:
            json_match = re.search(r'\{.*"risk_level".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            logger.debug("Failed to extract AI analysis JSON from response")
        return {}
