"""FastAPI routes for Plugin System, Marketplace, and Industry Packages."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from ecosystem.plugin_models import IndustryPackage, Plugin, PluginInstallation
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

plugin_router = APIRouter(prefix="/marketplace", tags=["Platform / Marketplace"])


# ─── Schemas ───────────────────────────────────────────────


class PluginPublish(BaseModel):
    plugin_id: str
    name: str
    version: str = "1.0.0"
    author: str
    description: str | None = None
    category: str  # connector, dashboard_template, ai_agent, industry_solution, data_processor
    icon: str | None = None
    permissions: list[str] | None = None
    dependencies: list[str] | None = None
    config_schema: dict | None = None
    tags: list[str] | None = None


class PluginInstall(BaseModel):
    configuration: dict | None = None


# ─── Marketplace Browsing ──────────────────────────────────


@plugin_router.get("/plugins")
async def list_plugins(
    category: str | None = Query(None),
    search: str | None = Query(None),
    featured: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Browse the plugin marketplace."""
    query = select(Plugin)
    if category:
        query = query.where(Plugin.category == category)
    if featured:
        query = query.where(Plugin.is_featured == True)  # noqa: E712
    if search:
        query = query.where(Plugin.name.ilike(f"%{search}%"))
    plugins = db.execute(query.order_by(Plugin.install_count.desc()).limit(limit)).scalars().all()
    return success_response(
        [
            {
                "id": p.id,
                "plugin_id": p.plugin_id,
                "name": p.name,
                "version": p.version,
                "author": p.author,
                "description": p.description,
                "category": p.category,
                "icon": p.icon,
                "is_verified": p.is_verified,
                "is_featured": p.is_featured,
                "install_count": p.install_count,
                "rating": p.rating,
                "tags": p.tags,
            }
            for p in plugins
        ]
    )


