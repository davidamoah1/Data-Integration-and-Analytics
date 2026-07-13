# Phase 8.1 — Enterprise Plugin Framework (EPF)

## Purpose

This document defines the Enterprise Plugin Framework (EPF) for AEDIP, enabling modular, secure, versioned installation, management, and lifecycle of plugins without affecting the core platform. EPF becomes the foundation for all future industry modules, AI packs, connector packs, dashboard packs, workflow packs, and enterprise features.

---

## 1. Enterprise Plugin Framework Architecture

### 1.1 Design Principles

- **Modular First:** Every feature is a plugin; the core is minimal.
- **Zero Downtime:** Install, enable, disable, upgrade, and rollback without core restart.
- **Secure by Default:** Sandboxing, RBAC integration, digital signatures, audit logs.
- **Versioned & Compatible:** Strict semantic versioning, compatibility matrix, dependency resolution.
- **Self-Describing:** Manifest-driven; metadata, permissions, routes, migrations, assets.
- **Observable:** Health checks, metrics, usage analytics, audit trails.
- **Developer Friendly:** SDK, generators, marketplace, hot-reload, testing harness.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AEDIP Core Platform                                      │
│  Auth · RBAC · API Gateway · ETL · AI Platform · Decision Center · Events       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Enterprise Plugin Framework                             │
│  Plugin Manager · Registry · Loader · Sandbox · Config · Events · Health       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐                ┌────────▼────────┐               ┌──────────▼─────────┐
│  Plugin       │                │  Plugin         │               │  Plugin            │
│  Health       │                │  Education      │               │  AI Pack           │
│               │                │                 │               │                    │
│ Manifest      │                │ Manifest        │               │ Manifest           │
│ Routes        │                │ Routes          │               │ Routes             │
│ Migrations    │                │ Migrations      │               │ Migrations         │
│ Widgets       │                │ Widgets         │               │ Prompts            │
│ APIs          │                │ APIs            │               │ Models             │
│ Permissions   │                │ Permissions     │               │ Permissions        │
│ Jobs          │                │ Jobs            │               │ Jobs               │
└───────────────┘                └─────────────────┘               └────────────────────┘
```

### 1.3 Core Components

| Component | Responsibility |
|-----------|----------------|
| **Plugin Manager** | Install, enable, disable, upgrade, rollback, uninstall plugins; resolve dependencies; enforce policies. |
| **Plugin Registry** | Central catalog of installed and available plugins; metadata, versions, permissions, assets. |
| **Plugin Loader** | Bootstrap plugins at startup; lazy loading; hot reload; dependency injection. |
| **Plugin Sandbox** | Isolated execution environment; resource limits; API isolation; secrets management. |
| **Plugin Config** | Hierarchical configuration (global, org, dept, user, environment); encrypted secrets. |
| **Plugin Events** | Event bus integration; plugin lifecycle events; domain events. |
| **Plugin Health** | Health checks, diagnostics, metrics, failure recovery. |
| **Plugin Marketplace** | Enterprise marketplace for discovery, distribution, reviews, licensing. |
| **Plugin SDK** | CLI, generators, testing harness, packaging tools. |

---

## 2. Plugin Lifecycle

| State | Description | Transitions |
|-------|-------------|-------------|
| **Discovered** | Plugin package detected in repository or marketplace. | → Installed |
| **Installed** | Package extracted, metadata stored, dependencies resolved. | → Registered / Failed |
| **Registered** | Manifest validated, database migrations applied, assets registered. | → Enabled / Disabled |
| **Enabled** | Plugin is active; routes, widgets, APIs, jobs loaded. | → Disabled / Updated / Failed |
| **Disabled** | Plugin is inactive; no routes, widgets, or jobs. | → Enabled / Uninstalled |
| **Paused** | Temporarily suspended (e.g., maintenance). | → Enabled / Disabled |
| **Updated** | New version installed; migrations applied; hot-reload if possible. | → Enabled / Rollback |
| **Downgraded** | Reverted to previous version. | → Enabled |
| **Rollback** | Failed upgrade reverted to prior version. | → Enabled |
| **Failed** | Error in installation, migration, or runtime. | → Disabled / Rollback |
| **Uninstalled** | Plugin removed; migrations rolled back if requested. | → Archived |
| **Archived** | Plugin records retained for audit; no code present. | — |

---

## 3. Plugin Manager

### 3.1 Capabilities

- **Discovery:** Scan local repository, marketplace, and remote registries.
- **Installation:** Extract, validate, apply migrations, register assets.
- **Enabling/Disabling:** Load/unload routes, widgets, APIs, jobs.
- **Updates:** Upgrade/downgrade, automatic updates, rollback.
- **Dependency Management:** Resolve required/optional dependencies, detect cycles, enforce version constraints.
- **Conflict Detection:** Detect overlapping routes, widget IDs, API paths, permissions.
- **Health & Diagnostics:** Health checks, metrics, logs, crash recovery.
- **Permission Enforcement:** Validate plugin permissions against RBAC.
- **Licensing:** Validate licenses, enforce usage limits.
- **Usage Analytics:** Track plugin usage per organization.
- **Audit Logging:** Log all lifecycle actions with user context.

### 3.2 Manager Interface

```python
class PluginManager:
    async def discover() -> List[PluginInfo]
    async def install(package_path: str, config: dict) -> PluginInstallation
    async def enable(plugin_id: str) -> None
    async def disable(plugin_id: str) -> None
    async def update(plugin_id: str, target_version: str) -> None
    async def rollback(plugin_id: str) -> None
    async def uninstall(plugin_id: str, keep_data: bool) -> None
    async def health(plugin_id: str) -> PluginHealth
    async def dependencies(plugin_id: str) -> List[Dependency]
    async def conflicts(plugin_id: str) -> List[Conflict]
    async def usage(plugin_id: str, org_id: int) -> PluginUsage
