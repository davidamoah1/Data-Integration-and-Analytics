"""Natural Language to SQL Engine â€” translates questions into safe SQL.

Features:
- Translates natural language to SQL queries
- Validates SQL (SELECT only, no destructive operations)
- Explains generated SQL in plain language
- Estimates result row count
- Warns about performance issues
"""

import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.security import AISecurityLayer

# SQL keywords that are NOT allowed
FORBIDDEN_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "MERGE",
    "REPLACE",
]

# Allowed SQL keywords
ALLOWED_KEYWORDS = [
    "SELECT",
    "FROM",
    "WHERE",
    "GROUP BY",
    "ORDER BY",
    "LIMIT",
    "OFFSET",
    "JOIN",
    "LEFT JOIN",
    "RIGHT JOIN",
    "INNER JOIN",
    "OUTER JOIN",
    "HAVING",
    "UNION",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "DISTINCT",
    "AS",
    "AND",
    "OR",
    "NOT",
    "IN",
    "LIKE",
    "BETWEEN",
    "IS NULL",
    "IS NOT NULL",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
]


class NLToSQLEngine:
    """Translates natural language to safe SQL queries."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)
        self.security = AISecurityLayer(db)

    def generate_sql(
        self,
        question: str,
        table_name: str | None = None,
        schema_hint: dict | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Generate SQL from a natural language question.

        Returns:
            Dict with sql, explanation, is_safe, warnings.
        """
        # Build context for the AI
        context = {}
        if table_name:
            context["target_table"] = table_name
        if schema_hint:
            context["schema_hint"] = schema_hint

        # Use the SQL copilot to generate SQL
        result = self.gateway.chat(
            user_message=f"Generate a SQL query for this question: {question}\n"
            f'Respond with JSON: {{"sql": "...", "explanation": "..."}}',
            assistant_type="sql_copilot",
            user_id=user_id,
            context=context,
        )

        # Extract SQL from the response
        sql, explanation = self._extract_sql(result["response"])

        # Validate the SQL
        is_safe, warnings = self._validate_sql(sql)

        # Estimate row count if safe
        estimated_rows = None
        if is_safe and sql:
            estimated_rows = self._estimate_rows(sql)

        return {
            "sql": sql,
            "explanation": explanation,
            "is_safe": is_safe,
            "warnings": warnings,
            "estimated_rows": estimated_rows,
        }

    def _extract_sql(self, response: str) -> tuple[str, str]:
        """Extract SQL and explanation from AI response."""
        # Try to parse as JSON first
        try:
            # Find JSON in the response
            json_match = re.search(r'\{[^{}]*"sql"[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("sql", "").strip(), data.get("explanation", "")
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fall back to extracting SQL from code blocks
        sql_match = re.search(r"```sql\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
            # Remove the SQL block from response to get explanation
            explanation = re.sub(r"```sql.*?```", "", response, flags=re.DOTALL).strip()
            return sql, explanation

        # Try to find SELECT statement directly
        select_match = re.search(r"(SELECT\s+.*?)(?:;|$)", response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip(), response

        return "", response

    def _validate_sql(self, sql: str) -> tuple[bool, list[str]]:
        """Validate that SQL is safe (SELECT only)."""
        warnings = []
        if not sql:
            return False, ["Empty SQL query"]

        sql_upper = sql.upper().strip()

        # Check for forbidden keywords first
        for keyword in FORBIDDEN_KEYWORDS:
            if re.search(r"\b" + keyword + r"\b", sql_upper):
                warnings.append(f"Forbidden keyword detected: {keyword}")
                return False, warnings

        # Must start with SELECT or WITH
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            warnings.append("Query must start with SELECT or WITH")
            return False, warnings

        # Check for semicolons (could indicate multiple statements)
        if ";" in sql.rstrip(";"):
            warnings.append("Multiple statements detected (semicolons not allowed)")
            return False, warnings

        # Check for missing LIMIT on potentially large queries
        if "LIMIT" not in sql_upper and ("COUNT" not in sql_upper or "GROUP BY" in sql_upper):
            warnings.append("Consider adding LIMIT clause for large result sets")

        # Check for SELECT *
        if "SELECT *" in sql_upper:
            warnings.append(
                "SELECT * may return unnecessary columns â€” specify columns explicitly"
            )

        return len(warnings) == 0 or all("Consider" in w or "may" in w for w in warnings), warnings

    def _estimate_rows(self, sql: str) -> int | None:
        """Estimate the number of rows the query will return."""
        try:
            # Wrap in a COUNT subquery
            count_sql = f"SELECT COUNT(*) FROM ({sql}) AS _estimate"  # nosec B608 â€” sql is validated by _validate_sql() before reaching here
            result = self.db.execute(text(count_sql))  # nosec B608
            row = result.fetchone()
            return row[0] if row else None
        except Exception:
            return None

    def execute_sql(self, sql: str, limit: int = 100) -> dict:
        """Execute a validated SQL query safely.

        Returns:
            Dict with columns, rows, and total_count.
        """
        # Validate first
        is_safe, warnings = self._validate_sql(sql)
        if not is_safe:
            return {
                "columns": [],
                "rows": [],
                "total_count": 0,
                "error": "Unsafe SQL: " + "; ".join(warnings),
            }

        # Add LIMIT if not present
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        try:
            result = self.db.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
            return {
                "columns": columns,
                "rows": rows[:limit],
                "total_count": len(rows),
            }
        except Exception as e:
            return {
                "columns": [],
                "rows": [],
                "total_count": 0,
                "error": str(e),
            }
