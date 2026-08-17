# Report and Presentation Engine

This document describes how Dataflow turns analysis results into professional
reports and presentations: the backend report/presentation engines, the
frontend workflow steps that configure them, and the API endpoints that
generate the final files.

## Report Engine Overview

The report engine lives in `services/report_engine.py` and models a report as
a `ReportComposition`:

```
ReportComposition
  ├── Cover Page (title, organization, date, author)
  ├── Executive Summary
  ├── Sections (ordered, each a ReportSection)
  │     ├── Key Metrics   (KPIMetric cards)
  │     ├── Charts        (ChartDefinition)
  │     ├── Data Tables   (TableDefinition)
  │     ├── Insights      (Insight)
  │     └── Recommendations (Recommendation)
  └── Appendix
```

Key data classes:
- `KPIMetric` — label, value, unit, trend direction/value, target, color
- `ChartDefinition` — title, `ChartType` (bar, line, pie, donut, area,
  scatter, heatmap, gauge), data, axes, series, config
- `TableDefinition` — title, columns, rows, summary
- `Insight` — title, description, `severity` (`info`/`warning`/`critical`/
  `positive`), metric, impact
- `Recommendation` — title, description, `priority` (`high`/`medium`/`low`),
  action, expected impact, timeline
- `ReportSection` — a `ReportSectionType` (`cover`, `executive_summary`,
  `key_metrics`, `chart`, `table`, `insights`, `recommendations`,
  `methodology`, `appendix`, `custom`), plus the KPIs/charts/tables/insights/
  recommendations attached to it, an `order`, and an optional `page_break`

`ReportCompositionService` is the in-memory service layer for building and
mutating reports: `create_report`, `get_report`, `list_reports`,
`delete_report`, `add_section` / `remove_section` / `update_section`,
`add_kpis`, `add_chart`, `add_insights`, `add_recommendations`,
`generate_executive_summary` (template-based summary text), and export
methods (`export_to_dict`, `export_to_html`, `export_to_pdf`,
`export_to_pptx`, `export_report`).

The report workflow is: **Dataset → Analysis → Insights → Report →
Presentation**, mirroring the dataset workflow's stages.

## Configurable Sections

Reports are built from `ReportTemplateFactory` templates
(`services/report_engine.py`), each pre-populating an ordered list of
`ReportSection`s:

- `executive_template` — Cover → Executive Summary → Key Performance
  Indicators → Performance Trends (chart) → Detailed Breakdown (table) → Key
  Insights → Strategic Recommendations
- `analytical_template` — a more detailed variant aimed at analysts
- `research_template` — an academic-style variant with methodology and
  hypotheses sections
- `create_template` — factory dispatcher that selects a template by
  `ReportTemplate` (`executive`, `analytical`, `research`, `operational`,
  `compliance`)

On the frontend, `frontend/features/data-workflow/ReportStep.tsx` exposes a
**Report Configuration** form (title, organization, author, sector) and a
**Report Sections** toggle grid, letting the user opt in/out of:

| Section | Description |
|---|---|
| Executive Summary | High-level findings overview |
| Data Quality | Quality assessment and cleaning actions |
| Methodology | Analysis approach and methods used |
| Visualizations | Charts and dashboard views |
| Recommendations | Actionable recommendations |
| Limitations | Data limitations and caveats |

The component previews the resulting structure as
`Cover Page - <enabled sections> - Appendix` and calls
`onGenerateReport(config)` when the user clicks **Generate Report**. In the
`data-to-decision` workflow page, this is wired to
`datasetService.persistAnalysis(...)`, which persists the analysis and returns
a `report_id` used to gate the "Continue to Presentation" action.

Standalone (non-workflow) report management is exposed through
`services/report_engine_routes.py`, mounted under a `reports` router, with
endpoints to create/list/get/delete reports and to add/update/remove
sections, KPIs, charts, tables, insights, and recommendations individually
(see **API Endpoints** below).

## Presentation Templates

`studios/presentation_service.py` defines `PresentationStudioService`, which
generates presentation slide decks from analysis results. It supports four
templates via `generate_slides(source_type, source_data, template)`:

- **`executive`** — high-level summary for C-suite: Title → Executive Summary
  → Key Metrics (chart) → Findings → Recommendations → Next Steps
- **`analytical`** — detailed findings for analysts: Title → Data Overview →
  Descriptive Statistics (chart) → Trend Analysis (chart) → Statistical Tests
  → Detailed Findings → Limitations & Assumptions → Conclusions
- **`research`** — academic-style with methodology: Title → Research Question
  → Methodology → Hypotheses → Results (chart) → Statistical Summary (table)
  → Discussion → Conclusions & Future Work
- **`pitch`** — persuasive format for stakeholders: Title → The Opportunity →
  Market Evidence (chart) → Key Insights → Expected Impact → Call to Action

