"""FastAPI routes for all Data Intelligence Studios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id
from studios.cleaning_service import DataCleaningService
from studios.collaboration_service import CollaborationService
from studios.industry_service import IndustryIntelligenceService, seed_industry_data
from studios.mentor_service import AIMentorService
from studios.ml_lab_service import MLLabService
from studios.presentation_service import PresentationStudioService
from studios.research_service import ResearchStudioService
from studios.statistics_service import StatisticsService
from studios.visualization_service import VisualizationEngine
from studios.workspace_service import DataWorkspaceService

router = APIRouter(prefix="/api/studios", tags=["studios"])


# ═══════════════════════════════════════════════════════════════
# Studio 1: Data Workspace
# ═══════════════════════════════════════════════════════════════


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataWorkspaceService(db)
    ws = svc.create_workspace(
        org_id=org_id,
        user_id=current_user["id"],
        name=payload["name"],
        dataset_id=payload.get("dataset_id"),
        description=payload.get("description"),
    )
    return {"id": ws.id, "name": ws.name}


@router.get("/workspaces")
async def list_workspaces(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataWorkspaceService(db)
    workspaces = svc.list_workspaces(org_id)
    return {
        "workspaces": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "dataset_id": w.dataset_id,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in workspaces
        ]
    }


@router.get("/workspaces/{workspace_id}")
async def get_workspace(
    workspace_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataWorkspaceService(db)
    ws = svc.get_workspace(workspace_id, org_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "id": ws.id,
        "name": ws.name,
        "description": ws.description,
        "dataset_id": ws.dataset_id,
        "columns_config": ws.columns_config,
        "filters": ws.filters,
        "sort_config": ws.sort_config,
        "conditional_formatting": ws.conditional_formatting,
        "pivot_config": ws.pivot_config,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
    }


@router.put("/workspaces/{workspace_id}/config")
async def update_workspace_config(
    workspace_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataWorkspaceService(db)
    ws = svc.update_config(
        workspace_id,
        org_id,
        columns_config=payload.get("columns_config"),
        filters=payload.get("filters"),
        sort_config=payload.get("sort_config"),
        conditional_formatting=payload.get("conditional_formatting"),
        pivot_config=payload.get("pivot_config"),
    )
    return {"id": ws.id, "updated": True}


@router.post("/workspaces/{workspace_id}/columns")
async def add_calculated_column(
    workspace_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataWorkspaceService(db)
    col = svc.add_calculated_column(
        workspace_id=workspace_id,
        column_name=payload["column_name"],
        formula=payload["formula"],
        data_type=payload.get("data_type", "float"),
        ai_generated=payload.get("ai_generated", False),
        ai_explanation=payload.get("ai_explanation"),
    )
    return {"id": col.id, "column_name": col.column_name}


@router.post("/workspaces/ai-suggest-formula")
async def ai_suggest_formula(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """AI-suggested formula based on natural language description."""
    result = DataWorkspaceService.ai_suggest_formula(
        description=payload["description"],
        available_columns=payload.get("available_columns", []),
    )
    return result


# ═══════════════════════════════════════════════════════════════
# Studio 2: Data Cleaning Engine
# ═══════════════════════════════════════════════════════════════


@router.post("/cleaning/jobs", status_code=status.HTTP_201_CREATED)
async def create_cleaning_job(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataCleaningService(db)
    job = svc.create_job(org_id, payload["dataset_id"], current_user["id"])
    return {"id": job.id, "status": job.status}


@router.get("/cleaning/jobs")
async def list_cleaning_jobs(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataCleaningService(db)
    jobs = svc.list_jobs(org_id)
    return {
        "jobs": [
            {
                "id": j.id,
                "dataset_id": j.dataset_id,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ]
    }


@router.get("/cleaning/jobs/{job_id}")
async def get_cleaning_job(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = DataCleaningService(db)
    job = svc.get_job(job_id, org_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "dataset_id": job.dataset_id,
        "status": job.status,
        "issues_found": job.issues_found,
        "transformations": job.transformations,
        "approved_changes": job.approved_changes,
        "summary": job.summary,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# Studio 3: Statistics Engine
# ═══════════════════════════════════════════════════════════════


@router.get("/statistics/analyses")
async def list_analyses(
    dataset_id: int | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = StatisticsService(db)
    analyses = svc.list_analyses(org_id, dataset_id)
    return {
        "analyses": [
            {
                "id": a.id,
                "dataset_id": a.dataset_id,
                "analysis_type": a.analysis_type,
                "test_name": a.test_name,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ]
    }


@router.get("/statistics/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = StatisticsService(db)
    analysis = svc.get_analysis(analysis_id, org_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "id": analysis.id,
        "analysis_type": analysis.analysis_type,
        "test_name": analysis.test_name,
        "parameters": analysis.parameters,
        "results": analysis.results,
        "interpretation": analysis.interpretation,
        "assumptions": analysis.assumptions,
        "assumptions_met": analysis.assumptions_met,
        "limitations": analysis.limitations,
    }


# ═══════════════════════════════════════════════════════════════
# Studio 4: ML Lab
# ═══════════════════════════════════════════════════════════════


@router.post("/ml/experiments", status_code=status.HTTP_201_CREATED)
async def create_ml_experiment(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = MLLabService(db)
    exp = svc.create_experiment(
        org_id=org_id,
        dataset_id=payload["dataset_id"],
        user_id=current_user["id"],
        name=payload["name"],
        task_type=payload["task_type"],
        features=payload.get("features"),
        target=payload.get("target"),
        algorithm=payload.get("algorithm"),
        hyperparameters=payload.get("hyperparameters"),
        is_no_code=payload.get("is_no_code", True),
    )
    return {"id": exp.id, "name": exp.name, "status": exp.status}


@router.get("/ml/experiments")
async def list_ml_experiments(
    dataset_id: int | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = MLLabService(db)
    experiments = svc.list_experiments(org_id, dataset_id)
    return {
        "experiments": [
            {
                "id": e.id,
                "name": e.name,
                "task_type": e.task_type,
                "algorithm": e.algorithm,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in experiments
        ]
    }


@router.get("/ml/experiments/{exp_id}")
async def get_ml_experiment(
    exp_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = MLLabService(db)
    exp = svc.get_experiment(exp_id, org_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": exp.id,
        "name": exp.name,
        "task_type": exp.task_type,
        "algorithm": exp.algorithm,
        "features": exp.features,
        "target": exp.target,
        "metrics": exp.metrics,
        "feature_importance": exp.feature_importance,
        "model_summary": exp.model_summary,
        "status": exp.status,
    }


# ═══════════════════════════════════════════════════════════════
# Studio 5: Research Studio
# ═══════════════════════════════════════════════════════════════


@router.post("/research/projects", status_code=status.HTTP_201_CREATED)
async def create_research_project(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = ResearchStudioService(db)
    project = svc.create_project(
        org_id=org_id,
        user_id=current_user["id"],
        title=payload["title"],
        research_question=payload.get("research_question"),
        methodology=payload.get("methodology"),
        industry=payload.get("industry"),
    )
    return {"id": project.id, "title": project.title}


@router.get("/research/projects")
async def list_research_projects(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = ResearchStudioService(db)
    projects = svc.list_projects(org_id)
    return {
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "research_question": p.research_question,
                "status": p.status,
                "industry": p.industry,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }


@router.get("/research/projects/{project_id}")
async def get_research_project(
    project_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = ResearchStudioService(db)
    project = svc.get_project(project_id, org_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    hypotheses = svc.list_hypotheses(project_id)
    return {
        "id": project.id,
        "title": project.title,
        "research_question": project.research_question,
        "methodology": project.methodology,
        "status": project.status,
        "industry": project.industry,
        "hypotheses": [
            {
                "id": h.id,
                "hypothesis": h.hypothesis,
                "null_hypothesis": h.null_hypothesis,
                "test_type": h.test_type,
                "status": h.status,
            }
            for h in hypotheses
        ],
    }


@router.post("/research/projects/{project_id}/hypotheses", status_code=status.HTTP_201_CREATED)
async def create_hypothesis(
    project_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = ResearchStudioService(db)
    project = svc.get_project(project_id, org_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    hyp = svc.create_hypothesis(
        project_id=project_id,
        hypothesis=payload["hypothesis"],
        null_hypothesis=payload.get("null_hypothesis"),
        alternative_hypothesis=payload.get("alternative_hypothesis"),
        test_type=payload.get("test_type"),
        significance_level=payload.get("significance_level", 0.05),
    )
    return {"id": hyp.id}


@router.post("/research/suggest-design")
async def suggest_research_design(payload: dict):
    """AI-suggested research design."""
    return ResearchStudioService.suggest_research_design(
        research_question=payload["research_question"],
        industry=payload.get("industry"),
    )


@router.post("/research/generate-hypotheses")
async def generate_hypotheses(payload: dict):
    """AI-generated hypotheses."""
    return {
        "hypotheses": ResearchStudioService.generate_hypothesis(
            research_question=payload["research_question"],
            variables=payload.get("variables", []),
        )
    }


# ═══════════════════════════════════════════════════════════════
# Studio 6: Presentation Studio
# ═══════════════════════════════════════════════════════════════


@router.post("/presentations", status_code=status.HTTP_201_CREATED)
async def create_presentation(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = PresentationStudioService(db)
    pres = svc.create_presentation(
        org_id=org_id,
        user_id=current_user["id"],
        title=payload["title"],
        source_type=payload["source_type"],
        source_id=payload.get("source_id"),
        template=payload.get("template", "executive"),
    )
    return {"id": pres.id, "title": pres.title}


@router.get("/presentations")
async def list_presentations(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = PresentationStudioService(db)
    presentations = svc.list_presentations(org_id)
    return {
        "presentations": [
            {
                "id": p.id,
                "title": p.title,
                "source_type": p.source_type,
                "template": p.template,
                "is_generated": p.is_generated,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in presentations
        ]
    }


@router.get("/presentations/{pres_id}")
async def get_presentation(
    pres_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = PresentationStudioService(db)
    pres = svc.get_presentation(pres_id, org_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return {
        "id": pres.id,
        "title": pres.title,
        "source_type": pres.source_type,
        "source_id": pres.source_id,
        "slides": pres.slides,
        "template": pres.template,
        "format": pres.format,
        "is_generated": pres.is_generated,
    }


# ═══════════════════════════════════════════════════════════════
# Studio 7: Industry Intelligence Engine
# ═══════════════════════════════════════════════════════════════


@router.get("/industries")
async def list_industries():
    """List all supported industries."""
    return {"industries": IndustryIntelligenceService.SUPPORTED_INDUSTRIES}


@router.get("/industries/{industry}/overview")
async def industry_overview(
    industry: str,
    db: DbSession = Depends(get_db),
):
    org_id = get_current_organization_id(current_user, db)
    svc = IndustryIntelligenceService(db)
    return svc.get_industry_overview(industry)


@router.get("/industries/{industry}/kpis")
async def industry_kpis(
    industry: str,
    db: DbSession = Depends(get_db),
):
    org_id = get_current_organization_id(current_user, db)
    svc = IndustryIntelligenceService(db)
    kpis = svc.get_kpis(industry)
    return {
        "kpis": [
            {
                "kpi_name": k.kpi_name,
                "kpi_code": k.kpi_code,
                "formula": k.formula,
                "unit": k.unit,
                "target": k.target,
                "category": k.category,
            }
            for k in kpis
        ]
    }


@router.get("/industries/{industry}/templates")
async def industry_templates(
    industry: str,
    db: DbSession = Depends(get_db),
):
    org_id = get_current_organization_id(current_user, db)
    svc = IndustryIntelligenceService(db)
    templates = svc.get_templates(industry)
    return {
        "templates": [
            {
                "template_name": t.template_name,
                "template_type": t.template_type,
                "config": t.config,
                "description": t.description,
            }
            for t in templates
        ]
    }


@router.post("/industries/recommend")
async def recommend_industry_analysis(payload: dict):
    """AI-recommended analyses for an industry."""
    return IndustryIntelligenceService.recommend_analysis(
        industry=payload["industry"],
        available_columns=payload.get("available_columns", []),
    )


# ═══════════════════════════════════════════════════════════════
# Studio 8: Visualization Engine
# ═══════════════════════════════════════════════════════════════


@router.post("/visualizations/recommend")
async def recommend_chart(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """AI-recommended chart for given data characteristics."""
    import pandas as pd

    # Build a DataFrame from provided data
    data = payload.get("data", [])
    columns = payload.get("columns")
    intent = payload.get("intent")

    if data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame()

    return VisualizationEngine.recommend_chart(df, columns, intent)


@router.post("/visualizations/recommend-multiple")
async def recommend_multiple_charts(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Recommend multiple complementary charts."""
    import pandas as pd

    data = payload.get("data", [])
    max_charts = payload.get("max_charts", 5)

    df = pd.DataFrame(data) if data else pd.DataFrame()
    return {"recommendations": VisualizationEngine.recommend_multiple(df, max_charts)}


