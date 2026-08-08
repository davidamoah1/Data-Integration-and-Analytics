"""Data Workspace service — Excel-like spreadsheet experience with AI assistance."""

from __future__ import annotations

import ast
import operator
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import CalculatedColumn, DataWorkspace, WorkspaceVersion

# Safe operators for formula evaluation
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}

_SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "float": float,
    "int": int,
    "str": str,
}


class DataWorkspaceService:
    """Service for the Data Workspace studio."""

    def __init__(self, db: DbSession):
        self.db = db

    def create_workspace(
        self,
        org_id: int,
        user_id: int,
        name: str,
        dataset_id: int | None = None,
        description: str | None = None,
    ) -> DataWorkspace:
        ws = DataWorkspace(
            organization_id=org_id,
            dataset_id=dataset_id,
            name=name,
            description=description,
            created_by=user_id,
            columns_config=[],
            filters=[],
            sort_config=[],
            conditional_formatting=[],
            pivot_config=None,
        )
        self.db.add(ws)
        self.db.flush()
        self.db.commit()
        return ws

    def list_workspaces(self, org_id: int) -> list[DataWorkspace]:
        return (
            self.db.execute(
                select(DataWorkspace)
                .where(
                    DataWorkspace.organization_id == org_id, DataWorkspace.is_active == True  # noqa: E712
                )
                .order_by(DataWorkspace.updated_at.desc())
            )
            .scalars()
            .all()
        )

    def get_workspace(self, workspace_id: int, org_id: int) -> DataWorkspace | None:
        return self.db.execute(
            select(DataWorkspace).where(
                DataWorkspace.id == workspace_id,
                DataWorkspace.organization_id == org_id,
            )
        ).scalar_one_or_none()

    def update_config(
        self,
        workspace_id: int,
        org_id: int,
        columns_config: list | None = None,
        filters: list | None = None,
        sort_config: list | None = None,
        conditional_formatting: list | None = None,
        pivot_config: dict | None = None,
    ) -> DataWorkspace:
        ws = self.get_workspace(workspace_id, org_id)
        if not ws:
            raise ValueError("Workspace not found")

        if columns_config is not None:
            ws.columns_config = columns_config
        if filters is not None:
            ws.filters = filters
        if sort_config is not None:
            ws.sort_config = sort_config
        if conditional_formatting is not None:
            ws.conditional_formatting = conditional_formatting
        if pivot_config is not None:
            ws.pivot_config = pivot_config

        self.db.commit()
        return ws

    def create_version(
        self, workspace_id: int, user_id: int, change_description: str, changes: dict
    ) -> WorkspaceVersion:
        latest = self.db.execute(
            select(WorkspaceVersion)
            .where(WorkspaceVersion.workspace_id == workspace_id)
            .order_by(WorkspaceVersion.version_number.desc())
            .limit(1)
        ).scalar_one_or_none()
        next_version = (latest.version_number + 1) if latest else 1

        version = WorkspaceVersion(
            workspace_id=workspace_id,
            version_number=next_version,
            change_description=change_description,
            changes=changes,
            changed_by=user_id,
        )
        self.db.add(version)
        self.db.commit()
        return version

    def list_versions(self, workspace_id: int) -> list[WorkspaceVersion]:
        return (
            self.db.execute(
                select(WorkspaceVersion)
                .where(WorkspaceVersion.workspace_id == workspace_id)
                .order_by(WorkspaceVersion.version_number.desc())
            )
            .scalars()
            .all()
        )

    def add_calculated_column(
        self,
        workspace_id: int,
        column_name: str,
        formula: str,
        data_type: str = "float",
        ai_generated: bool = False,
        ai_explanation: str | None = None,
    ) -> CalculatedColumn:
        col = CalculatedColumn(
            workspace_id=workspace_id,
            column_name=column_name,
            formula=formula,
            data_type=data_type,
            ai_generated=ai_generated,
            ai_explanation=ai_explanation,
        )
        self.db.add(col)
        self.db.commit()
        return col

    def list_calculated_columns(self, workspace_id: int) -> list[CalculatedColumn]:
        return (
            self.db.execute(
                select(CalculatedColumn)
                .where(CalculatedColumn.workspace_id == workspace_id)
                .order_by(CalculatedColumn.created_at.desc())
            )
            .scalars()
            .all()
        )

    @staticmethod
    def evaluate_formula(formula: str, row: dict[str, Any]) -> Any:
        """Safely evaluate a formula against a row of data.

        Supports basic arithmetic: +, -, *, /, **, %
        Supports functions: abs, round, min, max, sum, len
        Column names are resolved from the row dict.
        """
        try:
            # Replace column names with values
            eval_formula = formula
            for col_name, value in row.items():
                if col_name in eval_formula:
                    # Use a safe placeholder
                    col_name.replace(" ", "_").replace("-", "_")
                    eval_formula = eval_formula.replace(
                        col_name, str(value if value is not None else 0)
                    )

            # Parse and evaluate safely
            tree = ast.parse(eval_formula, mode="eval")
            return DataWorkspaceService._eval_node(tree.body, {})
        except Exception:
            return None

    @staticmethod
    def _eval_node(node: ast.AST, context: dict) -> Any:
        """Recursively evaluate an AST node safely."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return context.get(node.id, 0)
        elif isinstance(node, ast.BinOp):
            left = DataWorkspaceService._eval_node(node.left, context)
            right = DataWorkspaceService._eval_node(node.right, context)
            op = _SAFE_OPS.get(type(node.op))
            if op:
                return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = DataWorkspaceService._eval_node(node.operand, context)
            op = _SAFE_OPS.get(type(node.op))
            if op:
                return op(operand)
        elif isinstance(node, ast.Call):
            func = _SAFE_FUNCS.get(node.func.id)
            if func:
                args = [DataWorkspaceService._eval_node(a, context) for a in node.args]
                return func(*args)
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    @staticmethod
    def ai_suggest_formula(description: str, available_columns: list[str]) -> dict:
        """AI-suggested formula based on natural language description.

        This is a rule-based heuristic that maps common descriptions to formulas.
        In production, this would call an LLM.
        """
        desc = description.lower().strip()
        suggestions = []

        # Profit margin
        if "profit margin" in desc or "margin" in desc:
            profit_cols = [c for c in available_columns if "profit" in c.lower()]
            revenue_cols = [
                c for c in available_columns if "revenue" in c.lower() or "sales" in c.lower()
            ]
            if profit_cols and revenue_cols:
                formula = f"{profit_cols[0]} / {revenue_cols[0]} * 100"
                suggestions.append(
                    {
                        "formula": formula,
                        "column_name": "profit_margin",
                        "data_type": "float",
                        "explanation": f"Calculates profit margin as ({profit_cols[0]} / {revenue_cols[0]}) × 100",
                    }
                )

        # Growth rate
        if "growth" in desc or "increase" in desc or "change" in desc:
            if len(available_columns) >= 2:
                suggestions.append(
                    {
                        "formula": f"({available_columns[1]} - {available_columns[0]}) / {available_columns[0]} * 100",
                        "column_name": "growth_rate",
                        "data_type": "float",
                        "explanation": "Calculates percentage change between two values",
                    }
                )

        # Total / sum
        if "total" in desc or "sum" in desc:
            num_cols = [
                c
                for c in available_columns
                if not c.isalpha()
                or c.lower() in ("revenue", "cost", "price", "amount", "quantity")
            ]
            if num_cols:
                suggestions.append(
                    {
                        "formula": f"sum({', '.join(num_cols[:3])})",
                        "column_name": "total",
                        "data_type": "float",
                        "explanation": f"Sums {', '.join(num_cols[:3])}",
                    }
                )

        # Ratio
        if ("ratio" in desc or "percentage of" in desc) and len(available_columns) >= 2:
            suggestions.append(
                {
                    "formula": f"{available_columns[0]} / {available_columns[1]}",
                    "column_name": "ratio",
                    "data_type": "float",
                    "explanation": f"Ratio of {available_columns[0]} to {available_columns[1]}",
                }
            )

        # Default: if no match, suggest a simple expression
        if not suggestions:
            suggestions.append(
                {
                    "formula": f"# Could not auto-detect. Available columns: {', '.join(available_columns[:5])}",
                    "column_name": "calculated",
                    "data_type": "float",
                    "explanation": "Please specify the formula manually or rephrase your request.",
                }
            )

        return {"suggestions": suggestions}
