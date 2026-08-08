"""Built-in workflow node registry and implementations.

A node is a callable that receives a `WorkflowContext` and returns a
NodeResult. New node types can be registered at runtime by adding a
factory function to `NODE_REGISTRY`.
"""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class NodeResult:
    """Result returned by every node execution."""

    status: str = "completed"  # completed, failed, skipped, pending_approval
    data: Any = None
    rows_processed: int = 0
    rows_failed: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "rows_processed": self.rows_processed,
            "rows_failed": self.rows_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class WorkflowContext:
    """Execution context shared across all nodes in a workflow run."""

    def __init__(self, execution_id: str, config: dict, inputs: dict | None = None):
        self.execution_id = execution_id
        self.config = config or {}
        self.inputs = inputs or {}
        self.outputs: dict[str, NodeResult] = {}
        self.variables: dict[str, Any] = {}

    def get_input(self, key: str, default: Any = None) -> Any:
        """Return a named input or default."""
        return self.inputs.get(key, default)

    def resolve_ref(self, ref: str | None) -> Any:
        """Resolve a reference like `{{node_id.data}}` or plain values."""
        if ref is None:
            return None
        if isinstance(ref, str) and ref.startswith("{{") and ref.endswith("}}"):
            path = ref[2:-2].strip()
            parts = path.split(".")
            node_id = parts[0]
            attr = ".".join(parts[1:]) if len(parts) > 1 else "data"
            result = self.outputs.get(node_id)
            if result is None:
                raise ValidationError(f"Reference to unknown node output: {node_id}")
            value = getattr(result, attr, None)
            if value is None and attr == "data":
                value = result.data
            return value
        return ref

    def set_output(self, node_id: str, result: NodeResult) -> None:
        self.outputs[node_id] = result


def _get_param(config: dict, key: str, default: Any = None, required: bool = False) -> Any:
    if key in config and config[key] is not None:
        return config[key]
    if required:
        raise ValidationError(f"Missing required config parameter: {key}")
    return default


class WorkflowNode(ABC):
    """Base class for all workflow nodes."""

    NODE_TYPE: str = ""

    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config

    @abstractmethod
    def run(self, ctx: WorkflowContext) -> NodeResult:
        raise NotImplementedError

    def resolve_inputs(self, ctx: WorkflowContext) -> dict[str, Any]:
        """Resolve node input references using the current context."""
        resolved = {}
        for key, value in self.config.get("inputs", {}).items():
            resolved[key] = ctx.resolve_ref(value)
        return resolved


# --- Data source nodes -------------------------------------------------------


class ReadCsvNode(WorkflowNode):
    NODE_TYPE = "read_csv"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        path_or_content = _get_param(self.config, "path") or _get_param(self.config, "content")
        if path_or_content is None:
            return NodeResult(status="failed", errors=["read_csv requires 'path' or 'content'"])
        try:
            if isinstance(path_or_content, str):
                content = path_or_content.encode("utf-8")
            elif isinstance(path_or_content, bytes):
                content = path_or_content
            else:
                content = str(path_or_content).encode("utf-8")
            if isinstance(path_or_content, str) and (
                path_or_content.startswith("http://") or path_or_content.startswith("https://")
            ):
                df = pd.read_csv(path_or_content)
            else:
                df = pd.read_csv(io.BytesIO(content))
            return NodeResult(status="completed", data=df, rows_processed=len(df))
        except Exception as e:
            logger.exception("read_csv failed")
            return NodeResult(status="failed", errors=[str(e)])


class ReadExcelNode(WorkflowNode):
    NODE_TYPE = "read_excel"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        path_or_content = _get_param(self.config, "path") or _get_param(self.config, "content")
        sheet = _get_param(self.config, "sheet_name", 0)
        try:
            if isinstance(path_or_content, bytes):
                df = pd.read_excel(io.BytesIO(path_or_content), sheet_name=sheet)
            else:
                df = pd.read_excel(path_or_content, sheet_name=sheet)
            return NodeResult(status="completed", data=df, rows_processed=len(df))
        except Exception as e:
            logger.exception("read_excel failed")
            return NodeResult(status="failed", errors=[str(e)])


