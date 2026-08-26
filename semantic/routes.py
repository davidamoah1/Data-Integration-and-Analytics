"""API routes for the Semantic Intelligence Engine."""

from __future__ import annotations

import logging

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from semantic.service import SemanticIntelligenceService
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic", tags=["semantic"])


class AnalyzeRequest(BaseModel):
    """Request to analyze a dataset (when data is already loaded)."""

    table_name: str = "uploaded_dataset"
    overrides: dict | None = None
    admin_confirmed: bool = False


class SearchRequest(BaseModel):
    """Semantic search request."""

    query: str


class OverrideRequest(BaseModel):
    """Admin override for semantic mappings."""

    overrides: dict  # {column_name: entity_key}


@router.get("/entities")
async def list_entities():
    """List all business entities in the library."""
    from semantic.entity_library import get_all_entities

    entities = get_all_entities()
    return {
        "total": len(entities),
        "entities": [
            {
                "key": k,
                "display_name": v["display_name"],
                "industry": v["industry"],
                "synonyms": v["synonyms"],
                "kpis": v["kpis"],
            }
            for k, v in entities.items()
        ],
    }


@router.get("/entities/{industry}")
async def list_entities_by_industry(industry: str):
    """List business entities for a specific industry."""
    from semantic.entity_library import get_entities_by_industry

    entities = get_entities_by_industry(industry)
    return {
        "industry": industry,
        "total": len(entities),
        "entities": [
            {
                "key": k,
                "display_name": v["display_name"],
                "industry": v["industry"],
                "synonyms": v["synonyms"],
                "kpis": v["kpis"],
            }
            for k, v in entities.items()
        ],
    }


@router.get("/industries")
async def list_industries():
    """List all supported industries with their knowledge bases."""
    from semantic.industry_knowledge import get_all_industries

    industries = get_all_industries()
    return {
        "total": len(industries),
        "industries": [
            {
                "key": k,
                "display_name": v["display_name"],
                "description": v["description"],
                "entities": v["entities"],
                "kpi_categories": list(v["kpis"].keys()),
                "alert_count": len(v["alerts"]),
                "prompt_count": len(v["ai_prompts"]),
            }
            for k, v in industries.items()
        ],
    }


@router.get("/industries/{industry}")
async def get_industry_detail(industry: str):
    """Get detailed knowledge base for a specific industry."""
    from semantic.industry_knowledge import get_industry_knowledge

    knowledge = get_industry_knowledge(industry)
    if not knowledge:
        return {"error": f"Industry '{industry}' not found"}, 404
    return knowledge


def _read_semantic_upload(file: UploadFile) -> pd.DataFrame:
    """Read an uploaded CSV/Excel file into a DataFrame."""
    content = file.file.read()
    file.file.seek(0)
    if file.filename.endswith(".csv"):
        from io import StringIO

        return pd.read_csv(StringIO(content.decode("utf-8")))
    elif file.filename.endswith((".xlsx", ".xls")):
        from io import BytesIO

        return pd.read_excel(BytesIO(content))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or XLSX.")