```

---

## 4. Plugin Architecture

Every plugin is a self-contained directory with a manifest and optional subfolders.

### 4.1 Directory Structure

```
plugins/{plugin_id}/
├── plugin.yaml                 # Manifest
├── README.md                   # Documentation
├── CHANGELOG.md                # Version history
├── LICENSE                     # License file
├── src/                        # Python source
│   └── {plugin_id}/
│       ├── __init__.py
│       ├── api.py              # FastAPI routes
│       ├── models.py           # SQLAlchemy models
│       ├── schemas.py          # Pydantic schemas
│       ├── services.py         # Business logic
│       ├── jobs.py             # Background jobs
│       ├── migrations/         # Alembic migrations
│       ├── widgets/            # Widget definitions
│       ├── dashboards/         # Dashboard templates
│       ├── reports/            # Report templates
│       ├── workflows/          # Workflow definitions
│       ├── rules/              # Rule definitions
│       ├── ai/                 # AI prompts/models
│       └── events.py           # Event handlers
├── frontend/                   # Frontend assets (optional)
│   ├── components/
│   ├── pages/
│   ├── widgets/
│   ├── assets/
│   └── locales/
├── assets/                     # Static assets (icons, images)
├── config/                     # Default configuration
├── tests/                      # Plugin tests
└── docs/                       # Additional docs
```

### 4.2 Manifest (plugin.yaml)

```yaml
plugin:
  id: health
  name: Health Industry Module
  version: 1.2.0
  description: Healthcare intelligence for hospitals and clinics.
  author: AEDIP Team
  license: MIT
  homepage: https://aedip.dev/plugins/health
  repository: https://github.com/aedip/plugins/health
  tags: [health, hospital, clinic, industry]

aedip:
  min_version: 7.0.0
  max_version: 8.0.0
  api_version: v1
  database_version: 8.0

dependencies:
  required:
    - id: core
      version: ">=7.0.0"
  optional:
    - id: ai
      version: ">=6.0.0"
    - id: etl
      version: ">=5.0.0"

permissions:
  - health.patient.read
  - health.patient.write
  - health.pharmacy.manage
  - health.laboratory.read

configuration:
  schema: config/schema.json
  defaults: config/defaults.yaml

routes:
  - prefix: /api/v1/health
    file: src/health/api.py
    tags: [Health]

widgets:
  - id: health_admissions
    name: Admissions Overview
    component: frontend/widgets/AdmissionsOverview.tsx
    permissions: [health.patient.read]

dashboards:
  - id: health_executive
    name: Executive Health Dashboard
    file: src/health/dashboards/executive.yaml
    permissions: [health.dashboard.read]