# ═══════════════════════════════════════════════════════════════
# Studio 9: AI Mentors
# ═══════════════════════════════════════════════════════════════


@router.get("/mentors")
async def list_mentors():
    """List all available AI mentors."""
    svc = AIMentorService(None)  # No DB needed for listing
    return {"mentors": svc.list_mentors()}


@router.get("/mentors/{mentor_type}")
async def get_mentor_profile(mentor_type: str):
    org_id = get_current_organization_id(current_user, db)
    svc = AIMentorService(None)
    profile = svc.get_mentor_profile(mentor_type)
    if not profile:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return profile


@router.post("/mentors/sessions", status_code=status.HTTP_201_CREATED)
async def create_mentor_session(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = AIMentorService(db)
    session = svc.create_session(
        org_id=org_id,
        user_id=current_user["id"],
        mentor_type=payload["mentor_type"],
        title=payload.get("title"),
        context=payload.get("context"),
    )
    return {"id": session.id, "title": session.title}


@router.get("/mentors/sessions")
async def list_mentor_sessions(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = AIMentorService(db)
    sessions = svc.list_sessions(org_id, current_user["id"])
    return {
        "sessions": [
            {
                "id": s.id,
                "mentor_type": s.mentor_type,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]
    }


@router.post("/mentors/sessions/{session_id}/messages")
async def send_mentor_message(
    session_id: int,
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = AIMentorService(db)
    session = svc.get_session(session_id, org_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = svc.add_message(
        session_id=session_id,
        role="user",
        content=payload["content"],
        metadata=payload.get("metadata"),
    )
    return result


# ═══════════════════════════════════════════════════════════════
# Studio 10: Collaboration
# ═══════════════════════════════════════════════════════════════


@router.post("/collaboration/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CollaborationService(db)
    comment = svc.add_comment(
        org_id=org_id,
        user_id=current_user["id"],
        resource_type=payload["resource_type"],
        resource_id=payload["resource_id"],
        content=payload["content"],
        parent_id=payload.get("parent_id"),
        mentions=payload.get("mentions"),
    )
    return {"id": comment.id}


@router.get("/collaboration/comments")
async def list_comments(
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CollaborationService(db)
    comments = svc.list_comments(org_id, resource_type, resource_id)
    return {
        "comments": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "content": c.content,
                "parent_id": c.parent_id,
                "resolved": c.resolved,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comments
        ]
    }


@router.post("/collaboration/share", status_code=status.HTTP_201_CREATED)
async def share_resource(
    payload: dict,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CollaborationService(db)
    share = svc.share_resource(
        org_id=org_id,
        user_id=current_user["id"],
        resource_type=payload["resource_type"],
        resource_id=payload["resource_id"],
        shared_with_user_id=payload.get("shared_with_user_id"),
        shared_with_role=payload.get("shared_with_role"),
        permission=payload.get("permission", "view"),
    )
    return {"id": share.id}


@router.get("/collaboration/shares")
async def list_shares(
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = get_current_organization_id(current_user, db)
    svc = CollaborationService(db)
    shares = svc.list_shares(org_id, resource_type, resource_id)
    return {
        "shares": [
            {
                "id": s.id,
                "shared_with_user_id": s.shared_with_user_id,
                "shared_with_role": s.shared_with_role,
                "permission": s.permission,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in shares
        ]
    }
