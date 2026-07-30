# Cross-Reference Map

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Enterprise Architecture Board

---

## Purpose

Map of all cross-references between documentation files.

## Scope

Every document and its links to related documents.

## Audience

All contributors and documentation maintainers.

---

## 1. Architecture

| Document | References |
|----------|-----------|
| [architecture/overview.md](architecture/overview.md) | system-design.md, component-diagram.md, deployment-architecture.md, technology-stack.md, adr/ |
| [architecture/system-design.md](architecture/system-design.md) | overview.md, component-diagram.md, data-flow.md, technology-stack.md |
| [architecture/component-diagram.md](architecture/component-diagram.md) | system-design.md, overview.md, data-flow.md, sequence-diagrams.md |
| [architecture/deployment-architecture.md](architecture/deployment-architecture.md) | deployment/local-development.md, deployment/vercel.md, deployment/production.md, deployment/environments.md |
| [architecture/data-flow.md](architecture/data-flow.md) | sequence-diagrams.md, system-design.md, workflows/ |
| [architecture/sequence-diagrams.md](architecture/sequence-diagrams.md) | data-flow.md, system-design.md, backend/authentication.md |
| [architecture/integrations.md](architecture/integrations.md) | integrations/, adr/ADR-0012, technology-stack.md |
| [architecture/scalability.md](architecture/scalability.md) | deployment-architecture.md, database/optimization.md, backend/caching.md, testing/performance-tests.md |
| [architecture/technology-stack.md](architecture/technology-stack.md) | system-design.md, overview.md, deployment/ |
| [architecture/adr/README.md](architecture/adr/README.md) | overview.md, governance/README.md |

## 2. Governance

| Document | References |
|----------|-----------|
| [governance/roles.md](governance/roles.md) | permission-matrix.md, authorization.md, architecture/adr/README.md |
| [governance/permission-matrix.md](governance/permission-matrix.md) | roles.md, authorization.md, permission-matrix.json |
| [governance/authorization.md](governance/authorization.md) | roles.md, permission-matrix.md, api-authorization-matrix.md, security-model.md, architecture/adr/README.md |
| [governance/audit-logging.md](governance/audit-logging.md) | security-model.md, compliance-notes.md, architecture/adr/README.md, backend/logging.md |
| [governance/organization-model.md](governance/organization-model.md) | workspace-model.md, authorization.md, security-model.md, architecture/adr/README.md |
| [governance/workspace-model.md](governance/workspace-model.md) | organization-model.md, architecture/adr/README.md, workflows/onboarding.md |
| [governance/security-model.md](governance/security-model.md) | authorization.md, audit-logging.md, compliance-notes.md, architecture/adr/README.md |
| [governance/compliance-notes.md](governance/compliance-notes.md) | security-model.md, audit-logging.md, operations/incident-response.md, operations/disaster-recovery.md |
| [governance/api-authorization-matrix.md](governance/api-authorization-matrix.md) | authorization.md, backend/endpoints.md, permission-matrix.md |
| [governance/frontend-navigation-matrix.md](governance/frontend-navigation-matrix.md) | frontend/navigation.md, frontend/routing.md, roles.md |
| [governance/user-journeys.md](governance/user-journeys.md) | roles.md, workflows/onboarding.md, user-guides/ |

## 3. Database

| Document | References |
|----------|-----------|
| [database/schema.md](database/schema.md) | entity-relationship.md, migrations.md, indexing.md, governance/organization-model.md |
| [database/entity-relationship.md](database/entity-relationship.md) | schema.md, indexing.md, governance/organization-model.md |
| [database/migrations.md](database/migrations.md) | schema.md, architecture/system-design.md, deployment/production.md |
| [database/indexing.md](database/indexing.md) | schema.md, optimization.md, entity-relationship.md |
| [database/backup-recovery.md](database/backup-recovery.md) | operations/backups.md, operations/disaster-recovery.md, deployment/production.md |
| [database/optimization.md](database/optimization.md) | indexing.md, schema.md, architecture/scalability.md, backend/caching.md |

## 4. Backend

