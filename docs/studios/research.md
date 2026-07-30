# Research Studio

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: Product Manager

---

## Purpose

Document the Research Studio for research analytics.

## Scope

Research-specific features, statistical analysis, and publication tools.

## Audience

Researchers and data analysts.

---

## 1. Overview

The Research Studio provides tools for academic and market research, including survey analysis, statistical modeling, and publication-ready report generation.

## 2. Use Cases

- Survey response analysis
- Statistical hypothesis testing
- Correlation and regression analysis
- Publication-ready report generation
- Research dataset management

## 3. Key Features

| Feature | Permission | Description |
|---------|------------|-------------|
| Upload research data | `datasets.upload` | Import survey and research data |
| Statistical analysis | `analytics.view` | Run descriptive and inferential statistics |
| ML predictions | `ml.read`, `ml.execute` | Apply ML models to research data |
| Report generation | `reports.generate` | Create publication-ready reports |
| Report export | `reports.export` | Export to PDF, CSV, Excel |

## 4. Researcher Role

The `researcher` role has permissions tailored for research workflows:
- `datasets.upload`, `datasets.view`
- `analytics.view`
- `reports.generate`, `reports.view`, `reports.export`
- `etl.export`
- `ml.read`, `ml.execute`

## 5. Access

- Route: `/studios` → Research card
- Permission: `dashboard.view` (minimum)

## Related Documents

- [../workflows/user-journeys.md](../workflows/user-journeys.md) — Researcher journey
- [../governance/roles.md](../governance/roles.md) — Researcher role
- [../product/industry-solutions.md](../product/industry-solutions.md) — Industry solutions