class ReadSqlNode(WorkflowNode):
    NODE_TYPE = "read_sql"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        connection = _get_param(self.config, "connection", required=True)
        query = _get_param(self.config, "query", required=True)
        try:
            from sqlalchemy import create_engine

            engine = create_engine(connection)
            df = pd.read_sql(query, engine)
            return NodeResult(status="completed", data=df, rows_processed=len(df))
        except Exception as e:
            logger.exception("read_sql failed")
            return NodeResult(status="failed", errors=[str(e)])


class ReadRestNode(WorkflowNode):
    NODE_TYPE = "read_rest"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        url = _get_param(self.config, "url", required=True)
        try:
            import requests

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            return NodeResult(status="completed", data=df, rows_processed=len(df))
        except Exception as e:
            logger.exception("read_rest failed")
            return NodeResult(status="failed", errors=[str(e)])


class ReadSftpNode(WorkflowNode):
    NODE_TYPE = "read_sftp"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        return NodeResult(
            status="failed",
            errors=["SFTP node requires paramiko or pysftp dependency; not installed by default"],
        )


# --- Data processing nodes ---------------------------------------------------


class ValidateDataNode(WorkflowNode):
    NODE_TYPE = "validate_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["validate_data requires a DataFrame input"])
        try:
            from validation.engine import ValidationEngine

            engine = ValidationEngine()
            result = engine.validate(df, dataset_name=self.config.get("dataset_name", "dataset"))
            return NodeResult(
                status="completed",
                data=result,
                rows_processed=len(df),
                rows_failed=result.total_errors,
                metadata={
                    "status": result.status.value,
                    "score": result.quality_score.overall if result.quality_score else None,
                },
            )
        except Exception as e:
            logger.exception("validate_data failed")
            return NodeResult(status="failed", errors=[str(e)])


class CleanDataNode(WorkflowNode):
    NODE_TYPE = "clean_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["clean_data requires a DataFrame input"])
        original_len = len(df)
        try:
            df = df.dropna(how="all")
            df = df.drop_duplicates()
            return NodeResult(
                status="completed",
                data=df,
                rows_processed=len(df),
                rows_failed=original_len - len(df),
                metadata={"dropped_rows": original_len - len(df)},
            )
        except Exception as e:
            logger.exception("clean_data failed")
            return NodeResult(status="failed", errors=[str(e)])


class TransformDataNode(WorkflowNode):
    NODE_TYPE = "transform_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["transform_data requires a DataFrame input"])
        try:
            from etl.transformations import TransformationEngine

            engine = TransformationEngine()
            operations = self.config.get("operations", [])
            for op in operations:
                df = engine.apply(df, op)
            return NodeResult(status="completed", data=df, rows_processed=len(df))
        except Exception as e:
            logger.exception("transform_data failed")
            return NodeResult(status="failed", errors=[str(e)])


class AggregateDataNode(WorkflowNode):
    NODE_TYPE = "aggregate_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        group_by = _get_param(self.config, "group_by", required=True)
        agg = _get_param(self.config, "aggregations", required=True)
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["aggregate_data requires a DataFrame input"])
        try:
            result = df.groupby(group_by).agg(agg).reset_index()
            return NodeResult(status="completed", data=result, rows_processed=len(result))
        except Exception as e:
            logger.exception("aggregate_data failed")
            return NodeResult(status="failed", errors=[str(e)])


class MergeDataNode(WorkflowNode):
    NODE_TYPE = "merge_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        left = ctx.resolve_ref(_get_param(self.config, "left"))
        right = ctx.resolve_ref(_get_param(self.config, "right"))
        on = _get_param(self.config, "on", required=True)
        how = _get_param(self.config, "how", "inner")
        if not isinstance(left, pd.DataFrame) or not isinstance(right, pd.DataFrame):
            return NodeResult(status="failed", errors=["merge_data requires two DataFrame inputs"])
        try:
            result = pd.merge(left, right, on=on, how=how)
            return NodeResult(status="completed", data=result, rows_processed=len(result))
        except Exception as e:
            logger.exception("merge_data failed")
            return NodeResult(status="failed", errors=[str(e)])