| Document | References |
|----------|-----------|
| [backend/api-overview.md](backend/api-overview.md) | endpoints.md, authentication.md, authorization.md, error-handling.md, governance/api-authorization-matrix.md |
| [backend/endpoints.md](backend/endpoints.md) | api-overview.md, authentication.md, authorization.md, governance/api-authorization-matrix.md |
| [backend/authentication.md](backend/authentication.md) | authorization.md, api-overview.md, governance/security-model.md, architecture/sequence-diagrams.md |
| [backend/authorization.md](backend/authorization.md) | authentication.md, governance/authorization.md, governance/permission-matrix.md, governance/api-authorization-matrix.md |
| [backend/services.md](backend/services.md) | api-overview.md, authentication.md, authorization.md, architecture/system-design.md |
| [backend/background-jobs.md](backend/background-jobs.md) | architecture/system-design.md, deployment/vercel.md, operations/maintenance.md |
| [backend/caching.md](backend/caching.md) | architecture/scalability.md, database/optimization.md, services.md |
| [backend/error-handling.md](backend/error-handling.md) | api-overview.md, logging.md, architecture/system-design.md |
| [backend/logging.md](backend/logging.md) | error-handling.md, governance/audit-logging.md, operations/monitoring.md |

## 5. Frontend

| Document | References |
|----------|-----------|
| [frontend/design-system.md](frontend/design-system.md) | themes.md, component-library.md, accessibility.md |
| [frontend/routing.md](frontend/routing.md) | navigation.md, state-management.md, governance/frontend-navigation-matrix.md |
| [frontend/state-management.md](frontend/state-management.md) | routing.md, navigation.md, backend/authentication.md |
| [frontend/themes.md](frontend/themes.md) | design-system.md, component-library.md |
| [frontend/accessibility.md](frontend/accessibility.md) | design-system.md, component-library.md, testing/accessibility-tests.md |
| [frontend/component-library.md](frontend/component-library.md) | design-system.md, routing.md, state-management.md |
| [frontend/forms.md](frontend/forms.md) | component-library.md, routing.md, backend/error-handling.md |
| [frontend/navigation.md](frontend/navigation.md) | routing.md, state-management.md, governance/frontend-navigation-matrix.md |

## 6. Studios

| Document | References |
|----------|-----------|
| [studios/analytics.md](studios/analytics.md) | workflows/dashboard-generation.md, architecture/data-flow.md, governance/permission-matrix.md |
| [studios/healthcare.md](studios/healthcare.md) | governance/compliance-notes.md, governance/security-model.md, product/industry-solutions.md |
| [studios/education.md](studios/education.md) | governance/compliance-notes.md, product/industry-solutions.md |
| [studios/business.md](studios/business.md) | product/industry-solutions.md, analytics.md |
| [studios/research.md](studios/research.md) | workflows/user-journeys.md, governance/roles.md, product/industry-solutions.md |
| [studios/automation.md](studios/automation.md) | workflows/etl-pipeline.md, architecture/data-flow.md, backend/services.md |
| [studios/smart-data-capture.md](studios/smart-data-capture.md) | workflows/document-capture.md, governance/roles.md, workflows/user-journeys.md |
| [studios/reporting.md](studios/reporting.md) | workflows/report-generation.md, backend/background-jobs.md, analytics.md |
| [studios/integrations.md](studios/integrations.md) | architecture/data-flow.md, architecture/integrations.md, integrations/ |

## 7. Workflows

| Document | References |
|----------|-----------|
| [workflows/onboarding.md](workflows/onboarding.md) | governance/organization-model.md, governance/workspace-model.md, user-journeys.md, architecture/sequence-diagrams.md |
| [workflows/dataset-upload.md](workflows/dataset-upload.md) | studios/analytics.md, architecture/data-flow.md, backend/endpoints.md |
| [workflows/etl-pipeline.md](workflows/etl-pipeline.md) | studios/automation.md, architecture/data-flow.md, backend/services.md |
| [workflows/dashboard-generation.md](workflows/dashboard-generation.md) | studios/analytics.md, architecture/data-flow.md, report-generation.md |
| [workflows/report-generation.md](workflows/report-generation.md) | studios/reporting.md, backend/background-jobs.md, dashboard-generation.md |
| [workflows/presentation-builder.md](workflows/presentation-builder.md) | dashboard-generation.md, report-generation.md, product/roadmap.md |
| [workflows/document-capture.md](workflows/document-capture.md) | studios/smart-data-capture.md, governance/roles.md, dataset-upload.md |
| [workflows/user-journeys.md](workflows/user-journeys.md) | governance/user-journeys.md, onboarding.md, governance/roles.md, user-guides/ |