reports:
  - id: health_monthly
    name: Monthly Health Report
    file: src/health/reports/monthly.yaml
    schedule: 0 6 1 * *

workflows:
  - id: health_medicine_reorder
    name: Medicine Reorder Approval
    file: src/health/workflows/medicine_reorder.yaml

ai:
  prompts:
    - id: health_recommendations
      file: src/health/ai/prompts/recommendations.yaml
  models:
    - id: health_forecast
      file: src/health/ai/models/forecast.py

jobs:
  - id: health_daily_sync
    schedule: 0 5 * * *
    file: src/health/jobs/daily_sync.py

assets:
  icon: assets/icon.png

install:
  script: scripts/install.sh
  migration: src/health/migrations
  seed: src/health/seeds

upgrade:
  script: scripts/upgrade.sh
  migration: src/health/migrations

rollback:
  script: scripts/rollback.sh
  migration: src/health/migrations

uninstall:
  script: scripts/uninstall.sh
  cleanup: true
```

---

## 5. Database Design

### 5.1 Tables

```sql
CREATE TABLE plugins (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  author VARCHAR(255),
  license VARCHAR(128),
  homepage VARCHAR(512),
  repository VARCHAR(512),
  tags JSON,
  current_version VARCHAR(64) NOT NULL,
  installed_version VARCHAR(64),
  status VARCHAR(32) NOT NULL DEFAULT 'discovered',
  checksum CHAR(64),
  signature TEXT,
  manifest JSON NOT NULL,
  config_schema JSON,
  default_config JSON,
  installed_at DATETIME,
  enabled_at DATETIME,
  disabled_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status),
  INDEX idx_installed (installed_at)
) ENGINE=InnoDB;