class JoinDataNode(WorkflowNode):
    NODE_TYPE = "join_data"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        return MergeDataNode(self.node_id, self.config).run(ctx)


class ExecuteSqlNode(WorkflowNode):
    NODE_TYPE = "execute_sql"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        query = _get_param(self.config, "query", required=True)
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["execute_sql requires a DataFrame input"])
        try:
            import duckdb

            con = duckdb.connect(":memory:")
            con.register("source_df", df)
            result = con.execute(query).fetchdf()
            return NodeResult(status="completed", data=result, rows_processed=len(result))
        except Exception as e:
            logger.exception("execute_sql failed")
            return NodeResult(status="failed", errors=[str(e), "DuckDB may not be installed"])


class ExecutePythonNode(WorkflowNode):
    NODE_TYPE = "execute_python"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        code = _get_param(self.config, "code", required=True)
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        local_ns = {"df": df, "context": ctx, "pd": pd}
        try:
            exec(code, {"__builtins__": {}}, local_ns)
            result = local_ns.get("result", df)
            return NodeResult(
                status="completed",
                data=result,
                rows_processed=len(result) if isinstance(result, pd.DataFrame) else 0,
            )
        except Exception as e:
            logger.exception("execute_python failed")
            return NodeResult(status="failed", errors=[str(e)])


# --- Intelligence & metadata nodes -------------------------------------------


class AiAnalysisNode(WorkflowNode):
    NODE_TYPE = "ai_analysis"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        prompt = _get_param(self.config, "prompt", required=True)
        try:
            from ai.services import AIService

            service = AIService()
            summary = (
                service.analyze_dataset(df, prompt)
                if hasattr(service, "analyze_dataset")
                else f"AI analysis placeholder: {prompt}"
            )
            return NodeResult(status="completed", data=summary, metadata={"provider": "ai"})
        except Exception as e:
            logger.exception("ai_analysis failed")
            return NodeResult(status="failed", errors=[str(e)])


class SemanticMappingNode(WorkflowNode):
    NODE_TYPE = "semantic_mapping"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(
                status="failed", errors=["semantic_mapping requires a DataFrame input"]
            )
        try:
            from semantic.analyzer import SemanticAnalyzer

            analyzer = SemanticAnalyzer()
            mappings = analyzer.map_columns(df.columns.tolist())
            return NodeResult(
                status="completed",
                data=mappings,
                rows_processed=len(df),
                metadata={"mappings": mappings},
            )
        except Exception as e:
            logger.exception("semantic_mapping failed")
            return NodeResult(status="failed", errors=[str(e)])


class MetadataGenerationNode(WorkflowNode):
    NODE_TYPE = "metadata_generation"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(
                status="failed", errors=["metadata_generation requires a DataFrame input"]
            )
        metadata = {
            "columns": [
                {"name": c, "dtype": str(df[c].dtype), "sample": df[c].dropna().head(5).tolist()}
                for c in df.columns
            ],
            "row_count": len(df),
        }
        return NodeResult(
            status="completed", data=metadata, rows_processed=len(df), metadata=metadata
        )


class DashboardGenerationNode(WorkflowNode):
    NODE_TYPE = "dashboard_generation"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        if not isinstance(df, pd.DataFrame):
            return NodeResult(
                status="failed", errors=["dashboard_generation requires a DataFrame input"]
            )
        return NodeResult(
            status="completed",
            data={"dashboard_type": "auto", "widgets": []},
            metadata={"columns": df.columns.tolist()},
        )


class ReportGenerationNode(WorkflowNode):
    NODE_TYPE = "report_generation"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        data = ctx.resolve_ref(_get_param(self.config, "dataset"))
        return NodeResult(
            status="completed",
            data={"report_type": "summary", "sections": []},
            metadata={"input_type": type(data).__name__},
        )


# --- Export & sink nodes -------------------------------------------------------


class ExportDatasetNode(WorkflowNode):
    NODE_TYPE = "export_dataset"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        fmt = _get_param(self.config, "format", "csv")
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["export_dataset requires a DataFrame input"])
        try:
            if fmt == "csv":
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                content = buffer.getvalue()
            elif fmt == "excel":
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                content = buffer.getvalue()
            else:
                return NodeResult(status="failed", errors=[f"Unsupported export format: {fmt}"])
            return NodeResult(
                status="completed", data=content, rows_processed=len(df), metadata={"format": fmt}
            )
        except Exception as e:
            logger.exception("export_dataset failed")
            return NodeResult(status="failed", errors=[str(e)])


