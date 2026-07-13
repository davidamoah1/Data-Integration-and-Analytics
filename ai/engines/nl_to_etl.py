"""Natural Language to ETL Engine — translates instructions into ETL pipeline steps.

Translates natural language instructions like:
  "Import the Excel file, remove duplicates, convert dates, load into Sales"
into concrete ETL pipeline step configurations.
"""

import json
import re
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway


class NLToETLEngine:
    """Translates natural language instructions to ETL pipeline configurations."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def generate_pipeline(self, instruction: str, file_path: Optional[str] = None,
                          target_table: Optional[str] = None,
                          user_id: Optional[int] = None) -> dict:
        """Generate ETL pipeline steps from natural language instruction.

        Returns:
            Dict with pipeline_steps, explanation, estimated_duration.
        """
        context = {}
        if file_path:
            context["file_path"] = file_path
        if target_table:
            context["target_table"] = target_table

        result = self.gateway.chat(
            user_message=(
                f"Convert this instruction into ETL pipeline steps:\n{instruction}\n\n"
                f"Respond with JSON:\n"
                f'{{"pipeline_steps": [{{"type": "extract|transform|load", "config": {{...}}}}], '
                f'"explanation": "...", "estimated_duration": "..."}}\n'
                f"Available step types: extract, clean, transform, profile, quality_check, load\n"
                f"Available connectors: csv, excel, json, xml, mysql, api\n"
                f"Available transformations: rename, drop, filter, fill, convert, calculate, "
                f"split, merge, sort, deduplicate, standardize\n"
                f"Available load modes: insert, update, upsert, incremental, full, batch"
            ),
            assistant_type="etl_copilot",
            user_id=user_id,
            context=context,
        )

        steps, explanation, duration = self._extract_pipeline(result["response"])

        return {
            "pipeline_steps": steps,
            "explanation": explanation,
            "estimated_duration": duration,
        }

    def _extract_pipeline(self, response: str) -> tuple[list[dict], str, Optional[str]]:
        """Extract pipeline steps from AI response."""
        # Try JSON extraction
        try:
            json_match = re.search(r'\{.*"pipeline_steps".*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                steps = data.get("pipeline_steps", [])
                explanation = data.get("explanation", "")
                duration = data.get("estimated_duration")
                if isinstance(steps, list):
                    return steps, explanation, duration
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fall back to code block extraction
        code_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            try:
                data = json.loads(code_match.group(1))
                if "pipeline_steps" in data:
                    return data["pipeline_steps"], data.get("explanation", ""), data.get("estimated_duration")
            except json.JSONDecodeError:
                pass

        # If no structured data found, return the raw response as explanation
        return [], response, None
