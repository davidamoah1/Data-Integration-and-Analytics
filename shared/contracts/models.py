from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

CONTRACT_VERSION = "1.0.0"


class LifecycleState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class PlatformContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    display_name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    version: str = Field(default=CONTRACT_VERSION, pattern=r"^\d+\.\d+\.\d+$")
    lifecycle: LifecycleState = LifecycleState.DRAFT
    configuration: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    extension_points: list[str] = Field(default_factory=list)

    @field_validator("permissions", "events", "extension_points")
    @classmethod
    def unique_values(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("values must be unique")
        return value


class MetadataContract(PlatformContract):
    owner: str | None = None
    sensitivity: str = "internal"
    tags: list[str] = Field(default_factory=list)
    lineage: list[str] = Field(default_factory=list)
    quality_rules: list[str] = Field(default_factory=list)


class SemanticContract(PlatformContract):
    vocabulary: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    taxonomy: list[str] = Field(default_factory=list)


class BusinessEntityContract(PlatformContract):
    attributes: dict[str, str] = Field(default_factory=dict)
    relationships: list[dict[str, str]] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    reports: list[str] = Field(default_factory=list)
    dashboard_widgets: list[str] = Field(default_factory=list)
    ai_context: dict[str, Any] = Field(default_factory=dict)


class IndustryPackContract(PlatformContract):
    industry: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    capabilities: list[str] = Field(default_factory=list)
    manifest_path: str = "manifest.yaml"


class KPIContract(PlatformContract):
    industry: str
    business_entity: str
    formula: str = Field(min_length=3)
    dimensions: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    thresholds: dict[str, float] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    visualizations: list[str] = Field(default_factory=list)
    ai_explanation: str = ""


class DashboardContract(PlatformContract):
    industry: str | None = None
    semantic_entities: list[str] = Field(default_factory=list)
    widgets: list[str] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)


class WidgetContract(PlatformContract):
    supported_kpis: list[str] = Field(default_factory=list)
    inputs: dict[str, str] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    theme_support: list[str] = Field(default_factory=lambda: ["light", "dark"])
    accessibility: dict[str, Any] = Field(default_factory=dict)


class ReportContract(PlatformContract):
    industry: str
    data_sources: list[str] = Field(default_factory=list)
    semantic_entities: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list)
    export_formats: list[str] = Field(default_factory=lambda: ["pdf", "csv"])


class ConnectorContract(PlatformContract):
    source_types: list[str]
    configuration_schema: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)


class ETLContract(PlatformContract):
    source_contracts: list[str] = Field(default_factory=list)
    transformations: list[str] = Field(default_factory=list)
    destination_contracts: list[str] = Field(default_factory=list)
    quality_rules: list[str] = Field(default_factory=list)


class WorkflowContract(PlatformContract):
    triggers: list[dict[str, Any]] = Field(default_factory=list)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    notifications: list[dict[str, Any]] = Field(default_factory=list)
    retry_rules: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = Field(default=None, ge=1)
    escalations: list[dict[str, Any]] = Field(default_factory=list)


class AIAgentContract(PlatformContract):
    role: str
    capabilities: list[str] = Field(default_factory=list)
    context_sources: list[str] = Field(default_factory=list)
    prompt_templates: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    safety_rules: list[str] = Field(default_factory=list)


class PluginContract(PlatformContract):
    plugin_type: str
    module_path: str
    dependencies: list[str] = Field(default_factory=list)
    compatible_platform_versions: list[str] = Field(default_factory=lambda: ["2.x"])


class NotificationContract(PlatformContract):
    channels: list[str] = Field(default_factory=list)
    recipients: list[str] = Field(default_factory=list)
    template: str = ""


class SearchContract(PlatformContract):
    resource_types: list[str] = Field(default_factory=list)
    searchable_fields: list[str] = Field(default_factory=list)
    ranking_strategy: str = "relevance"


class AuditContract(PlatformContract):
    actions: list[str] = Field(default_factory=list)
    retention_days: int = Field(default=365, ge=1)
    immutable: bool = True


class MonitoringContract(PlatformContract):
    metrics: list[str] = Field(default_factory=list)
    health_checks: list[str] = Field(default_factory=list)
    alert_rules: list[dict[str, Any]] = Field(default_factory=list)


class SecurityContract(PlatformContract):
    authentication_methods: list[str] = Field(default_factory=list)
    authorization_model: str = "rbac"
    data_classifications: list[str] = Field(default_factory=list)
    secret_requirements: list[str] = Field(default_factory=list)