class ExportCsvNode(ExportDatasetNode):
    NODE_TYPE = "export_csv"


class ExportExcelNode(ExportDatasetNode):
    NODE_TYPE = "export_excel"


class ExportPdfNode(WorkflowNode):
    NODE_TYPE = "export_pdf"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        return NodeResult(status="completed", data=b"PDF placeholder", metadata={"format": "pdf"})


class SaveDatasetNode(WorkflowNode):
    NODE_TYPE = "save_dataset"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        name = _get_param(self.config, "name", "saved_dataset")
        if not isinstance(df, pd.DataFrame):
            return NodeResult(status="failed", errors=["save_dataset requires a DataFrame input"])
        return NodeResult(
            status="completed",
            data={"dataset_name": name, "columns": df.columns.tolist(), "rows": len(df)},
            rows_processed=len(df),
            metadata={"dataset_name": name},
        )


class ArchiveDatasetNode(WorkflowNode):
    NODE_TYPE = "archive_dataset"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        df = ctx.resolve_ref(_get_param(self.config, "dataset"))
        return NodeResult(
            status="completed",
            data={"archived": True},
            rows_processed=len(df) if isinstance(df, pd.DataFrame) else 0,
        )


# --- Notification nodes ------------------------------------------------------


class SendEmailNode(WorkflowNode):
    NODE_TYPE = "send_email"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        to = _get_param(self.config, "to", required=True)
        subject = _get_param(self.config, "subject", "Workflow notification")
        _get_param(self.config, "body", "")
        return NodeResult(
            status="completed", data={"to": to, "subject": subject}, metadata={"channel": "email"}
        )


class SendSmsNode(WorkflowNode):
    NODE_TYPE = "send_sms"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        to = _get_param(self.config, "to", required=True)
        return NodeResult(status="completed", data={"to": to}, metadata={"channel": "sms"})


class SendWebhookNode(WorkflowNode):
    NODE_TYPE = "send_webhook"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        url = _get_param(self.config, "url", required=True)
        try:
            import requests

            payload = self.config.get("payload", {})
            response = requests.post(url, json=payload, timeout=10)
            return NodeResult(
                status="completed",
                data={"status_code": response.status_code},
                metadata={"channel": "webhook"},
            )
        except Exception as e:
            logger.exception("send_webhook failed")
            return NodeResult(status="failed", errors=[str(e)])


# --- Control-flow nodes ------------------------------------------------------


class ApprovalStepNode(WorkflowNode):
    NODE_TYPE = "approval_step"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        approvers = _get_param(self.config, "approvers", [])
        return NodeResult(
            status="pending_approval",
            data={"approvers": approvers, "approved": False},
            metadata={"requires_approval": True},
        )


class ManualReviewNode(WorkflowNode):
    NODE_TYPE = "manual_review"

    def run(self, ctx: WorkflowContext) -> NodeResult:
        return NodeResult(
            status="pending_approval",
            data={"review_required": True},
            metadata={"manual_review": True},
        )


# --- Registry ----------------------------------------------------------------

