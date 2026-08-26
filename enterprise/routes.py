"""Platform API routes â€” templates, collaboration, branding, and enterprise search."""

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session as DbSession

from enterprise.demo_data import is_demo_seeded, seed_demo_data
from enterprise.industry_packs import get_all_packs, get_pack
from enterprise.models import (
    ActivityEvent,
    Comment,
    OrganizationBranding,
    SharedResource,
    Template,
    TemplateInstall,
)
from enterprise.schemas import (
    BrandingUpdate,
    CommentCreate,
    CommentResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ShareCreate,
    ShareResponse,
    TemplateCreate,
)
from enterprise.subscription import (
    ALL_FEATURES,
    PLAN_DEFINITIONS,
    SubscriptionService,
)
from services.backup_service import BackupService
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/api/platform", tags=["Platform"])


# --- Template Marketplace ----------------------------------------------------


@router.get("/templates")
async def list_templates(
    template_type: str | None = Query(None),
    industry: str | None = Query(None),
    is_featured: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List templates with optional filters."""
    query = db.query(Template).filter(Template.is_public.is_(True))
    if template_type:
        query = query.filter(Template.template_type == template_type)
    if industry:
        query = query.filter(Template.industry == industry)
    if is_featured is not None:
        query = query.filter(Template.is_featured == is_featured)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Template.name.ilike(pattern), Template.description.ilike(pattern)))
    templates = query.order_by(Template.install_count.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "template_type": t.template_type,
            "industry": t.industry,
            "name": t.name,
            "description": t.description,
            "author": t.author,
            "version": t.version,
            "tags": t.tags or [],
            "is_featured": t.is_featured,
            "install_count": t.install_count,
            "rating": round(t.rating_sum / t.rating_count, 1) if t.rating_count else 0.0,
            "created_at": str(t.created_at) if t.created_at else None,
        }
        for t in templates
    ]


@router.post("/templates")
async def create_template(
    body: TemplateCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new template (admin only)."""
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    template = Template(
        template_type=body.template_type,
        industry=body.industry,
        name=body.name,
        description=body.description,
        author=body.author or current_user.get("email", "Unknown"),
        version=body.version,
        content=body.content,
        tags=body.tags,
        is_public=body.is_public,
        is_featured=body.is_featured,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "name": template.name}


@router.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a template with full content."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": template.id,
        "template_type": template.template_type,
        "industry": template.industry,
        "name": template.name,
        "description": template.description,
        "author": template.author,
        "version": template.version,
        "content": template.content,
        "tags": template.tags or [],
        "is_featured": template.is_featured,
        "install_count": template.install_count,
        "rating": (
            round(template.rating_sum / template.rating_count, 1) if template.rating_count else 0.0
        ),
        "created_at": str(template.created_at) if template.created_at else None,
        "updated_at": str(template.updated_at) if template.updated_at else None,
    }


@router.post("/templates/{template_id}/install")
async def install_template(
    template_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Install a template for the current organization."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    existing = (
        db.query(TemplateInstall)
        .filter(
            TemplateInstall.template_id == template_id,
            TemplateInstall.organization_id == current_user.get("organization_id"),
        )
        .first()
    )
    if existing:
        return {"message": "Template already installed", "already_installed": True}
    install = TemplateInstall(
        template_id=template_id,
        organization_id=current_user.get("organization_id"),
        installed_by=current_user["id"],
    )
    db.add(install)
    template.install_count += 1
    db.commit()
    return {"message": "Template installed", "content": template.content}


