"""FastAPI routes for the Enterprise Connector Framework."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from connectors.base import ConnectorRegistry
from connectors.models import Connector, ConnectorExecution
from connectors.schemas import (
    ConnectorCreate,
    ConnectorUpdate,
)
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/api/connectors", tags=["Connectors"])

# Ensure built-in connectors are registered
import connectors.builtin  # noqa: F401, E402


@router.get("/types")
async def list_connector_types(
    category: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all available connector types."""
    types = ConnectorRegistry.list_types()
    if category:
        types = [t for t in types if t["category"] == category]
    return success_response(types)


@router.get("/types/africa")
async def list_africa_connectors(
    current_user: dict = Depends(get_current_user),
):
    """List Africa-first connector types."""
    types = ConnectorRegistry.list_types()
    return success_response([t for t in types if t.get("is_africa_first")])


@router.get("")
async def list_connectors(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List connectors for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    connectors = (
        db.execute(
            select(Connector)
            .where(Connector.organization_id == org_id)
            .order_by(Connector.created_at.desc())
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": c.id,
                "name": c.name,
                "connector_type": c.connector_type,
                "category": c.category,
                "description": c.description,
                "status": c.status,
                "last_tested_at": str(c.last_tested_at) if c.last_tested_at else None,
                "is_public": c.is_public,
                "created_at": str(c.created_at) if c.created_at else None,
            }
            for c in connectors
        ]
    )


@router.post("")
async def create_connector(
    body: ConnectorCreate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Create a new connector instance."""
    org_id = get_current_organization_id(current_user, db)
    connector_type = ConnectorRegistry.get(body.connector_type)
    if not connector_type:
        raise HTTPException(
            status_code=400, detail=f"Unknown connector type: {body.connector_type}"
        )

    connector = Connector(
        organization_id=org_id,
        name=body.name,
        connector_type=body.connector_type,
        category=body.category,
        description=body.description,
        configuration=body.configuration,
        auth_config=body.auth_config,
        is_public=body.is_public,
        created_by=current_user["id"],
    )
    db.add(connector)
    db.flush()
    db.commit()
    return success_response(
        {
            "id": connector.id,
            "name": connector.name,
            "connector_type": connector.connector_type,
            "status": connector.status,
        },
        "Connector created",
    )


@router.get("/{connector_id}")
async def get_connector(
    connector_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get a specific connector."""
    org_id = get_current_organization_id(current_user, db)
    connector = db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.organization_id == org_id)
    ).scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    return success_response(
        {
            "id": connector.id,
            "name": connector.name,
            "connector_type": connector.connector_type,
            "category": connector.category,
            "description": connector.description,
            "configuration": connector.configuration,
            "status": connector.status,
            "last_tested_at": str(connector.last_tested_at) if connector.last_tested_at else None,
            "last_test_result": connector.last_test_result,
            "is_public": connector.is_public,
            "created_at": str(connector.created_at) if connector.created_at else None,
        }
    )


@router.put("/{connector_id}")
async def update_connector(
    connector_id: int,
    body: ConnectorUpdate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Update a connector."""
    org_id = get_current_organization_id(current_user, db)
    connector = db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.organization_id == org_id)
    ).scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if kwargs:
        db.execute(update(Connector).where(Connector.id == connector_id).values(**kwargs))
        db.flush()
    db.commit()
    return success_response({"id": connector_id}, "Connector updated")


@router.delete("/{connector_id}")
async def delete_connector(
    connector_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Delete a connector."""
    org_id = get_current_organization_id(current_user, db)
    connector = db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.organization_id == org_id)
    ).scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    db.delete(connector)
    db.commit()
    return success_response(None, "Connector deleted")


@router.post("/{connector_id}/test")
async def test_connector(
    connector_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Test a connector's connection."""
    org_id = get_current_organization_id(current_user, db)
    connector = db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.organization_id == org_id)
    ).scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    instance = ConnectorRegistry.create(
        connector.connector_type,
        configuration=connector.configuration or {},
        auth_config=connector.auth_config or {},
    )
    if not instance:
        raise HTTPException(status_code=400, detail="Connector type not available")

    result = instance.test_connection()
    db.execute(
        update(Connector)
        .where(Connector.id == connector_id)
        .values(
            status="active" if result["success"] else "error",
            last_tested_at=datetime.now(timezone.utc),
            last_test_result=result,
        )
    )
    db.commit()
    return success_response(result)


@router.post("/{connector_id}/extract")
async def extract_data(
    connector_id: int,
    query: dict | None = None,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Extract data from a connector."""
    org_id = get_current_organization_id(current_user, db)
    connector = db.execute(
        select(Connector).where(Connector.id == connector_id, Connector.organization_id == org_id)
    ).scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    instance = ConnectorRegistry.create(
        connector.connector_type,
        configuration=connector.configuration or {},
        auth_config=connector.auth_config or {},
    )
    if not instance:
        raise HTTPException(status_code=400, detail="Connector type not available")

    execution = ConnectorExecution(
        connector_id=connector_id,
        organization_id=org_id,
        status="running",
    )
    db.add(execution)
    db.flush()

    try:
        df = instance.extract_data(query)
        db.execute(
            update(ConnectorExecution)
            .where(ConnectorExecution.id == execution.id)
            .values(
                status="success",
                rows_extracted=len(df),
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        return success_response(
            {
                "execution_id": execution.id,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.head(100).to_dict(orient="records"),
            }
        )
    except Exception as e:
        db.execute(
            update(ConnectorExecution)
            .where(ConnectorExecution.id == execution.id)
            .values(
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}") from None


@router.get("/{connector_id}/executions")
async def list_executions(
    connector_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List execution history for a connector."""
    org_id = get_current_organization_id(current_user, db)
    executions = (
        db.execute(
            select(ConnectorExecution)
            .where(
                ConnectorExecution.connector_id == connector_id,
                ConnectorExecution.organization_id == org_id,
            )
            .order_by(ConnectorExecution.started_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return success_response(
        [
            {
                "id": e.id,
                "status": e.status,
                "rows_extracted": e.rows_extracted,
                "error_message": e.error_message,
                "started_at": str(e.started_at) if e.started_at else None,
                "completed_at": str(e.completed_at) if e.completed_at else None,
            }
            for e in executions
        ]
    )