Each slide is a dict with `slide_number`, `layout` (`title`, `bullets`,
`chart`, or `table`), `title`, `content`, optional `chart_config`, and
(for the executive template) `speaker_notes`.

`PresentationStudioService` also provides persistence:
`create_presentation` / `list_presentations` / `get_presentation` (backed by
the `Presentation` model in `studios/models.py`), and
`generate_and_save`, which generates slides and stores them (`pres.slides`,
`pres.is_generated = True`) against an organization and source (analysis,
research, dashboard, or workflow).

`services/report_engine.py` additionally exposes `export_to_pptx` on
`ReportCompositionService`, which converts a `ReportComposition` directly into
a `.pptx` file (title slides, content slides, KPI slides, table slides) using
`python-pptx`, and a `PresentationGenerator.from_report` helper to derive
slide metadata from a report composition without exporting a file.

## PPTX Generation Pipeline

There are two ways a PPTX file gets produced in the platform:

1. **Report-driven export** — `ReportCompositionService.export_to_pptx(report)`
   (`services/report_engine.py`) builds a `pptx.Presentation` directly from a
   `ReportComposition`'s sections (title slide, KPI slides, table slides,
   content slides), falling back to a JSON representation if `python-pptx`
   is not installed. Reachable via `GET /{report_id}/export?format=pptx`
   (`export_report` in `report_engine_routes.py`) or
   `GET /{report_id}/presentation/export`.

2. **One-click workflow presentation** — the dataset workflow's **Present**
   step (`frontend/features/data-workflow/PresentStep.tsx`) offers a single
   "Create Presentation" button. It calls
   `POST /api/dataset-workflow/{workflow_id}/presentation`
   (`generate_presentation` in `services/dataset_workflow_routes.py`), which:
   - Reads results already computed during the workflow: `PROFILED`,
     `QUALITY_CHECKED`, `INDUSTRY_IDENTIFIED`, `INSIGHTS_GENERATED`, and
     `DASHBOARD_READY` stage outputs.
   - Assembles a `source_data` dict (title, subtitle, executive summary,
     top 5 findings from `insights_data`, top 5 recommendations from the
     quality report, a data overview string with row/column counts and
     quality score, and a chart config from the recommended dashboard
     charts).
   - Calls `PresentationStudioService.generate_slides(source_type="workflow",
     source_data, template=payload.template)` to get slide metadata.
   - Builds an actual `.pptx` in memory with `python-pptx`
     (`Presentation()`, 13.333×7.5 inch widescreen slides), setting each
     slide's title/content placeholders and speaker notes.
   - Writes an audit event (`dataset_workflow.presentation.generate`) via
     `log_audit_event`.
   - Streams the file back as
     `StreamingResponse` with
     `media_type=application/vnd.openxmlformats-officedocument.presentationml.presentation`
     and a `Content-Disposition: attachment` header
     (`{dataset_name}_presentation.pptx`).

The frontend then stores the returned blob and enables a **Download PPTX**
button (`onDownloadPresentation`), after which the workflow is marked
complete (all stages: Upload → Understand → Clean → Analyze → Visualize →
Report → Present).

## API Endpoints

### Dataset workflow (per-workflow, stateful)
`services/dataset_workflow_routes.py`:
- `POST /{workflow_id}/analyze` — run Easy/Pro mode analysis (feeds report data)
- `POST /{workflow_id}/presentation` — generate and download a one-click PPTX
  presentation from the workflow's accumulated stage results
  (`GeneratePresentationRequest`: `template` — `executive`/`analytical`/
  `research`/`pitch`, and optional `title`)

### Standalone report builder
`services/report_engine_routes.py`:
- `POST /` — create a report (`create_report`)
- `GET /` — list reports
- `GET /{report_id}` — get a report
- `DELETE /{report_id}` — delete a report
- `POST /{report_id}/sections` — add a section
- `PUT /{report_id}/sections/{section_order}` — update a section
- `DELETE /{report_id}/sections/{section_order}` — remove a section
- `POST /{report_id}/sections/{section_order}/kpis` — add KPIs to a section
- `POST /{report_id}/sections/{section_order}/charts` — add a chart
- `POST /{report_id}/sections/{section_order}/tables` — add a table
- `POST /{report_id}/sections/{section_order}/insights` — add insights
- `POST /{report_id}/sections/{section_order}/recommendations` — add recommendations
- `GET /{report_id}/executive-summary` — generate/return the executive summary
- `GET /{report_id}/export?format=` — export as `pdf`, `pptx`, `html`, or `json`
- `GET /{report_id}/presentation` — get generated slide metadata
- `GET /{report_id}/presentation/export` — export the presentation file
- `GET /templates/list` — list available `ReportTemplate`s
- `GET /section-types/list` — list available `ReportSectionType`s
- `GET /chart-types/list` — list available `ChartType`s