## 8. Integrations

| Document | References |
|----------|-----------|
| [integrations/database-connectors.md](integrations/database-connectors.md) | file-imports.md, architecture/integrations.md, future-integrations.md |
| [integrations/file-imports.md](integrations/file-imports.md) | database-connectors.md, workflows/dataset-upload.md, cloud-storage.md |
| [integrations/cloud-storage.md](integrations/cloud-storage.md) | file-imports.md, future-integrations.md, architecture/integrations.md |
| [integrations/authentication-providers.md](integrations/authentication-providers.md) | backend/authentication.md, governance/security-model.md, future-integrations.md |
| [integrations/email.md](integrations/email.md) | backend/authentication.md, governance/organization-model.md, future-integrations.md |
| [integrations/future-integrations.md](integrations/future-integrations.md) | architecture/integrations.md, architecture/adr/README.md, product/roadmap.md |

## 9. Deployment

| Document | References |
|----------|-----------|
| [deployment/local-development.md](deployment/local-development.md) | docker.md, vercel.md, environments.md |
| [deployment/docker.md](deployment/docker.md) | local-development.md, vercel.md, production.md |
| [deployment/vercel.md](deployment/vercel.md) | local-development.md, production.md, environments.md, architecture/deployment-architecture.md |
| [deployment/production.md](deployment/production.md) | vercel.md, docker.md, environments.md, operations/monitoring.md |
| [deployment/environments.md](deployment/environments.md) | local-development.md, production.md, vercel.md |
| [deployment/ci-cd.md](deployment/ci-cd.md) | vercel.md, production.md, testing/strategy.md |
| [deployment/monitoring.md](deployment/monitoring.md) | operations/monitoring.md, backend/logging.md, production.md |

## 10. Testing

| Document | References |
|----------|-----------|
| [testing/strategy.md](testing/strategy.md) | unit-tests.md, integration-tests.md, e2e-tests.md, security-tests.md |
| [testing/unit-tests.md](testing/unit-tests.md) | strategy.md, integration-tests.md |
| [testing/integration-tests.md](testing/integration-tests.md) | unit-tests.md, e2e-tests.md, security-tests.md |
| [testing/e2e-tests.md](testing/e2e-tests.md) | strategy.md, integration-tests.md, performance-tests.md |
| [testing/performance-tests.md](testing/performance-tests.md) | strategy.md, architecture/scalability.md, database/optimization.md |
| [testing/accessibility-tests.md](testing/accessibility-tests.md) | frontend/accessibility.md, strategy.md |
| [testing/security-tests.md](testing/security-tests.md) | governance/security-model.md, governance/authorization.md, governance/compliance-notes.md, strategy.md |

## 11. Operations

| Document | References |
|----------|-----------|
| [operations/incident-response.md](operations/incident-response.md) | governance/security-model.md, governance/audit-logging.md, disaster-recovery.md, troubleshooting.md |
| [operations/monitoring.md](operations/monitoring.md) | deployment/monitoring.md, backend/logging.md, governance/audit-logging.md, incident-response.md |
| [operations/troubleshooting.md](operations/troubleshooting.md) | backend/error-handling.md, backend/logging.md, monitoring.md, incident-response.md |
| [operations/maintenance.md](operations/maintenance.md) | backups.md, database/backup-recovery.md, deployment/environments.md |
| [operations/backups.md](operations/backups.md) | database/backup-recovery.md, disaster-recovery.md, maintenance.md |
| [operations/disaster-recovery.md](operations/disaster-recovery.md) | backups.md, database/backup-recovery.md, incident-response.md |

## 12. Product