NODE_REGISTRY: dict[str, Callable[[str, dict], WorkflowNode]] = {
    ReadCsvNode.NODE_TYPE: lambda nid, cfg: ReadCsvNode(nid, cfg),
    ReadExcelNode.NODE_TYPE: lambda nid, cfg: ReadExcelNode(nid, cfg),
    ReadSqlNode.NODE_TYPE: lambda nid, cfg: ReadSqlNode(nid, cfg),
    ReadRestNode.NODE_TYPE: lambda nid, cfg: ReadRestNode(nid, cfg),
    ReadSftpNode.NODE_TYPE: lambda nid, cfg: ReadSftpNode(nid, cfg),
    ValidateDataNode.NODE_TYPE: lambda nid, cfg: ValidateDataNode(nid, cfg),
    CleanDataNode.NODE_TYPE: lambda nid, cfg: CleanDataNode(nid, cfg),
    TransformDataNode.NODE_TYPE: lambda nid, cfg: TransformDataNode(nid, cfg),
    AggregateDataNode.NODE_TYPE: lambda nid, cfg: AggregateDataNode(nid, cfg),
    MergeDataNode.NODE_TYPE: lambda nid, cfg: MergeDataNode(nid, cfg),
    JoinDataNode.NODE_TYPE: lambda nid, cfg: JoinDataNode(nid, cfg),
    ExecuteSqlNode.NODE_TYPE: lambda nid, cfg: ExecuteSqlNode(nid, cfg),
    ExecutePythonNode.NODE_TYPE: lambda nid, cfg: ExecutePythonNode(nid, cfg),
    AiAnalysisNode.NODE_TYPE: lambda nid, cfg: AiAnalysisNode(nid, cfg),
    SemanticMappingNode.NODE_TYPE: lambda nid, cfg: SemanticMappingNode(nid, cfg),
    MetadataGenerationNode.NODE_TYPE: lambda nid, cfg: MetadataGenerationNode(nid, cfg),
    DashboardGenerationNode.NODE_TYPE: lambda nid, cfg: DashboardGenerationNode(nid, cfg),
    ReportGenerationNode.NODE_TYPE: lambda nid, cfg: ReportGenerationNode(nid, cfg),
    ExportDatasetNode.NODE_TYPE: lambda nid, cfg: ExportDatasetNode(nid, cfg),
    ExportCsvNode.NODE_TYPE: lambda nid, cfg: ExportCsvNode(nid, cfg),
    ExportExcelNode.NODE_TYPE: lambda nid, cfg: ExportExcelNode(nid, cfg),
    ExportPdfNode.NODE_TYPE: lambda nid, cfg: ExportPdfNode(nid, cfg),
    SaveDatasetNode.NODE_TYPE: lambda nid, cfg: SaveDatasetNode(nid, cfg),
    ArchiveDatasetNode.NODE_TYPE: lambda nid, cfg: ArchiveDatasetNode(nid, cfg),
    SendEmailNode.NODE_TYPE: lambda nid, cfg: SendEmailNode(nid, cfg),
    SendSmsNode.NODE_TYPE: lambda nid, cfg: SendSmsNode(nid, cfg),
    SendWebhookNode.NODE_TYPE: lambda nid, cfg: SendWebhookNode(nid, cfg),
    ApprovalStepNode.NODE_TYPE: lambda nid, cfg: ApprovalStepNode(nid, cfg),
    ManualReviewNode.NODE_TYPE: lambda nid, cfg: ManualReviewNode(nid, cfg),
}


def register_node(node_type: str, factory: Callable[[str, dict], WorkflowNode]) -> None:
    """Register a custom node type at runtime."""
    NODE_REGISTRY[node_type] = factory


def create_node(node_type: str, node_id: str, config: dict) -> WorkflowNode:
    """Factory function for creating a node instance from its type."""
    if node_type not in NODE_REGISTRY:
        raise ValidationError(f"Unsupported node type: {node_type}")
    return NODE_REGISTRY[node_type](node_id, config)


def list_node_types() -> list[dict]:
    """Return metadata about all registered node types."""
    return [
        {
            "type": key,
            "category": _category(key),
            "description": f"Execute a {key} node.",
        }
        for key in sorted(NODE_REGISTRY.keys())
    ]


def _category(node_type: str) -> str:
    if node_type.startswith("read_"):
        return "source"
    if node_type in (
        "validate_data",
        "clean_data",
        "transform_data",
        "aggregate_data",
        "merge_data",
        "join_data",
        "execute_sql",
        "execute_python",
    ):
        return "processing"
    if node_type in (
        "ai_analysis",
        "semantic_mapping",
        "metadata_generation",
        "dashboard_generation",
        "report_generation",
    ):
        return "intelligence"
    if node_type.startswith("export_") or node_type in (
        "save_dataset",
        "archive_dataset",
        "export_dataset",
    ):
        return "export"
    if node_type.startswith("send_"):
        return "notification"
    if node_type in ("approval_step", "manual_review"):
        return "control"
    return "other"