@router.post("/templates/{template_id}/rate")
async def rate_template(
    template_id: int,
    rating: int = Query(..., ge=1, le=5),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Rate a template (1-5 stars)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.rating_sum += rating
    template.rating_count += 1
    db.commit()
    avg = round(template.rating_sum / template.rating_count, 1)
    return {"message": "Rating submitted", "average": avg, "count": template.rating_count}


# --- Collaboration: Comments -------------------------------------------------


@router.get("/comments")
async def list_comments(
    resource_type: str = Query(...),
    resource_id: int = Query(...),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List comments for a resource."""
    org_id = get_current_organization_id(current_user, db)
    comments = (
        db.query(Comment)
        .filter(
            Comment.organization_id == org_id,
            Comment.resource_type == resource_type,
            Comment.resource_id == resource_id,
        )
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [
        {
            "id": c.id,
            "author_id": c.author_id,
            "parent_id": c.parent_id,
            "body": c.body,
            "mentions": c.mentions or [],
            "is_resolved": c.is_resolved,
            "created_at": str(c.created_at) if c.created_at else None,
        }
        for c in comments
    ]


@router.post("/comments", response_model=CommentResponse)
async def create_comment(
    body: CommentCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a comment on a resource."""
    org_id = get_current_organization_id(current_user, db)
    comment = Comment(
        organization_id=org_id,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        author_id=current_user["id"],
        parent_id=body.parent_id,
        body=body.body,
        mentions=body.mentions,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse(
        id=comment.id,
        resource_type=comment.resource_type,
        resource_id=comment.resource_id,
        author_id=comment.author_id,
        parent_id=comment.parent_id,
        body=comment.body,
        mentions=comment.mentions or [],
        is_resolved=comment.is_resolved,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark a comment as resolved."""
    org_id = get_current_organization_id(current_user, db)
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment or comment.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    if (
        comment.author_id != current_user["id"]
        and "admin" not in current_user["roles"]
        and "super_admin" not in current_user["roles"]
    ):
        raise HTTPException(
            status_code=403, detail="Only the author or an admin can resolve a comment"
        )
    comment.is_resolved = True
    db.commit()
    return {"message": "Comment resolved"}


# --- Collaboration: Shared Resources -----------------------------------------


@router.post("/share", response_model=ShareResponse)
async def share_resource(
    body: ShareCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Share a resource with a user, team, or organization."""
    share = SharedResource(
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        shared_by=current_user["id"],
        shared_with_type=body.shared_with_type,
        shared_with_id=body.shared_with_id,
        permission=body.permission,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return ShareResponse(
        id=share.id,
        resource_type=share.resource_type,
        resource_id=share.resource_id,
        shared_by=share.shared_by,
        shared_with_type=share.shared_with_type,
        shared_with_id=share.shared_with_id,
        permission=share.permission,
        created_at=share.created_at,
    )


@router.get("/shared")
async def list_shared_resources(
    resource_type: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List resources shared with the current user."""
    query = db.query(SharedResource).filter(
        or_(
            SharedResource.shared_with_id == current_user["id"],
            SharedResource.shared_by == current_user["id"],
        )
    )
    if resource_type:
        query = query.filter(SharedResource.resource_type == resource_type)
    shares = query.order_by(SharedResource.created_at.desc()).limit(50).all()
    return [
        {
            "id": s.id,
            "resource_type": s.resource_type,
            "resource_id": s.resource_id,
            "shared_by": s.shared_by,
            "shared_with_type": s.shared_with_type,
            "shared_with_id": s.shared_with_id,
            "permission": s.permission,
            "created_at": str(s.created_at) if s.created_at else None,
        }
        for s in shares
    ]


# --- Collaboration: Activity Timeline ----------------------------------------


@router.get("/activity")
async def list_activity(
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List recent activity events for the current user's organization."""
    query = db.query(ActivityEvent)
    if current_user.get("organization_id"):
        query = query.filter(ActivityEvent.organization_id == current_user["organization_id"])
    else:
        query = query.filter(ActivityEvent.user_id == current_user["id"])
    events = query.order_by(ActivityEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "metadata": e.event_metadata or {},
            "created_at": str(e.created_at) if e.created_at else None,
        }
        for e in events
    ]


# --- Branding ----------------------------------------------------------------


@router.get("/branding")
async def get_branding(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get branding configuration for the current organization."""
    org_id = current_user.get("organization_id")
    if not org_id:
        return {"branding": None, "message": "No organization configured"}
    branding = (
        db.query(OrganizationBranding)
        .filter(OrganizationBranding.organization_id == org_id)
        .first()
    )
    if not branding:
        return {"branding": None}
    return {
        "id": branding.id,
        "organization_id": branding.organization_id,
        "logo_url": branding.logo_url,
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "accent_color": branding.accent_color,
        "theme_mode": branding.theme_mode,
        "company_name": branding.company_name,
        "company_tagline": branding.company_tagline,
        "email_footer": branding.email_footer,
        "report_header_text": branding.report_header_text,
        "report_footer_text": branding.report_footer_text,
        "custom_css": branding.custom_css,
    }


@router.put("/branding")
async def update_branding(
    body: BrandingUpdate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create or update branding for the current organization."""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization configured")
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    branding = (
        db.query(OrganizationBranding)
        .filter(OrganizationBranding.organization_id == org_id)
        .first()
    )
    if not branding:
        branding = OrganizationBranding(organization_id=org_id)
        db.add(branding)
    branding.logo_url = body.logo_url
    branding.primary_color = body.primary_color or branding.primary_color
    branding.secondary_color = body.secondary_color or branding.secondary_color
    branding.accent_color = body.accent_color or branding.accent_color
    branding.theme_mode = body.theme_mode
    branding.company_name = body.company_name
    branding.company_tagline = body.company_tagline
    branding.email_footer = body.email_footer
    branding.report_header_text = body.report_header_text
    branding.report_footer_text = body.report_footer_text
    branding.custom_css = body.custom_css
    db.commit()
    db.refresh(branding)
    return {
        "id": branding.id,
        "organization_id": branding.organization_id,
        "message": "Branding updated",
    }


# --- Enterprise Search -------------------------------------------------------


@router.post("/search", response_model=SearchResponse)
async def enterprise_search(
    body: SearchRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Search across dashboards, reports, pipelines, KPIs, templates, and conversations."""
    results: list[dict] = []
    pattern = f"%{body.query}%"
    types = body.resource_types or [
        "dashboard",
        "kpi",
        "pipeline",
        "template",
        "conversation",
        "report",
    ]

    if "dashboard" in types:
        from analytics.models import Dashboard

        dash_query = db.query(Dashboard).filter(
            or_(
                Dashboard.name.ilike(pattern),
                Dashboard.description.ilike(pattern),
            )
        )
        if current_user.get("organization_id"):
            dash_query = dash_query.filter(
                or_(
                    Dashboard.organization_id == current_user["organization_id"],
                    Dashboard.is_public.is_(True),
                )
            )
        dashboards = dash_query.limit(body.limit).all()
        for d in dashboards:
            results.append(
                {
                    "resource_type": "dashboard",
                    "resource_id": d.id,
                    "title": d.name,
                    "description": d.description,
                    "url": f"/analytics/dashboards/{d.id}",
                    "score": 1.0,
                }
            )

    if "kpi" in types:
        from analytics.models import KPI

        kpi_query = db.query(KPI).filter(
            or_(KPI.name.ilike(pattern), KPI.description.ilike(pattern))
        )
        if current_user.get("organization_id"):
            kpi_query = kpi_query.filter(
                or_(
                    KPI.organization_id == current_user["organization_id"],
                    KPI.organization_id.is_(None),
                )
            )
        kpis = kpi_query.limit(body.limit).all()
        for k in kpis:
            results.append(
                {
                    "resource_type": "kpi",
                    "resource_id": k.id,
                    "title": k.name,
                    "description": k.description,
                    "url": f"/analytics/kpis/{k.id}",
                    "score": 1.0,
                }
            )

    if "pipeline" in types:
        from etl.models import ETLPipeline

        pipelines = (
            db.query(ETLPipeline)
            .filter(or_(ETLPipeline.name.ilike(pattern), ETLPipeline.description.ilike(pattern)))
            .limit(body.limit)
            .all()
        )
        for p in pipelines:
            results.append(
                {
                    "resource_type": "pipeline",
                    "resource_id": p.id,
                    "title": p.name,
                    "description": p.description,
                    "url": f"/etl/pipelines/{p.id}",
                    "score": 1.0,
                }
            )

    if "template" in types:
        templates = (
            db.query(Template)
            .filter(
                Template.is_public.is_(True),
                or_(Template.name.ilike(pattern), Template.description.ilike(pattern)),
            )
            .limit(body.limit)
            .all()
        )
        for t in templates:
            results.append(
                {
                    "resource_type": "template",
                    "resource_id": t.id,
                    "title": t.name,
                    "description": t.description,
                    "url": f"/platform/templates/{t.id}",
                    "score": 1.0,
                }
            )

    if "conversation" in types:
        from ai.models import AIConversation

        convs = (
            db.query(AIConversation)
            .filter(
                AIConversation.user_id == current_user["id"],
                or_(
                    AIConversation.title.ilike(pattern),
                    AIConversation.assistant_type.ilike(pattern),
                ),
            )
            .limit(body.limit)
            .all()
        )
        for c in convs:
            results.append(
                {
                    "resource_type": "conversation",
                    "resource_id": c.id,
                    "title": c.title or f"Conversation {c.id}",
                    "description": c.assistant_type,
                    "url": f"/ai/conversations/{c.id}",
                    "score": 1.0,
                }
            )

    if "report" in types:
        from ai.models import AIReportGeneration

        reports = (
            db.query(AIReportGeneration)
            .filter(
                AIReportGeneration.user_id == current_user["id"],
                AIReportGeneration.title.ilike(pattern),
            )
            .limit(body.limit)
            .all()
        )
        for r in reports:
            results.append(
                {
                    "resource_type": "report",
                    "resource_id": r.id,
                    "title": r.title,
                    "description": r.summary[:200] if r.summary else None,
                    "url": f"/ai/reports/{r.id}",
                    "score": 1.0,
                }
            )

    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results[: body.limit]],
        total=len(results),
    )


# --- Industry Solution Packs -------------------------------------------------


@router.get("/industry-packs")
async def list_industry_packs(
    current_user: dict = Depends(get_current_user),
):
    """List all available industry solution packs."""
    packs = get_all_packs()
    return [
        {
            "key": key,
            "name": pack["name"],
            "description": pack["description"],
            "dashboard_count": len(pack.get("dashboards", [])),
            "kpi_count": len(pack.get("kpis", [])),
            "etl_template_count": len(pack.get("etl_templates", [])),
            "report_template_count": len(pack.get("report_templates", [])),
            "ai_prompt_count": len(pack.get("ai_prompts", [])),
        }
        for key, pack in packs.items()
    ]


@router.get("/industry-packs/{pack_key}")
async def get_industry_pack(
    pack_key: str,
    current_user: dict = Depends(get_current_user),
):
    """Get full details of a specific industry pack."""
    pack = get_pack(pack_key)
    if not pack:
        raise HTTPException(status_code=404, detail="Industry pack not found")
    return pack


# --- Demo Data Seeding -------------------------------------------------------


@router.post("/demo/seed")
async def seed_demo(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Seed demo organization, dashboards, KPIs, and ETL pipeline for pilot.

    Blocked in production unless SEED_DEMO_DATA=true is explicitly set.
    """
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    app_env = os.getenv("APP_ENV", "development").lower()
    seed_enabled = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")
    if app_env == "production" and not seed_enabled:
        raise HTTPException(
            status_code=403,
            detail="Demo data seeding is disabled in production. "
            "Set SEED_DEMO_DATA=true to enable for pilot deployments.",
        )
    if is_demo_seeded(db):
        return {"message": "Demo data already seeded", "already_seeded": True}
    result = seed_demo_data(db)
    return {"message": "Demo data seeded successfully", "created": result}


@router.get("/demo/status")
async def demo_status(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check if demo data has been seeded."""
    return {"is_seeded": is_demo_seeded(db)}


# --- Subscription & Licensing ------------------------------------------------


@router.get("/subscription/plans")
async def list_plans():
    """List all available subscription plans."""
    return [
        {
            "key": key,
            "name": plan["name"],
            "description": plan["description"],
            "trial_days": plan["trial_days"],
            "limits": {
                "max_users": plan["max_users"],
                "max_dashboards": plan["max_dashboards"],
                "max_pipelines": plan["max_pipelines"],
                "max_ai_queries_per_month": plan["max_ai_queries_per_month"],
                "max_upload_mb": plan["max_upload_mb"],
            },
            "features": plan["features"],
        }
        for key, plan in PLAN_DEFINITIONS.items()
    ]


@router.get("/subscription/current")
async def get_current_subscription(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the current organization's subscription state."""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization configured")
    svc = SubscriptionService(db)
    svc.check_trial_expired(org_id)
    return svc.get_limits(org_id)


@router.post("/subscription/upgrade")
async def upgrade_subscription(
    plan: str = Query(
        ..., description="Plan key: free_trial, starter, professional, enterprise, government"
    ),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upgrade the organization to a new plan."""
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if plan not in PLAN_DEFINITIONS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization configured")
    svc = SubscriptionService(db)
    sub = svc.upgrade_plan(org_id, plan)
    return {
        "message": f"Upgraded to {PLAN_DEFINITIONS[plan]['name']}",
        "plan": sub.plan,
        "status": sub.status,
        "limits": svc.get_limits(org_id),
    }


@router.post("/subscription/cancel")
async def cancel_subscription(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel the organization's subscription."""
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization configured")
    svc = SubscriptionService(db)
    svc.cancel_subscription(org_id)
    return {"message": "Subscription canceled"}


@router.get("/subscription/features")
async def list_all_features():
    """List all available feature keys."""
    return {"features": ALL_FEATURES}


@router.get("/subscription/feature-check")
async def check_feature(
    feature: str = Query(..., description="Feature key to check"),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check if the current organization has access to a feature."""
    org_id = current_user.get("organization_id")
    if not org_id:
        return {"has_access": False, "reason": "No organization configured"}
    svc = SubscriptionService(db)
    has_access = svc.has_feature(org_id, feature)
    return {"has_access": has_access, "feature": feature}


@router.put("/subscription/feature-flag")
async def set_feature_flag(
    feature: str = Query(..., description="Feature key"),
    enabled: bool = Query(True, description="Enable or disable"),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Set a feature flag override for the organization."""
    if "super_admin" not in current_user["roles"] and "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization configured")
    svc = SubscriptionService(db)
    svc.set_feature_flag(org_id, feature, enabled)
    return {"message": f"Feature '{feature}' {'enabled' if enabled else 'disabled'}"}


# --- Backup management -------------------------------------------------------


@router.post("/backups")
async def trigger_backup(current_user: dict = Depends(get_current_user)):
    """Trigger an on-demand backup of the database and configuration.

    Requires admin or super_admin role.
    """
    if "admin" not in current_user["roles"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = BackupService().create_backup()
    return success_response(result, "Backup created")


@router.get("/backups")
async def list_backups(current_user: dict = Depends(get_current_user)):
    """List available backups.

    Requires admin or super_admin role.
    """
    if "admin" not in current_user["roles"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    backups = BackupService().list_backups()
    return success_response(backups)