@router.post("/analyze")
async def analyze_upload(
    request: Request,
    file: UploadFile = File(...),
    admin_confirmed: bool = False,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Analyze an uploaded dataset through the full semantic pipeline."""
    df = _read_semantic_upload(file)
    org_id = get_current_organization_id(current_user, db)

    result = SemanticIntelligenceService.analyze_dataset(
        df, file.filename, admin_confirmed=admin_confirmed
    )
    log_audit_event(
        db=db,
        action="semantic.analyze_upload",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="dataset",
        resource_id=file.filename,
        new_values={"admin_confirmed": admin_confirmed},
        request=request,
    )
    db.commit()
    return result


@router.post("/analyze-with-overrides")
async def analyze_with_overrides(
    request: Request,
    file: UploadFile = File(...),
    overrides: str | None = Form(None),
    admin_confirmed: bool = False,
    force_industry: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Analyze a dataset with admin overrides applied."""
    import json as _json

    parsed_overrides: dict | None = None
    if overrides:
        try:
            parsed_overrides = _json.loads(overrides)
        except (ValueError, TypeError):
            parsed_overrides = None

    df = _read_semantic_upload(file)
    org_id = get_current_organization_id(current_user, db)

    result = SemanticIntelligenceService.analyze_dataset(
        df,
        file.filename,
        parsed_overrides,
        admin_confirmed=admin_confirmed,
        force_industry=force_industry,
    )
    log_audit_event(
        db=db,
        action="semantic.analyze_with_overrides",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="dataset",
        resource_id=file.filename,
        new_values={"overrides": overrides, "admin_confirmed": admin_confirmed},
        request=request,
    )
    db.commit()
    return result


@router.post("/detect-industry")
async def detect_industry(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Quick industry detection from an uploaded file."""
    df = _read_semantic_upload(file)
    org_id = get_current_organization_id(current_user, db)

    result = SemanticIntelligenceService.detect_industry(df)
    log_audit_event(
        db=db,
        action="semantic.detect_industry",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="dataset",
        resource_id=file.filename,
        request=request,
    )
    db.commit()
    return result


@router.post("/search")
async def semantic_search(request: SearchRequest):
    """Perform semantic search for business concepts."""
    result = SemanticIntelligenceService.semantic_search(request.query)
    return result


@router.get("/glossary")
async def get_glossary():
    """Get the full business glossary."""
    glossary = SemanticIntelligenceService.get_business_glossary()
    return {"total": len(glossary), "glossary": glossary}


@router.get("/dashboard-registry/{industry}")
async def get_dashboard_registry(industry: str):
    """Get the dashboard template for an industry."""
    from semantic.dashboard_registry import DashboardRegistry

    return DashboardRegistry.to_dict(industry)


@router.get("/kpi-registry/{industry}")
async def get_kpi_registry(industry: str):
    """Get KPI definitions for an industry."""
    from semantic.kpi_registry import KPIRegistry

    return {"industry": industry, "kpis": KPIRegistry.to_dict(industry)}


@router.get("/widget-registry")
async def get_widget_registry():
    """List reusable widget types supported by dashboard templates."""
    from semantic.dashboard_registry import WidgetRegistry

    return {"widget_types": WidgetRegistry.supported_types()}


@router.get("/report-registry/{industry}")
async def get_report_registry(industry: str):
    """Get industry-aware report types."""
    from semantic.report_registry import ReportRegistry

    return {"industry": industry, "reports": ReportRegistry.get(industry)}


@router.get("/knowledge-graph/stats")
async def knowledge_graph_stats():
    """Get knowledge graph statistics (from entity library)."""
    from semantic.entity_library import ENTITY_LIBRARY
    from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE

    total_entities = len(ENTITY_LIBRARY)
    total_industries = len(INDUSTRY_KNOWLEDGE)
    total_kpis = sum(len(e["kpis"]) for e in ENTITY_LIBRARY.values())
    total_relationships = sum(len(e["relationships"]) for e in ENTITY_LIBRARY.values())

    return {
        "total_entities": total_entities,
        "total_industries": total_industries,
        "total_kpis": total_kpis,
        "total_relationships": total_relationships,
        "industries": list(INDUSTRY_KNOWLEDGE.keys()),
    }


@router.get("/health")
async def semantic_health():
    """Health check for the semantic engine."""
    return {
        "status": "healthy",
        "engine": "semantic_intelligence",
        "version": "1.0",
        "modules": [
            "metadata_extraction",
            "data_profiling",
            "semantic_engine",
            "entity_library",
            "relationship_engine",
            "industry_knowledge",
            "mapping_engine",
            "knowledge_graph",
            "kpi_generator",
            "dashboard_generator",
            "semantic_search",
            "governance",
        ],
    }


class PersistAnalysisRequest(BaseModel):
    """Request body for persisting semantic analysis results."""

    table_name: str = "uploaded_dataset"
    industry: str | None = None
    dashboard_config: dict | None = None
    kpis: list[dict] | None = None
    recommendations: list[str] | None = None
    alerts: list[dict] | None = None


@router.post("/persist-analysis")
async def persist_analysis(
    body: PersistAnalysisRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Persist semantic analysis results (dashboard + KPIs) to the analytics database.

    Creates a Dashboard with widgets and KPI records so they appear on the
    Analytics and Dashboard pages.
    """
    from analytics.models import KPI, AnalyticsAlert, Dashboard, DashboardWidget, KPIHistory

    org_id = current_user.get("organization_id")
    if org_id is None:
        from shared.tenant import get_current_organization_id

        org_id = get_current_organization_id(current_user, db)

    created_dashboard_id = None
    created_kpi_ids: list[int] = []

    # 1. Create dashboard if config provided
    if body.dashboard_config:
        dash = Dashboard(
            owner_id=current_user["id"],
            organization_id=org_id,
            name=body.dashboard_config.get("title", f"{body.table_name} Dashboard"),
            description=body.dashboard_config.get("subtitle", ""),
            theme=body.industry or "default",
            layout=body.dashboard_config.get("widgets", []),
            is_public=True,
        )
        db.add(dash)
        db.flush()
        created_dashboard_id = dash.id

        # Add widgets
        for i, widget in enumerate(body.dashboard_config.get("widgets", [])):
            w = DashboardWidget(
                organization_id=org_id,
                dashboard_id=dash.id,
                widget_type=widget.get("type", "chart"),
                title=widget.get("title", ""),
                configuration={
                    "entity": widget.get("entity", ""),
                    "metric": widget.get("metric", ""),
                    "available": widget.get("available", False),
                },
                position={"x": (i % 4) * 3, "y": (i // 4) * 4, "w": 3, "h": 4},
                group_name=widget.get("entity", "general"),
            )
            db.add(w)

    # 2. Create KPIs
    if body.kpis:
        for kpi_data in body.kpis:
            kpi = KPI(
                owner_id=current_user["id"],
                organization_id=org_id,
                name=kpi_data.get("label", kpi_data.get("key", "Unknown KPI")),
                description=f"Auto-generated from semantic analysis of '{body.table_name}'",
                category=kpi_data.get("category", "general"),
                formula=kpi_data.get("key", "semantic"),
                unit=kpi_data.get("unit", ""),
            )
            db.add(kpi)
            db.flush()
            created_kpi_ids.append(kpi.id)

            # Record the value in history
            if kpi_data.get("value") is not None:
                hist = KPIHistory(
                    kpi_id=kpi.id,
                    value=float(kpi_data["value"]),
                    status="healthy",
                )
                db.add(hist)

    # 3. Create alerts if any
    if body.alerts:
        for alert_data in body.alerts:
            alert = AnalyticsAlert(
                organization_id=org_id,
                alert_type="semantic",
                severity=alert_data.get("severity", "warning"),
                title=alert_data.get("title", "Semantic Alert"),
                message=alert_data.get("description", ""),
                source_type="semantic_analysis",
            )
            db.add(alert)

    db.commit()

    # 4. Generate a report from the analysis results
    from ai.models import AIReportGeneration

    report_sections = []
    report_content_parts = []

    industry_label = body.industry or "Unknown"
    report_title = f"{industry_label.capitalize()} Analysis Report â€” {body.table_name}"

    # Summary
    summary_parts = []
    if created_dashboard_id:
        summary_parts.append(
            f"Dashboard created with {len(body.dashboard_config.get('widgets', [])) if body.dashboard_config else 0} widgets."
        )
    if created_kpi_ids:
        summary_parts.append(f"{len(created_kpi_ids)} KPIs tracked.")
    if body.alerts:
        summary_parts.append(f"{len(body.alerts)} alerts detected.")
    summary = " ".join(summary_parts) if summary_parts else "Semantic analysis completed."

    # KPI section
    if body.kpis:
        report_sections.append("Key Performance Indicators")
        report_content_parts.append("## Key Performance Indicators\n")
        for kpi in body.kpis:
            label = kpi.get("label", kpi.get("key", "Unknown"))
            value = kpi.get("value", "N/A")
            unit = kpi.get("unit", "")
            report_content_parts.append(f"- **{label}**: {value}{unit}\n")

    # Dashboard section
    if body.dashboard_config:
        report_sections.append("Dashboard Configuration")
        widgets = body.dashboard_config.get("widgets", [])
        report_content_parts.append("\n## Dashboard Configuration\n")
        report_content_parts.append(f"Title: {body.dashboard_config.get('title', 'N/A')}\n")
        report_content_parts.append(f"Widgets: {len(widgets)}\n")
        for w in widgets:
            report_content_parts.append(
                f"- {w.get('title', 'Untitled')} ({w.get('type', 'chart')})\n"
            )

    # Alerts section
    if body.alerts:
        report_sections.append("Alerts")
        report_content_parts.append("\n## Alerts\n")
        for alert in body.alerts:
            report_content_parts.append(
                f"- **{alert.get('title', 'Alert')}**: {alert.get('description', '')}\n"
            )

    # Recommendations section
    if body.recommendations:
        report_sections.append("Recommendations")
        report_content_parts.append("\n## Recommendations\n")
        for rec in body.recommendations:
            report_content_parts.append(f"- {rec}\n")

    report_content = (
        "".join(report_content_parts) if report_content_parts else "No detailed content available."
    )

    report = AIReportGeneration(
        organization_id=org_id,
        report_type="semantic_analysis",
        title=report_title,
        content=report_content,
        summary=summary,
        sections=report_sections,
        format="markdown",
        user_id=current_user["id"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    log_audit_event(
        db=db,
        action="semantic.persist_analysis",
        user_id=current_user["id"],
        organization_id=org_id,
        resource_type="dataset",
        resource_id=body.table_name,
        new_values={
            "dashboard_id": created_dashboard_id,
            "kpi_count": len(created_kpi_ids),
            "report_id": report.id,
        },
        request=request,
    )
    db.commit()

    return {
        "dashboard_id": created_dashboard_id,
        "kpi_ids": created_kpi_ids,
        "report_id": report.id,
        "message": f"Persisted {len(created_kpi_ids)} KPIs, {'1 dashboard' if created_dashboard_id else 'no dashboard'}, and 1 report",
    }