@plugin_router.get("/plugins/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get details of a specific plugin."""
    plugin = db.execute(select(Plugin).where(Plugin.plugin_id == plugin_id)).scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return success_response(
        {
            "id": plugin.id,
            "plugin_id": plugin.plugin_id,
            "name": plugin.name,
            "version": plugin.version,
            "author": plugin.author,
            "description": plugin.description,
            "category": plugin.category,
            "icon": plugin.icon,
            "permissions": plugin.permissions,
            "dependencies": plugin.dependencies,
            "config_schema": plugin.config_schema,
            "is_verified": plugin.is_verified,
            "is_featured": plugin.is_featured,
            "install_count": plugin.install_count,
            "rating": plugin.rating,
            "tags": plugin.tags,
            "screenshots": plugin.screenshots,
        }
    )


@plugin_router.post("/plugins")
async def publish_plugin(
    body: PluginPublish,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Publish a plugin to the marketplace (admin only)."""
    if "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Only admins can publish plugins")

    existing = db.execute(
        select(Plugin).where(Plugin.plugin_id == body.plugin_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Plugin with this ID already exists")

    plugin = Plugin(
        plugin_id=body.plugin_id,
        name=body.name,
        version=body.version,
        author=body.author,
        description=body.description,
        category=body.category,
        icon=body.icon,
        permissions=body.permissions,
        dependencies=body.dependencies,
        config_schema=body.config_schema,
        tags=body.tags,
        is_verified=True,
    )
    db.add(plugin)
    db.flush()
    db.commit()
    return success_response({"id": plugin.id, "plugin_id": plugin.plugin_id}, "Plugin published")


# ─── Installation Management ───────────────────────────────


@plugin_router.post("/plugins/{plugin_id_str}/install")
async def install_plugin(
    plugin_id_str: str,
    body: PluginInstall,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Install a plugin for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    plugin = db.execute(
        select(Plugin).where(Plugin.plugin_id == plugin_id_str)
    ).scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    existing = db.execute(
        select(PluginInstallation).where(
            PluginInstallation.plugin_id == plugin_id_str,
            PluginInstallation.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Plugin already installed")

    installation = PluginInstallation(
        organization_id=org_id,
        plugin_id=plugin_id_str,
        version=plugin.version,
        status="enabled",
        configuration=body.configuration,
        installed_by=current_user["id"],
    )
    db.add(installation)
    db.execute(
        update(Plugin)
        .where(Plugin.plugin_id == plugin_id_str)
        .values(install_count=Plugin.install_count + 1)
    )
    db.commit()
    return success_response(
        {"id": installation.id, "status": installation.status}, "Plugin installed"
    )


@plugin_router.get("/installations")
async def list_installations(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List installed plugins for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    installations = (
        db.execute(
            select(PluginInstallation)
            .where(PluginInstallation.organization_id == org_id)
            .order_by(PluginInstallation.installed_at.desc())
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": i.id,
                "plugin_id": i.plugin_id,
                "version": i.version,
                "status": i.status,
                "configuration": i.configuration,
                "installed_at": str(i.installed_at) if i.installed_at else None,
            }
            for i in installations
        ]
    )


@plugin_router.post("/installations/{installation_id}/enable")
async def enable_plugin(
    installation_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Enable an installed plugin."""
    org_id = get_current_organization_id(current_user, db)
    inst = db.execute(
        select(PluginInstallation).where(
            PluginInstallation.id == installation_id,
            PluginInstallation.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")
    db.execute(
        update(PluginInstallation)
        .where(PluginInstallation.id == installation_id)
        .values(status="enabled")
    )
    db.commit()
    return success_response(None, "Plugin enabled")


@plugin_router.post("/installations/{installation_id}/disable")
async def disable_plugin(
    installation_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Disable an installed plugin."""
    org_id = get_current_organization_id(current_user, db)
    inst = db.execute(
        select(PluginInstallation).where(
            PluginInstallation.id == installation_id,
            PluginInstallation.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")
    db.execute(
        update(PluginInstallation)
        .where(PluginInstallation.id == installation_id)
        .values(status="disabled")
    )
    db.commit()
    return success_response(None, "Plugin disabled")


@plugin_router.delete("/installations/{installation_id}")
async def uninstall_plugin(
    installation_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Uninstall a plugin."""
    org_id = get_current_organization_id(current_user, db)
    inst = db.execute(
        select(PluginInstallation).where(
            PluginInstallation.id == installation_id,
            PluginInstallation.organization_id == org_id,
        )
    ).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")
    db.execute(
        update(Plugin)
        .where(Plugin.plugin_id == inst.plugin_id)
        .values(install_count=Plugin.install_count - 1)
    )
    db.delete(inst)
    db.commit()
    return success_response(None, "Plugin uninstalled")


# ─── Industry Solution Packages ────────────────────────────


@plugin_router.get("/industry-packages")
async def list_industry_packages(
    industry: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Browse industry solution packages."""
    query = select(IndustryPackage).where(IndustryPackage.is_available == True)  # noqa: E712
    if industry:
        query = query.where(IndustryPackage.industry == industry)
    packages = db.execute(query.order_by(IndustryPackage.industry)).scalars().all()
    return success_response(
        [
            {
                "id": p.id,
                "package_id": p.package_id,
                "industry": p.industry,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "is_africa_optimized": p.is_africa_optimized,
            }
            for p in packages
        ]
    )


@plugin_router.get("/industry-packages/{package_id_str}")
async def get_industry_package(
    package_id_str: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get details of an industry package."""
    pkg = db.execute(
        select(IndustryPackage).where(IndustryPackage.package_id == package_id_str)
    ).scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return success_response(
        {
            "id": pkg.id,
            "package_id": pkg.package_id,
            "industry": pkg.industry,
            "name": pkg.name,
            "description": pkg.description,
            "version": pkg.version,
            "dataset_templates": pkg.dataset_templates,
            "dashboard_templates": pkg.dashboard_templates,
            "kpi_templates": pkg.kpi_templates,
            "ai_insight_templates": pkg.ai_insight_templates,
            "ml_model_templates": pkg.ml_model_templates,
            "is_africa_optimized": pkg.is_africa_optimized,
        }
    )


@plugin_router.post("/industry-packages/{package_id_str}/install")
async def install_industry_package(
    package_id_str: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Install an industry package — creates dashboards, KPIs, and templates for the organization."""
    org_id = get_current_organization_id(current_user, db)
    pkg = db.execute(
        select(IndustryPackage).where(IndustryPackage.package_id == package_id_str)
    ).scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    created = {"dashboards": 0, "kpis": 0}

    # Create dashboards from templates
    if pkg.dashboard_templates:
        from analytics.models import Dashboard

        for tmpl in pkg.dashboard_templates:
            dash = Dashboard(
                organization_id=org_id,
                owner_id=current_user["id"],
                name=tmpl.get("name", "Industry Dashboard"),
                description=tmpl.get("description", ""),
                theme=pkg.industry,
                layout=tmpl.get("layout", {}),
                is_public=False,
            )
            db.add(dash)
            db.flush()
            created["dashboards"] += 1

    # Create KPIs from templates
    if pkg.kpi_templates:
        from analytics.models import KPI

        for tmpl in pkg.kpi_templates:
            kpi = KPI(
                organization_id=org_id,
                owner_id=current_user["id"],
                name=tmpl.get("name", "KPI"),
                description=tmpl.get("description", ""),
                category=tmpl.get("category", "general"),
                formula=tmpl.get("formula", ""),
                target_value=tmpl.get("target_value"),
                unit=tmpl.get("unit", ""),
                is_active=True,
            )
            db.add(kpi)
            db.flush()
            created["kpis"] += 1

    db.commit()
    return success_response(
        created,
        f"Industry package installed: {created['dashboards']} dashboards, {created['kpis']} KPIs created",
    )
