"""FastAPI routes for the Reporting & Presentation Engine (Phase 8)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from services.report_engine import (
    ChartDefinition,
    ChartType,
    ExportFormat,
    Insight,
    KPIMetric,
    PresentationGenerator,
    Recommendation,
    ReportCompositionService,
    ReportSection,
    ReportSectionType,
    ReportTemplate,
    TableDefinition,
)
from shared.dependencies import get_current_user, require_permissions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Reports & Presentations"])


# â”€â”€ Request / Response Models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class CreateReportRequest(BaseModel):
    title: str
    template: str = "executive"
    organization_name: str = ""
    author_name: str = ""
    industry: str = ""
    dataset_id: int | None = None
    analysis_id: int | None = None


class UpdateSectionRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    kpis: list[dict[str, Any]] | None = None
    charts: list[dict[str, Any]] | None = None
    tables: list[dict[str, Any]] | None = None
    insights: list[dict[str, Any]] | None = None
    recommendations: list[dict[str, Any]] | None = None


class AddKPIsRequest(BaseModel):
    kpis: list[dict[str, Any]]


class AddChartRequest(BaseModel):
    title: str
    chart_type: str = "bar"
    data: list[dict[str, Any]] = []
    x_axis: str = ""
    y_axis: str = ""
    series: list[dict[str, Any]] = []
    config: dict[str, Any] = {}


class AddTableRequest(BaseModel):
    title: str
    columns: list[str] = []
    rows: list[list[Any]] = []
    summary: str = ""


class AddInsightsRequest(BaseModel):
    insights: list[dict[str, Any]]


class AddRecommendationsRequest(BaseModel):
    recommendations: list[dict[str, Any]]


class ExportRequest(BaseModel):
    format: str = "pdf"


# â”€â”€ Report CRUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("")
async def create_report(
    req: CreateReportRequest,
    current_user: dict = Depends(require_permissions("reports.create")),
):
    """Create a new report from a template."""
    try:
        template = ReportTemplate(req.template)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid template: {req.template}") from None

    report = ReportCompositionService.create_report(
        title=req.title,
        template=template,
        org_name=req.organization_name,
        author=req.author_name,
        industry=req.industry,
        dataset_id=req.dataset_id,
        analysis_id=req.analysis_id,
    )
    return report.to_dict()


@router.get("")
async def list_reports(current_user: dict = Depends(get_current_user)):
    """List all reports."""
    return ReportCompositionService.list_reports()


@router.get("/{report_id}")
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific report with all sections."""
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportCompositionService.export_to_dict(report)


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(require_permissions("reports.delete")),
):
    """Delete a report."""
    deleted = ReportCompositionService.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"deleted": True}


