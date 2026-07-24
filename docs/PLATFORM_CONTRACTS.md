# AEDIP V2 Platform Contracts

## Foundation

All new AEDIP modules must validate their configuration against `shared.contracts` before registration. Every contract uses the `1.0.0` versioned `PlatformContract` base: identity, display name, description, configuration, permissions, events, extension points, lifecycle, and semantic version. Lifecycle states are `draft`, `active`, `disabled`, `deprecated`, and `removed`.

## Contract Catalog

| Contract | Purpose | Primary Responsibilities | Extension Point |
|---|---|---|---|
| Metadata | Govern technical and business data context | schema, owner, lineage, sensitivity, quality | catalog adapters |
| Semantic | Standardize business meaning | vocabulary, taxonomy, business rules | semantic libraries |
| Business Entity | Describe enterprise objects | attributes, relationships, KPIs, reports, AI context | entity packages |
| Industry Pack | Package vertical capability | manifest, capabilities, resources | installable packs |
| KPI | Govern decision measures | formula, dimensions, thresholds, alerts | KPI definitions |
| Dashboard | Compose semantic views | widgets, entities, filters | dashboard templates |
| Widget | Render accessible visualizations | inputs, outputs, themes, permissions | widget plugins |
| Report | Produce governed outputs | data sources, entities, templates, exports | report plugins |
| Connector | Integrate data sources | source types, configuration, capabilities | connector plugins |
| ETL | Govern data movement | sources, transforms, destinations, quality | ETL steps |
| Workflow | Automate operations | triggers, conditions, approvals, retries | workflow actions |
| AI Agent | Bound AI behavior | role, contexts, tools, safety, actions | agent plugins |
| Plugin | Install platform extensions | manifest, compatibility, dependencies | all plugin types |
| Notification | Deliver governed messages | channels, recipients, templates | notification adapters |
| Search | Index platform assets | resource types, fields, ranking | search providers |
| Audit | Record immutable activity | actions, retention, immutability | audit sinks |
| Monitoring | Measure platform health | metrics, health checks, alerts | metric exporters |
| Security | Enforce data protection | authentication, authorization, secrets | policy providers |

## API Contract

New APIs use `PageRequest`, `PageResponse`, and `APIError` from `shared.contracts.api`. Existing API responses remain unchanged for backward compatibility. New endpoints must expose OpenAPI schemas, accept bounded pagination, typed filtering, deterministic sorting, and machine-readable errors.

## Event Contract

`DomainEvent` carries an event ID, version, organization and actor scope, resource reference, timestamp, and payload. Use `EventBus` for in-process subscribers. Standard names include `dataset.uploaded`, `pipeline.completed`, `dashboard.generated`, `ai.insight_created`, `workflow.approved`, `metadata.updated`, and `semantic.mapping_changed`.

## Plugin Contract

`PluginManifest` validates plugin identity, version, type, entry point, permissions, dependencies, capabilities, and configuration. Supported types are `industry_pack`, `ai_agent`, `report`, `widget`, `connector`, `workflow`, `kpi`, `semantic_library`, and `validation_rule`. `PluginLifecycleRegistry` supports install, upgrade, disable, list, and removal without modifying core modules.

## Industry Pack Layout

Industry packs are discovered from `manifest.yaml` only when the following folders are present: `metadata`, `semantic`, `business_glossary`, `knowledge`, `kpis`, `dashboards`, `reports`, `widgets`, `rules`, `ai`, `sample_data`, `validation`, and `documentation`.

## Migration Rules

- Existing AEDIP models, routes, registries, and plugins are not replaced.
- New capability implementations should add an adapter that emits a contract-valid payload.
- Existing AI plugin records can be represented as `PluginManifest` records during phased migration.
- Existing semantic registries map naturally to `BusinessEntityContract`, `KPIContract`, `DashboardContract`, `WidgetContract`, and `ReportContract`.
- Persistent plugin lifecycle and event transport are intentionally deferred; the initial foundation is in-memory and additive.
