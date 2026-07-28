"""Workflow lineage graph builder.

Builds a chain of provenance edges during workflow execution. Each step that
touches a dataset becomes a vertex; data flowing between steps becomes edges.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class LineageBuilder:
    """Collect lineage edges for a single workflow execution."""

    def __init__(self, execution_id: str, organization_id: int | None = None):
        self.execution_id = execution_id
        self.organization_id = organization_id
        self.edges: list[dict] = []
        self._last_dataset_id: str | None = None

    def add_source(self, source_type: str, source_id: str, metadata: dict[str, Any] | None = None) -> None:
        self._last_dataset_id = source_id
        self.edges.append({
            "execution_id": self.execution_id,
            "organization_id": self.organization_id,
            "source_type": source_type,
            "source_id": source_id,
            "target_type": "execution",
            "target_id": self.execution_id,
            "transformation": "source",
            "meta": metadata or {},
            "created_at": datetime.now(timezone.utc),
        })

    def add_step(self, step_type: str, step_id: str, config: dict[str, Any] | None = None) -> None:
        if self._last_dataset_id:
            self.edges.append({
                "execution_id": self.execution_id,
                "organization_id": self.organization_id,
                "source_type": "execution_step",
                "source_id": step_id,
                "target_type": "dataset",
                "target_id": f"{self.execution_id}:{step_id}",
                "transformation": step_type,
                "meta": config or {},
                "created_at": datetime.now(timezone.utc),
            })
            self._last_dataset_id = f"{self.execution_id}:{step_id}"

    def add_target(self, target_type: str, target_id: str, metadata: dict[str, Any] | None = None) -> None:
        if self._last_dataset_id:
            self.edges.append({
                "execution_id": self.execution_id,
                "organization_id": self.organization_id,
                "source_type": "dataset",
                "source_id": self._last_dataset_id,
                "target_type": target_type,
                "target_id": target_id,
                "transformation": "export",
                "meta": metadata or {},
                "created_at": datetime.now(timezone.utc),
            })