| Document | References |
|----------|-----------|
| [product/vision.md](product/vision.md) | roadmap.md, personas.md, feature-catalog.md, industry-solutions.md |
| [product/roadmap.md](product/roadmap.md) | vision.md, feature-catalog.md, release-plan.md, architecture/adr/README.md |
| [product/personas.md](product/personas.md) | governance/roles.md, workflows/user-journeys.md, user-guides/ |
| [product/feature-catalog.md](product/feature-catalog.md) | roadmap.md, pricing-notes.md, industry-solutions.md |
| [product/pricing-notes.md](product/pricing-notes.md) | feature-catalog.md, roadmap.md, architecture/adr/README.md |
| [product/industry-solutions.md](product/industry-solutions.md) | studios/, governance/compliance-notes.md, feature-catalog.md |
| [product/release-plan.md](product/release-plan.md) | release-notes/CHANGELOG.md, release-notes/release-process.md, release-notes/version-history.md, roadmap.md |

## 13. User Guides

| Document | References |
|----------|-----------|
| [user-guides/platform-owner.md](user-guides/platform-owner.md) | governance/roles.md, workflows/user-journeys.md, governance/security-model.md |
| [user-guides/organization-admin.md](user-guides/organization-admin.md) | governance/roles.md, workflows/user-journeys.md, governance/organization-model.md |
| [user-guides/department-manager.md](user-guides/department-manager.md) | governance/roles.md, workflows/user-journeys.md |
| [user-guides/analyst.md](user-guides/analyst.md) | governance/roles.md, workflows/user-journeys.md, studios/analytics.md |
| [user-guides/researcher.md](user-guides/researcher.md) | governance/roles.md, workflows/user-journeys.md, studios/research.md |
| [user-guides/data-entry-officer.md](user-guides/data-entry-officer.md) | governance/roles.md, workflows/user-journeys.md, studios/smart-data-capture.md |
| [user-guides/viewer.md](user-guides/viewer.md) | governance/roles.md, workflows/user-journeys.md |
| [user-guides/personal-workspace.md](user-guides/personal-workspace.md) | governance/roles.md, governance/workspace-model.md, workflows/user-journeys.md |

## 14. API

| Document | References |
|----------|-----------|
| [api/openapi.md](api/openapi.md) | authentication.md, examples.md, backend/api-overview.md, backend/endpoints.md |
| [api/authentication.md](api/authentication.md) | openapi.md, examples.md, backend/authentication.md, webhooks.md |
| [api/examples.md](api/examples.md) | authentication.md, openapi.md, backend/endpoints.md |
| [api/webhooks.md](api/webhooks.md) | authentication.md, architecture/integrations.md, integrations/future-integrations.md |
| [api/sdk.md](api/sdk.md) | authentication.md, examples.md, openapi.md |

## 15. Release Notes

| Document | References |
|----------|-----------|
| [release-notes/CHANGELOG.md](release-notes/CHANGELOG.md) | release-process.md, version-history.md, product/roadmap.md |
| [release-notes/release-process.md](release-notes/release-process.md) | CHANGELOG.md, version-history.md, deployment/production.md |
| [release-notes/version-history.md](release-notes/version-history.md) | CHANGELOG.md, release-process.md, product/roadmap.md |

## 16. Top-Level Documents

| Document | References |
|----------|-----------|
| [README.md](README.md) | All section directories |
| [STYLE_GUIDE.md](STYLE_GUIDE.md) | README.md, MAINTENANCE_POLICY.md |
| [MAINTENANCE_POLICY.md](MAINTENANCE_POLICY.md) | STYLE_GUIDE.md, CONTRIBUTOR_CHECKLIST.md |
| [CONTRIBUTOR_CHECKLIST.md](CONTRIBUTOR_CHECKLIST.md) | STYLE_GUIDE.md, MAINTENANCE_POLICY.md |
| [CROSS_REFERENCE_MAP.md](CROSS_REFERENCE_MAP.md) | All documents |

## Related Documents

- [README.md](README.md) — Documentation index
- [STYLE_GUIDE.md](STYLE_GUIDE.md) — Style guide
- [MAINTENANCE_POLICY.md](MAINTENANCE_POLICY.md) — Maintenance policy
- [CONTRIBUTOR_CHECKLIST.md](CONTRIBUTOR_CHECKLIST.md) — Contributor checklist