CREATE TABLE plugin_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  version VARCHAR(64) NOT NULL,
  changelog TEXT,
  checksum CHAR(64),
  signature TEXT,
  manifest JSON NOT NULL,
  download_url VARCHAR(512),
  size_bytes BIGINT,
  published_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_plugin_version (plugin_id, version),
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_dependencies (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  dependency_plugin_id VARCHAR(128) NOT NULL,
  dependency_type VARCHAR(32) NOT NULL, -- required, optional
  version_constraint VARCHAR(128),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (dependency_plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  INDEX idx_plugin (plugin_id),
  INDEX idx_dependency (dependency_plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_installations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT,
  plugin_id VARCHAR(128) NOT NULL,
  version VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'installed',
  config JSON,
  enabled_at DATETIME,
  disabled_at DATETIME,
  installed_by BIGINT,
  installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (installed_by) REFERENCES users(id),
  UNIQUE KEY uniq_org_plugin (organization_id, plugin_id),
  INDEX idx_org (organization_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_settings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT,
  department_id BIGINT,
  user_id BIGINT,
  plugin_id VARCHAR(128) NOT NULL,
  scope VARCHAR(32) NOT NULL, -- global, org, dept, user
  key_name VARCHAR(128) NOT NULL,
  value JSON,
  is_encrypted BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (department_id) REFERENCES departments(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_scope_plugin_key (organization_id, department_id, user_id, plugin_id, scope, key_name),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_permissions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  permission_name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(128),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_plugin_permission (plugin_id, permission_name),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_routes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  method VARCHAR(16) NOT NULL,
  path VARCHAR(512) NOT NULL,
  handler VARCHAR(255),
  tags JSON,
  permissions JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_route (plugin_id, method, path),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_widgets (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  widget_id VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  component_path VARCHAR(512),
  permissions JSON,
  config_schema JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_widget (plugin_id, widget_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_dashboards (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  dashboard_id VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  layout JSON,
  permissions JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_dashboard (plugin_id, dashboard_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  report_id VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  template_path VARCHAR(512),
  schedule VARCHAR(128),
  permissions JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_report (plugin_id, report_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_workflows (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  workflow_id VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  definition JSON,
  permissions JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_workflow (plugin_id, workflow_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_jobs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  job_id VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  schedule VARCHAR(128),
  handler_path VARCHAR(512),
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_job (plugin_id, job_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_ai (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  ai_id VARCHAR(128) NOT NULL,
  type VARCHAR(32) NOT NULL, -- prompt, model, agent
  name VARCHAR(255) NOT NULL,
  file_path VARCHAR(512),
  config JSON,
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_ai (plugin_id, ai_id),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_events (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  event_name VARCHAR(255) NOT NULL,
  handler_path VARCHAR(512),
  enabled BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  UNIQUE KEY uniq_event (plugin_id, event_name),
  INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB;

CREATE TABLE plugin_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  level VARCHAR(16) NOT NULL,
  message TEXT NOT NULL,
  context JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  INDEX idx_plugin_time (plugin_id, created_at),
  INDEX idx_org_time (organization_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE plugin_health (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  status VARCHAR(32) NOT NULL,
  last_check DATETIME,
  error_message TEXT,
  metrics JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  UNIQUE KEY uniq_org_plugin (organization_id, plugin_id),
  INDEX idx_plugin (plugin_id),
  INDEX idx_status (status)
) ENGINE=InnoDB;

CREATE TABLE plugin_marketplace (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  category VARCHAR(128),
  rating DECIMAL(3,2),
  download_count INT DEFAULT 0,
  review_count INT DEFAULT 0,
  is_featured BOOLEAN DEFAULT FALSE,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  INDEX idx_category (category),
  INDEX idx_rating (rating),
  INDEX idx_featured (is_featured)
) ENGINE=InnoDB;

CREATE TABLE plugin_reviews (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  user_id BIGINT,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  title VARCHAR(255),
  comment TEXT,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_plugin (plugin_id),
  INDEX idx_rating (rating)
) ENGINE=InnoDB;

CREATE TABLE plugin_licenses (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  license_key VARCHAR(255),
  license_type VARCHAR(64), -- trial, commercial, enterprise
  expires_at DATETIME,
  usage_limits JSON,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  UNIQUE KEY uniq_org_plugin (organization_id, plugin_id),
  INDEX idx_plugin (plugin_id),
  INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

CREATE TABLE plugin_usage (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  date DATE NOT NULL,
  api_calls INT DEFAULT 0,
  widget_views INT DEFAULT 0,
  report_generations INT DEFAULT 0,
  job_runs INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  UNIQUE KEY uniq_org_plugin_date (organization_id, plugin_id, date),
  INDEX idx_plugin_date (plugin_id, date),
  INDEX idx_org_date (organization_id, date)
) ENGINE=InnoDB;

CREATE TABLE plugin_audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  plugin_id VARCHAR(128) NOT NULL,
  organization_id BIGINT,
  user_id BIGINT,
  action VARCHAR(64) NOT NULL,
  details JSON,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
  FOREIGN KEY (organization_id) REFERENCES organizations(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_plugin_time (plugin_id, created_at),
  INDEX idx_org_time (organization_id, created_at)
) ENGINE=InnoDB;
```

### 5.2 Indexes & Optimization

- Primary keys on all tables.
- Foreign key indexes.
- Composite unique constraints for business rules.
- Status and timestamp indexes for lifecycle queries.
- Full-text indexes on description and changelog for marketplace search.
- Partition `plugin_logs` and `plugin_usage` by month if needed.

---

## 6. ER Diagram (Textual)

```
plugins (1) → (n) plugin_versions
plugins (1) → (n) plugin_dependencies ←→ plugins
plugins (1) → (n) plugin_installations ←→ organizations
plugins (1) → (n) plugin_settings ←→ organizations/departments/users
plugins (1) → (n) plugin_permissions
plugins (1) → (n) plugin_routes
plugins (1) → (n) plugin_widgets
plugins (1) → (n) plugin_dashboards
plugins (1) → (n) plugin_reports
plugins (1) → (n) plugin_workflows
plugins (1) → (n) plugin_jobs
plugins (1) → (n) plugin_ai
plugins (1) → (n) plugin_events
plugins (1) → (n) plugin_logs ←→ organizations
plugins (1) → (n) plugin_health ←→ organizations
plugins (1) → (n) plugin_marketplace
plugins (1) → (n) plugin_reviews ←→ organizations/users
plugins (1) → (n) plugin_licenses ←→ organizations
plugins (1) → (n) plugin_usage ←→ organizations
plugins (1) → (n) plugin_audit_logs ←→ organizations/users
```

---

## 7. API Specification

Base path: `/api/v1/plugins`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List installed plugins. |
| GET | `/{id}` | Get plugin details. |
| POST | `/install` | Install a plugin from package or marketplace. |
| POST | `/{id}/enable` | Enable a plugin. |
| POST | `/{id}/disable` | Disable a plugin. |
| POST | `/{id}/update` | Update to latest or specified version. |
| POST | `/{id}/rollback` | Rollback to previous version. |
| DELETE | `/{id}` | Uninstall a plugin. |
| GET | `/{id}/health` | Get plugin health status. |
| GET | `/{id}/logs` | Get plugin logs. |
| GET | `/{id}/dependencies` | Get plugin dependencies. |
| GET | `/{id}/conflicts` | Check for conflicts. |
| GET | `/{id}/usage` | Get usage statistics. |
| GET | `/{id}/config` | Get plugin configuration. |
| PUT | `/{id}/config` | Update plugin configuration. |
| GET | `/marketplace` | Browse marketplace. |
| GET | `/marketplace/{id}` | Get marketplace plugin details. |
| POST | `/marketplace/{id}/install` | Install from marketplace. |
| POST | `/marketplace/{id}/review` | Submit a review. |
| GET | `/registry/routes` | Get all registered routes. |
| GET | `/registry/widgets` | Get all registered widgets. |
| GET | `/registry/dashboards` | Get all registered dashboards. |
| GET | `/registry/reports` | Get all registered reports. |
| GET | `/registry/workflows` | Get all registered workflows. |
| GET | `/registry/jobs` | Get all registered jobs. |
| GET | `/registry/ai` | Get all registered AI components. |
| GET | `/registry/permissions` | Get all registered permissions. |

### Example: Install Plugin

```http
POST /api/v1/plugins/install
{
  "source": "marketplace",
  "plugin_id": "health",
  "version": "1.2.0",
  "config": {
    "api_key": "secret",
    "sync_interval": "hourly"
  }
}
```

Response:
```json
{
  "installation_id": 123,
  "plugin_id": "health",
  "version": "1.2.0",
  "status": "installed",
  "enabled": false,
  "next_steps": [
    "Run migrations",
    "Configure settings",
    "Enable plugin"
  ]
}
```

---

## 8. Backend Architecture

### 8.1 Package Structure

```
plugin_framework/
├── __init__.py
├── manager.py              # PluginManager
├── loader.py               # PluginLoader
├── registry.py             # PluginRegistry
├── sandbox.py              # PluginSandbox
├── config.py               # PluginConfig
├── events.py               # PluginEventBus
├── health.py               # PluginHealth
├── marketplace.py          # MarketplaceClient
├── security.py             # Security, signatures, verification
├── migrations/             # Plugin framework migrations
├── api/
│   └── routes.py           # Plugin management APIs
├── models/
│   └── plugin_models.py    # SQLAlchemy models
├── schemas/
│   └── plugin_schemas.py   # Pydantic schemas
└── sdk/
    ├── cli.py              # Plugin CLI
    ├── generators.py       # Code generators
    └── packaging.py        # Packaging tools
```

### 8.2 Plugin Loader

```python
class PluginLoader:
    def __init__(self, registry: PluginRegistry, sandbox: PluginSandbox):
        self.registry = registry
        self.sandbox = sandbox

    async def load_plugin(self, plugin_id: str):
        plugin = await self.registry.get(plugin_id)
        if not plugin or plugin.status != 'enabled':
            return

        # Load routes
        for route in plugin.routes:
            await self.register_route(route)

        # Load widgets
        for widget in plugin.widgets:
            await self.register_widget(widget)

        # Start jobs
        for job in plugin.jobs:
            await self.schedule_job(job)

        # Register event handlers
        for event in plugin.events:
            await self.register_event_handler(event)

    async def unload_plugin(self, plugin_id: str):
        # Unregister routes, widgets, jobs, events
        pass
```

### 8.3 Plugin Sandbox

- **Process isolation** (optional for untrusted plugins).
- **Resource limits:** CPU, memory, file handles, network.
- **API isolation:** plugins access core via dependency injection.
- **Secrets management:** plugin secrets encrypted at rest, injected at runtime.

### 8.4 Event Bus Integration

- Core events: `plugin.installed`, `plugin.enabled`, `plugin.disabled`, `plugin.updated`, `plugin.failed`, `plugin.deleted`.
- Plugin events: plugins can subscribe to core events and emit their own.
- Async handlers for plugin lifecycle.

---

## 9. Frontend Architecture

### 9.1 Plugin UI Registration

- Plugins register pages, widgets, and menu items via manifest.
- Frontend registry lazy-loads components on demand.
- Route guards enforce plugin permissions.

### 9.2 Plugin Management UI

- **Installed Plugins:** list, enable/disable, configure, update, uninstall.
- **Marketplace:** browse, search, install, reviews.
- **Updates:** available updates, bulk update.
- **Health:** dashboard of plugin health, logs, metrics.
- **Configuration:** hierarchical settings with encryption indicators.

### 9.3 Widget System

- Widgets declare `component_path` and `permissions`.
- Dashboard builder lists available widgets per user permissions.
- Widgets receive plugin configuration and organization context.

### 9.4 Hot Reload

- Development mode: file watcher reloads plugin assets.
- Production: atomic updates without browser refresh.

---

## 10. Plugin SDK

### 10.1 CLI Commands

```bash
# Create new plugin
aedip plugin create health --template industry

# Generate components
aedip plugin generate widget admissions
aedip plugin generate api patients
aedip plugin generate migration add_patient_table
aedip plugin generate report monthly

# Build and package
aedip plugin build
aedip plugin package --version 1.2.0

# Publish to marketplace
aedip plugin publish --marketplace https://marketplace.aedip.dev

# Install locally
aedip plugin install ./health-1.2.0.zip

# Enable/disable
aedip plugin enable health
aedip plugin disable health

# Update/rollback
aedip plugin update health --version 1.2.1
aedip plugin rollback health

# Diagnostics
aedip plugin health health
aedip plugin logs health --tail 100
```

### 10.2 Generators

- **Plugin scaffold:** full directory with manifest, README, LICENSE.
- **API route:** FastAPI route with permissions and docs.
- **Widget:** React component with TypeScript and story.
- **Dashboard:** YAML layout with widgets.
- **Report:** Jinja2 template with data schema.
- **Migration:** Alembic revision.
- **Job:** Celery task template.
- **AI prompt:** YAML prompt with schema.

### 10.3 Testing Harness

```bash
aedip plugin test --type unit
aedip plugin test --type integration
aedip plugin test --type e2e
aedip plugin lint
aedip plugin security-scan
```

---

## 11. Marketplace Architecture

### 11.1 Marketplace Service

- **Catalog:** plugins, categories, versions, dependencies.
- **Search:** full-text, filters, tags.
- **Reviews & Ratings:** verified buyers only.
- **Licensing:** trial, commercial, enterprise; license key validation.
- **Analytics:** downloads, usage, revenue.
- **Content Delivery:** CDN for plugin packages.

### 11.2 Submission Workflow

1. Developer submits plugin package.
2. Automated security scan and validation.
3. Manual review for quality and compliance.
4. Approval → publish.
5. Version updates follow same flow.

### 11.3 Categories

- Industry Modules
- AI Packs
- Connector Packs
- Dashboard Packs
- Workflow Packs
- Report Packs
- Themes
- Notification Packs
- Developer Tools

---

## 12. Security Architecture

### 12.1 Digital Signatures

- Every plugin package signed with developer key.
- Core verifies signature before installation.
- Signature stored in `plugins.signature`.

### 12.2 Sandboxing

- Untrusted plugins run in isolated process.
- Resource limits enforced by cgroups/container.
- Network access controlled via allowlist.

### 12.3 Permissions

- Plugin permissions registered in `plugin_permissions`.
- RBAC integration: users must have permission to access plugin features.
- API endpoints enforce plugin permissions.

### 12.4 Secrets Management

- Plugin config values marked `is_encrypted` stored encrypted.
- Runtime secrets injected via environment or secure vault.
- Audit trail for secret access.

### 12.5 Audit Logging

- All lifecycle actions logged in `plugin_audit_logs`.
- Include user, IP, user agent, action, details.

---

## 13. Performance Strategy

### 13.1 Lazy Loading

- Plugins loaded only when enabled.
- Widgets and routes registered on demand.
- Frontend code-split per plugin.

### 13.2 Caching

- Plugin metadata cached in Redis.
- Registry lookups cached.
- Asset CDN caching.

### 13.3 Parallel Initialization

- Plugins initialize concurrently where possible.
- Dependency graph determines order.

### 13.4 Hot Reload

- Development: file watcher reloads plugin without restart.
- Production: atomic updates; new version loaded alongside old; switch over.

---

## 14. Monitoring Strategy

### 14.1 Health Checks

- Per-plugin health endpoint.
- Overall plugin framework health.
- Dependency health.

### 14.2 Metrics

- Plugin count, enabled/disabled.
- API latency per plugin.
- Error rates.
- Resource usage.
- Usage analytics per organization.

### 14.3 Logging

- Structured logs with correlation IDs.
- Log levels per plugin.
- Centralized log aggregation.

### 14.4 Alerting

- Plugin failure alerts.
- Resource threshold alerts.
- Security violation alerts.

---

## 15. Deployment Strategy

### 15.1 Core Deployment

- Plugin framework deployed with core platform.
- Database migrations run automatically.
- Plugin directory mounted as volume.

### 15.2 Plugin Deployment

- Plugins installed via API or CLI.
- Packages extracted to `plugins/` directory.
- Migrations applied; assets registered.

### 15.3 Multi-Tenant

- Plugins enabled per organization.
- Configuration isolated per org.
- Usage tracked per org.

### 15.4 Rollback

- Failed upgrades auto-rollback.
- Manual rollback via API/CLI.
- Database migrations rolled back if possible.

---

## 16. Testing Strategy

### 16.1 Unit Tests

- Plugin Manager, Loader, Registry, Sandbox.
- Mock dependencies and database.

### 16.2 Integration Tests

- Install/enable/disable/update/uninstall workflows.
- Database migrations.
- API registration.

### 16.3 Plugin Tests

- Each plugin includes its own test suite.
- SDK provides test harness.

### 16.4 Performance Tests

- Load time with many plugins.
- Memory usage.
- API latency.

### 16.5 Security Tests

- Signature verification.
- Sandbox escape attempts.
- Permission bypass.

### 16.6 Compatibility Tests

- Plugin compatibility matrix.
- Upgrade/downgrade paths.

---

## 17. Developer Documentation

- **Getting Started:** install SDK, create first plugin.
- **Plugin Manifest:** reference for all fields.
- **API Guide:** how to add routes, permissions.
- **Widget Guide:** React component patterns.
- **AI Integration:** prompts and models.
- **Testing Guide:** unit, integration, e2e.
- **Publishing Guide:** marketplace submission.
- **Best Practices:** security, performance, versioning.

---

## 18. Administrator Documentation

- **Installation:** deploy plugin framework.
- **Plugin Management:** install, enable, disable, update, uninstall.
- **Configuration:** global, org, department, user settings.
- **Security:** signatures, permissions, audit logs.
- **Monitoring:** health checks, metrics, logs.
- **Troubleshooting:** common issues, recovery.
- **Marketplace:** browsing, installing, managing licenses.

---

## 19. Output Summary

1. **Enterprise Plugin Framework Architecture** — design principles, components, lifecycle.
2. **Database Design** — 20 tables with DDL, indexes, relationships, audit fields.
3. **ER Diagram** — textual representation of relationships.
4. **API Specification** — 30+ REST endpoints for plugin lifecycle, marketplace, registry.
5. **Backend Architecture** — package structure, loader, sandbox, events.
6. **Frontend Architecture** — UI registration, management UI, widget system, hot reload.
7. **Plugin SDK** — CLI commands, generators, testing harness.
8. **Marketplace Architecture** — catalog, submission, categories, licensing.
9. **Security Architecture** — signatures, sandboxing, permissions, secrets, audit.
10. **Event Bus Integration** — lifecycle events, plugin events.
11. **Performance Strategy** — lazy loading, caching, parallel init, hot reload.
12. **Monitoring Strategy** — health checks, metrics, logging, alerting.
13. **Deployment Strategy** — core, plugins, multi-tenant, rollback.
14. **Testing Strategy** — unit, integration, plugin, performance, security, compatibility.
15. **Developer Documentation** — guides for creating, testing, publishing plugins.
16. **Administrator Documentation** — guides for managing, securing, monitoring plugins.

All specifications are enterprise-grade, modular, production-ready, cloud-ready, scalable, secure, and fully integrated into AEDIP without breaking previous phases.