# â”€â”€ Section Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections")
async def add_section(
    report_id: str,
    req: dict[str, Any],
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add a new section to a report."""
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        section_type = ReportSectionType(req.get("section_type", "custom"))
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid section type: {req.get('section_type')}"
        ) from None

    section = ReportSection(
        section_type=section_type,
        title=req.get("title", "New Section"),
        content=req.get("content", ""),
    )
    updated = ReportCompositionService.add_section(report_id, section)
    return updated.to_dict() if updated else {}


@router.put("/{report_id}/sections/{section_order}")
async def update_section(
    report_id: str,
    section_order: int,
    req: UpdateSectionRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Update a section in a report."""
    updated = ReportCompositionService.update_section(
        report_id, section_order, req.model_dump(exclude_none=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Report or section not found")
    return updated.to_dict()


@router.delete("/{report_id}/sections/{section_order}")
async def remove_section(
    report_id: str,
    section_order: int,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Remove a section from a report."""
    updated = ReportCompositionService.remove_section(report_id, section_order)
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found")
    return updated.to_dict()


# â”€â”€ KPI Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections/{section_order}/kpis")
async def add_kpis(
    report_id: str,
    section_order: int,
    req: AddKPIsRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add KPIs to a section."""
    kpis = [KPIMetric(**k) for k in req.kpis]
    updated = ReportCompositionService.add_kpis(report_id, section_order, kpis)
    if not updated:
        raise HTTPException(status_code=404, detail="Report or section not found")
    return updated.to_dict()


# â”€â”€ Chart Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections/{section_order}/charts")
async def add_chart(
    report_id: str,
    section_order: int,
    req: AddChartRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add a chart to a section."""
    try:
        chart_type = ChartType(req.chart_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid chart type: {req.chart_type}"
        ) from None

    chart = ChartDefinition(
        title=req.title,
        chart_type=chart_type,
        data=req.data,
        x_axis=req.x_axis,
        y_axis=req.y_axis,
        series=req.series,
        config=req.config,
    )
    updated = ReportCompositionService.add_chart(report_id, section_order, chart)
    if not updated:
        raise HTTPException(status_code=404, detail="Report or section not found")
    return updated.to_dict()


# â”€â”€ Table Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections/{section_order}/tables")
async def add_table(
    report_id: str,
    section_order: int,
    req: AddTableRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add a data table to a section."""
    table = TableDefinition(
        title=req.title,
        columns=req.columns,
        rows=req.rows,
        summary=req.summary,
    )
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for s in report.sections:
        if s.order == section_order:
            s.tables.append(table)
            break
    else:
        raise HTTPException(status_code=404, detail="Section not found")
    return report.to_dict()


# â”€â”€ Insight Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections/{section_order}/insights")
async def add_insights(
    report_id: str,
    section_order: int,
    req: AddInsightsRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add insights to a section."""
    insights = [Insight(**i) for i in req.insights]
    updated = ReportCompositionService.add_insights(report_id, section_order, insights)
    if not updated:
        raise HTTPException(status_code=404, detail="Report or section not found")
    return updated.to_dict()


# â”€â”€ Recommendation Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{report_id}/sections/{section_order}/recommendations")
async def add_recommendations(
    report_id: str,
    section_order: int,
    req: AddRecommendationsRequest,
    current_user: dict = Depends(require_permissions("reports.edit")),
):
    """Add recommendations to a section."""
    recs = [Recommendation(**r) for r in req.recommendations]
    updated = ReportCompositionService.add_recommendations(report_id, section_order, recs)
    if not updated:
        raise HTTPException(status_code=404, detail="Report or section not found")
    return updated.to_dict()


# â”€â”€ Executive Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/{report_id}/executive-summary")
async def get_executive_summary(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get the auto-generated executive summary for a report."""
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    summary = ReportCompositionService.generate_executive_summary(report)
    return {"report_id": report_id, "executive_summary": summary}


# â”€â”€ Export â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = Query("pdf", pattern="^(pdf|pptx|html|json)$"),
    current_user: dict = Depends(get_current_user),
):
    """Export a report to PDF, PPTX, HTML, or JSON."""
    try:
        fmt = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}") from None

    try:
        data, media_type, ext = ReportCompositionService.export_report(report_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.{ext}"},
    )


# â”€â”€ Presentation Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/{report_id}/presentation")
async def get_presentation_slides(report_id: str, current_user: dict = Depends(get_current_user)):
    """Generate presentation slides from a report."""
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    slides = PresentationGenerator.from_report(report)
    return {"report_id": report_id, "title": report.title, "slides": slides}


@router.get("/{report_id}/presentation/export")
async def export_presentation(
    report_id: str,
    format: str = Query("pptx", pattern="^(pptx|pdf)$"),
    current_user: dict = Depends(get_current_user),
):
    """Export a presentation from a report to PPTX or PDF."""
    report = ReportCompositionService.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "pptx":
        data, media_type, ext = ReportCompositionService.export_report(report_id, ExportFormat.PPTX)
    else:
        data, media_type, ext = ReportCompositionService.export_report(report_id, ExportFormat.PDF)

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=presentation_{report_id}.{ext}"},
    )


# â”€â”€ Templates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/templates/list")
async def list_templates(current_user: dict = Depends(get_current_user)):
    """List available report templates."""
    return {
        "templates": [
            {
                "key": t.value,
                "name": t.value.title(),
                "description": {
                    "executive": "High-level summary for C-suite with KPIs, insights, and recommendations",
                    "analytical": "Detailed analytical report with methodology, statistics, and findings",
                    "research": "Academic-style report with research methodology and discussion",
                    "operational": "Operational report focused on processes and performance",
                    "compliance": "Compliance and audit report format",
                }.get(t.value, ""),
            }
            for t in ReportTemplate
        ]
    }


@router.get("/section-types/list")
async def list_section_types(current_user: dict = Depends(get_current_user)):
    """List available section types."""
    return {
        "section_types": [
            {"key": s.value, "name": s.value.replace("_", " ").title()} for s in ReportSectionType
        ]
    }


@router.get("/chart-types/list")
async def list_chart_types(current_user: dict = Depends(get_current_user)):
    """List available chart types."""
    return {"chart_types": [{"key": c.value, "name": c.value.title()} for c in ChartType]}
