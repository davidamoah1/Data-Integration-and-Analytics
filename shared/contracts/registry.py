from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from shared.contracts.models import (
    AIAgentContract,
    AuditContract,
    BusinessEntityContract,
    ConnectorContract,
    DashboardContract,
    ETLContract,
    IndustryPackContract,
    KPIContract,
    MetadataContract,
    MonitoringContract,
    NotificationContract,
    PlatformContract,
    PluginContract,
    ReportContract,
    SearchContract,
    SecurityContract,
    SemanticContract,
    WidgetContract,
    WorkflowContract,
)

T = TypeVar("T", bound=PlatformContract)


@dataclass(frozen=True)
class ContractDefinition:
    name: str
    purpose: str
    responsibilities: tuple[str, ...]
    model: type[PlatformContract]


class ContractRegistry:
    def __init__(self, definitions: tuple[ContractDefinition, ...]):
        self._definitions = {definition.name: definition for definition in definitions}

    def names(self) -> list[str]:
        return sorted(self._definitions)

    def get(self, name: str) -> ContractDefinition:
        return self._definitions[name]

    def validate(self, name: str, payload: dict) -> PlatformContract:
        return self.get(name).model.model_validate(payload)


def _definition(name: str, purpose: str, model: type[PlatformContract]) -> ContractDefinition:
    return ContractDefinition(
        name=name,
        purpose=purpose,
        responsibilities=(
            "validate configuration",
            "enforce versioned lifecycle",
            "publish contract events",
        ),
        model=model,
    )


PLATFORM_CONTRACTS = ContractRegistry(
    (
        _definition(
            "metadata", "Govern dataset technical and business metadata.", MetadataContract
        ),
        _definition(
            "semantic", "Standardize business vocabulary, rules, and taxonomy.", SemanticContract
        ),
        _definition(
            "business_entity",
            "Describe enterprise business entities and relationships.",
            BusinessEntityContract,
        ),
        _definition(
            "industry_pack", "Package industry-specific platform extensions.", IndustryPackContract
        ),
        _definition("kpi", "Define governed measures and decision thresholds.", KPIContract),
        _definition("dashboard", "Describe semantic dashboard composition.", DashboardContract),
        _definition(
            "widget", "Define reusable accessible dashboard visualizations.", WidgetContract
        ),
        _definition(
            "report", "Define governed report data, templates, and exports.", ReportContract
        ),
        _definition(
            "connector", "Describe external data integration capabilities.", ConnectorContract
        ),
        _definition("etl", "Describe data movement and transformation pipelines.", ETLContract),
        _definition("workflow", "Describe automated operational orchestration.", WorkflowContract),
        _definition("ai_agent", "Define safe, permitted AI agent behavior.", AIAgentContract),
        _definition("plugin", "Define installable platform extensions.", PluginContract),
        _definition(
            "notification",
            "Define governed delivery of platform notifications.",
            NotificationContract,
        ),
        _definition("search", "Define searchable platform assets and ranking.", SearchContract),
        _definition("audit", "Define immutable audit behavior and retention.", AuditContract),
        _definition(
            "monitoring", "Define metrics, health checks, and alerting.", MonitoringContract
        ),
        _definition(
            "security", "Define platform security and data protection controls.", SecurityContract
        ),
    )
)
