# AEDIP V3 Platform Kernel

## Architecture

AEDIP now has an additive five-layer architecture: **Layer 0** Platform Kernel, **Layer 1** Platform Services, **Layer 2** Extension Framework, **Layer 3** Industry Packs, and **Layer 4** existing applications. The kernel is in `shared.kernel` and consumes the V2 `shared.contracts` foundation. Existing modules continue to operate unchanged and can integrate through adapters.

## Kernel Components

`PlatformKernel` provides configuration, extension, plugin, event, command, query, feature-flag, version, permission, audit, capability, health, and marketplace registries. `start()` publishes `kernel.started`. The kernel is intentionally in-memory for the initial additive foundation; persistent tenancy and distributed transport are later phases.

## Platform Services

Existing authentication, organization, monitoring, scheduling, logging, search, configuration, secrets, and subscription modules remain authoritative. Kernel scoped registries provide the standardized discovery surface for configuration, feature flags, versions, permissions, and audit metadata, including organization-specific overrides.

## Extension and Plugin Framework

Extensions register using the V2 `PluginManifest`. Each extension declares identity, semantic version, author metadata, dependencies, capabilities, permissions, compatibility, configuration, health, licensing, and support metadata. Kernel registration installs the extension, publishes `plugin.installed`, registers capabilities, and records version and permissions. Plugin lifecycle remains install, upgrade, disable, remove, and list.

## Commands, Queries, and Events

`CommandBus` registers and dispatches state-changing commands, including future `dashboard.create`, `report.create`, `pipeline.run`, `dataset.import`, `ai_insight.generate`, `prediction.train`, `plugin.install`, and `industry_pack.install`. `QueryBus` registers CQRS-ready reads such as dashboard, metadata, semantic entities, KPIs, industry packs, and AI agents. `EventBus` uses V2 `DomainEvent` envelopes for the dataset, metadata, semantic, pipeline, dashboard, report, AI, workflow, identity, organization, plugin, and industry-pack event families.

## Capabilities and Feature Flags

The capability registry discovers components that support a declared capability such as `semantic`, `dashboard`, `healthcare`, `kpi`, `ai`, or `report`. Feature flags support global defaults and organization overrides. Subscription and beta/preview policies can be represented as feature names and later backed by persistent authorization policy.

## Industry Packs and Marketplace

Industry packs remain first-class `industry_pack` plugins. Discovery requires `manifest.yaml` and the V2 pack layout. The kernel marketplace records browseable manifest, author, license, support, and health metadata. The V3 target pack layout adds `ontology`, `knowledge_graph`, `entities`, `relationships`, `etl_templates`, `workflows`, `ai_agents`, and `tests`; existing V2 packs remain valid for backward compatibility.

## Ontology and Knowledge Graph

`OntologyEngine` adapts the existing semantic entity library into reusable ontology nodes exposing vocabulary, rules, KPIs, reports, dashboards, and AI context. It builds graph nodes and typed relationship edges using the existing `semantic.knowledge_graph` data structures. AI, dashboard, KPI, and report extensions can consume `graph_context()` rather than raw schemas.

## Security and Observability

The existing authentication/RBAC/audit/monitoring modules remain authoritative. Kernel registries centralize declared permissions, health checks, and audit metadata. Plugin isolation and ABAC are future enforcement layers, not implied by in-process registration.

## Integration Rules

- Do not replace existing APIs or registries.
- New modules register a V2 contract and V3 extension manifest.
- Commands and queries must have one handler per name.
- New domain events use `DomainEvent` with organization and actor context where available.
- New features must be gated through the kernel feature flag registry when released progressively.
