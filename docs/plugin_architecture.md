# Plugin Architecture

## Overview

The DataFlow Plugin System enables extensibility through installable plugins.

## Plugin Categories

| Category | Description |
|----------|-------------|
| `connector` | Data source connectors |
| `dashboard_template` | Pre-built dashboard layouts |
| `ai_agent` | AI-powered analysis agents |
| `industry_solution` | Complete industry packages |
| `data_processor` | Data transformation plugins |

## Plugin Metadata

Every plugin includes:
- `plugin_id`: Unique identifier
- `name`, `version`, `author`
- `description`
- `category`
- `permissions`: Required platform permissions
- `dependencies`: Other plugins required
- `config_schema`: Configuration fields

## Marketplace Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/marketplace/plugins` | Browse plugins |
| GET | `/marketplace/plugins/{id}` | Plugin details |
| POST | `/marketplace/plugins` | Publish plugin (admin) |
| POST | `/marketplace/plugins/{id}/install` | Install plugin |
| GET | `/marketplace/installations` | List installed plugins |
| POST | `/marketplace/installations/{id}/enable` | Enable plugin |
| POST | `/marketplace/installations/{id}/disable` | Disable plugin |
| DELETE | `/marketplace/installations/{id}` | Uninstall plugin |

## Installation Lifecycle

```
Browse → Install → Enable → [Disable → Enable] → Uninstall
```

## Industry Packages

Pre-built packages that include dataset templates, dashboards, KPIs, AI insights, and ML models.

| Package | Industry |
|---------|----------|
| healthcare-analytics | Healthcare |
| education-intelligence | Education |
| banking-analytics | Banking |
| agriculture-analytics | Agriculture |
| retail-intelligence | Retail |
| government-analytics | Government |
