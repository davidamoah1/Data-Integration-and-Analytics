"""Analytics API routes — dashboards, KPIs, and alerts."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from analytics.models import (
    AnalyticsAlert,
    Dashboard,
    DashboardFavorite,
    DashboardWidget,
    KPI,
    KPIHistory,
)
from analytics.schemas import (
    AlertCreate,
    AlertResponse,
    DashboardCreate,
    DashboardUpdate,
    KPICreate,
    KPIRecord,
    WidgetCreate,
)
from shared.dependencies import get_current_user
from shared.database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# --- Dashboards --------------------------------------------------------------


@router.get("/dashboards")
async def list_dashboards(
    include_public: bool = Query(True),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Dashboard).filter(Dashboard.owner_id == current_user["id"])
    if include_public:
        query = query.union(
            db.query(Dashboard).filter(Dashboard.is_public.is_(True))
        )
    dashboards = query.order_by(Dashboard.updated_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "theme": d.theme,
            "is_public": d.is_public,
            "version": d.version,
            "owner_id": d.owner_id,
            "created_at": str(d.created_at) if d.created_at else None,
            "updated_at": str(d.updated_at) if d.updated_at else None,
        }
        for d in dashboards
    ]


@router.post("/dashboards")
async def create_dashboard(
    body: DashboardCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = Dashboard(
        owner_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        name=body.name,
        description=body.description,
        theme=body.theme,
        layout=body.layout,
        is_public=body.is_public,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return {"id": dashboard.id, "name": dashboard.name, "version": dashboard.version}


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if (
        dashboard.owner_id != current_user["id"]
        and not dashboard.is_public
        and "super_admin" not in current_user["roles"]
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    widgets = (
        db.query(DashboardWidget)
        .filter(DashboardWidget.dashboard_id == dashboard_id)
        .all()
    )
    return {
        "id": dashboard.id,
        "name": dashboard.name,
        "description": dashboard.description,
        "theme": dashboard.theme,
        "layout": dashboard.layout,
        "is_public": dashboard.is_public,
        "version": dashboard.version,
        "widgets": [
            {
                "id": w.id,
                "widget_type": w.widget_type,
                "title": w.title,
                "configuration": w.configuration,
                "position": w.position,
                "group_name": w.group_name,
            }
            for w in widgets
        ],
    }


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: int,
    body: DashboardUpdate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dashboard.owner_id != current_user["id"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Only the owner can update")
    if body.name is not None:
        dashboard.name = body.name
    if body.description is not None:
        dashboard.description = body.description
    if body.theme is not None:
        dashboard.theme = body.theme
    if body.layout is not None:
        dashboard.layout = body.layout
    if body.is_public is not None:
        dashboard.is_public = body.is_public
    dashboard.version += 1
    db.commit()
    db.refresh(dashboard)
    return {"id": dashboard.id, "name": dashboard.name, "version": dashboard.version}


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dashboard.owner_id != current_user["id"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete")
    db.query(DashboardWidget).filter(
        DashboardWidget.dashboard_id == dashboard_id
    ).delete()
    db.query(DashboardFavorite).filter(
        DashboardFavorite.dashboard_id == dashboard_id
    ).delete()
    db.delete(dashboard)
    db.commit()
    return {"message": "Dashboard deleted"}


# --- Widgets -----------------------------------------------------------------


@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: int,
    body: WidgetCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dashboard.owner_id != current_user["id"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Only the owner can add widgets")
    widget = DashboardWidget(
        dashboard_id=dashboard_id,
        widget_type=body.widget_type,
        title=body.title,
        configuration=body.configuration,
        position=body.position,
        group_name=body.group_name,
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return {"id": widget.id, "widget_type": widget.widget_type, "title": widget.title}


@router.delete("/dashboards/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(
    dashboard_id: int,
    widget_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dashboard.owner_id != current_user["id"] and "super_admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Only the owner can remove widgets")
    widget = (
        db.query(DashboardWidget)
        .filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.dashboard_id == dashboard_id,
        )
        .first()
    )
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    db.delete(widget)
    db.commit()
    return {"message": "Widget removed"}


# --- Favorites ---------------------------------------------------------------


@router.post("/dashboards/{dashboard_id}/favorite")
async def toggle_favorite(
    dashboard_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    existing = (
        db.query(DashboardFavorite)
        .filter(
            DashboardFavorite.dashboard_id == dashboard_id,
            DashboardFavorite.user_id == current_user["id"],
        )
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    fav = DashboardFavorite(dashboard_id=dashboard_id, user_id=current_user["id"])
    db.add(fav)
    db.commit()
    return {"is_favorite": True}


# --- KPIs --------------------------------------------------------------------


@router.get("/kpis")
async def list_kpis(
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(KPI)
    if category:
        query = query.filter(KPI.category == category)
    if is_active is not None:
        query = query.filter(KPI.is_active == is_active)
    kpis = query.order_by(KPI.created_at.desc()).all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "description": k.description,
            "category": k.category,
            "formula": k.formula,
            "target_value": k.target_value,
            "warning_threshold": k.warning_threshold,
            "critical_threshold": k.critical_threshold,
            "unit": k.unit,
            "is_active": k.is_active,
        }
        for k in kpis
    ]


@router.post("/kpis")
async def create_kpi(
    body: KPICreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    kpi = KPI(
        owner_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        name=body.name,
        description=body.description,
        category=body.category,
        formula=body.formula,
        target_value=body.target_value,
        warning_threshold=body.warning_threshold,
        critical_threshold=body.critical_threshold,
        unit=body.unit,
    )
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return {"id": kpi.id, "name": kpi.name}


@router.get("/kpis/{kpi_id}")
async def get_kpi(
    kpi_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    kpi = db.query(KPI).filter(KPI.id == kpi_id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    history = (
        db.query(KPIHistory)
        .filter(KPIHistory.kpi_id == kpi_id)
        .order_by(KPIHistory.recorded_at.desc())
        .limit(50)
        .all()
    )
    return {
        "id": kpi.id,
        "name": kpi.name,
        "description": kpi.description,
        "category": kpi.category,
        "formula": kpi.formula,
        "target_value": kpi.target_value,
        "warning_threshold": kpi.warning_threshold,
        "critical_threshold": kpi.critical_threshold,
        "unit": kpi.unit,
        "is_active": kpi.is_active,
        "history": [
            {
                "id": h.id,
                "value": h.value,
                "status": h.status,
                "recorded_at": str(h.recorded_at) if h.recorded_at else None,
            }
            for h in history
        ],
    }


@router.post("/kpis/{kpi_id}/record")
async def record_kpi_value(
    kpi_id: int,
    body: KPIRecord,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    kpi = db.query(KPI).filter(KPI.id == kpi_id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    status_label = "healthy"
    if kpi.critical_threshold is not None and body.value <= kpi.critical_threshold:
        status_label = "critical"
    elif kpi.warning_threshold is not None and body.value <= kpi.warning_threshold:
        status_label = "warning"
    record = KPIHistory(kpi_id=kpi_id, value=body.value, status=status_label)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "value": record.value, "status": record.status}


@router.delete("/kpis/{kpi_id}")
async def delete_kpi(
    kpi_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    kpi = db.query(KPI).filter(KPI.id == kpi_id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    db.query(KPIHistory).filter(KPIHistory.kpi_id == kpi_id).delete()
    db.delete(kpi)
    db.commit()
    return {"message": "KPI deleted"}


# --- Alerts ------------------------------------------------------------------


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    is_acknowledged: bool | None = Query(None),
    alert_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(AnalyticsAlert)
    if is_acknowledged is not None:
        if is_acknowledged:
            query = query.filter(AnalyticsAlert.acknowledged_by.isnot(None))
        else:
            query = query.filter(AnalyticsAlert.acknowledged_by.is_(None))
    if alert_type:
        query = query.filter(AnalyticsAlert.alert_type == alert_type)
    alerts = query.order_by(AnalyticsAlert.created_at.desc()).limit(limit).all()
    return [
        AlertResponse(
            id=a.id,
            alert_type=a.alert_type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            source_type=a.source_type,
            source_id=a.source_id,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    body: AlertCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    alert = AnalyticsAlert(
        organization_id=current_user.get("organization_id"),
        alert_type=body.alert_type,
        severity=body.severity,
        title=body.title,
        message=body.message,
        source_type=body.source_type,
        source_id=body.source_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        source_type=alert.source_type,
        source_id=alert.source_id,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    alert = db.query(AnalyticsAlert).filter(AnalyticsAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged_by = current_user["id"]
    alert.acknowledged_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"message": "Alert acknowledged"}
