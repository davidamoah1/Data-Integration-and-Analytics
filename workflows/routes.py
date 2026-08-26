"""REST API routes for the enterprise workflow engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.response import success_response
from workflows.schemas import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionUpdate,
    WorkflowExecutionCreate,
    WorkflowExecutionResponse,
    WorkflowLineageResponse,
    WorkflowTemplateCreate,
    WorkflowTemplateResponse,
    WorkflowVersionCreate,
    WorkflowVersionResponse,
)
from workflows.service import WorkflowService

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


class CloneWorkflowRequest(BaseModel):
    name: str


class ImportWorkflowRequest(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    nodes: list
    edges: list
    config: dict | None = None


@router.get("/node-types")
async def list_node_types(current_user: dict = Depends(get_current_user)):
    """Return all registered workflow node types."""
    from workflows.nodes import list_node_types

    return success_response(list_node_types())


# --- Workflow definitions ----------------------------------------------------


@router.get("", response_model=list[WorkflowDefinitionResponse])
async def list_workflows(
    category: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.list_definitions(category=category)


@router.post("", response_model=WorkflowDefinitionResponse, status_code=201)
async def create_workflow(
    request: WorkflowDefinitionCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    service = WorkflowService(db, current_user)
    wf = service.create_definition(request)
    log_audit_event(
        db=db,
        action="workflow.create",
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        resource_type="workflow_definition",
        resource_id=wf.id,
    )
    db.commit()
    return wf


@router.get("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.get_definition(workflow_id)


@router.put("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow(
    workflow_id: int,
    request: WorkflowDefinitionUpdate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    service = WorkflowService(db, current_user)
    wf = service.update_definition(workflow_id, request)
    log_audit_event(
        db=db,
        action="workflow.update",
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        resource_type="workflow_definition",
        resource_id=workflow_id,
    )
    db.commit()
    return wf


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.delete")),
):
    service = WorkflowService(db, current_user)
    service.delete_definition(workflow_id)
    log_audit_event(
        db=db,
        action="workflow.delete",
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        resource_type="workflow_definition",
        resource_id=workflow_id,
    )
    db.commit()
    return success_response(None, "Workflow deleted")


# --- Versions ----------------------------------------------------------------


@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=201)
async def create_version(
    workflow_id: int,
    request: WorkflowVersionCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    service = WorkflowService(db, current_user)
    version = service.create_version(workflow_id, request)
    return version


@router.get("/{workflow_id}/versions", response_model=list[WorkflowVersionResponse])
async def list_versions(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    wf = service.get_definition(workflow_id)
    return wf.versions


@router.post("/{workflow_id}/versions/{version_id}/publish", response_model=WorkflowVersionResponse)
async def publish_version(
    workflow_id: int,
    version_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.publish")),
):
    service = WorkflowService(db, current_user)
    version = service.publish_version(workflow_id, version_id)
    return version


@router.post("/{workflow_id}/versions/{version_id}/archive", response_model=WorkflowVersionResponse)
async def archive_version(
    workflow_id: int,
    version_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.publish")),
):
    service = WorkflowService(db, current_user)
    version = service.archive_version(workflow_id, version_id)
    return version


# --- Execution ---------------------------------------------------------------


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    request: WorkflowExecutionCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.execute")),
):
    service = WorkflowService(db, current_user)
    execution = service.execute_workflow(workflow_id, request)
    return execution


@router.get("/{workflow_id}/executions", response_model=list[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: int,
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    filters = {"workflow_id": workflow_id, "status": status, "limit": limit, "offset": offset}
    return service.list_executions(filters)


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.get_execution(execution_id)


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowExecutionResponse)
async def cancel_execution(
    execution_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.execute")),
):
    service = WorkflowService(db, current_user)
    return service.cancel_execution(execution_id)


# --- Execution history -------------------------------------------------------


@router.get("/executions", response_model=list[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: int | None = Query(None),
    status: str | None = Query(None),
    trigger_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    filters = {
        "workflow_id": workflow_id,
        "status": status,
        "trigger_type": trigger_type,
        "limit": limit,
        "offset": offset,
    }
    return service.list_executions(filters)


# --- Lineage -----------------------------------------------------------------


@router.get("/executions/{execution_id}/lineage", response_model=list[WorkflowLineageResponse])
async def get_lineage(
    execution_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.get_lineage(execution_id)


# --- Templates ---------------------------------------------------------------


@router.get("/templates", response_model=list[WorkflowTemplateResponse])
async def list_templates(
    category: str | None = Query(None),
    include_public: bool = Query(True),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.list_templates(include_public=include_public, category=category)


@router.post("/templates", response_model=WorkflowTemplateResponse, status_code=201)
async def create_template(
    request: WorkflowTemplateCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    service = WorkflowService(db, current_user)
    return service.create_template(request)


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = WorkflowService(db, current_user)
    return service.get_template(template_id)


@router.post(
    "/templates/{template_id}/import", response_model=WorkflowDefinitionResponse, status_code=201
)
async def import_template(
    template_id: int,
    request: ImportWorkflowRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    """Import a public or owned template as a new workflow."""
    service = WorkflowService(db, current_user)
    template = service.get_template(template_id)
    from workflows.schemas import (
        WorkflowDefinitionCreate,
        WorkflowEdgeDefinition,
        WorkflowNodeDefinition,
    )

    wf_request = WorkflowDefinitionCreate(
        name=request.name,
        description=request.description,
        category=request.category or template.category,
        nodes=[WorkflowNodeDefinition(**n) for n in template.nodes],
        edges=[WorkflowEdgeDefinition(**e) for e in template.edges],
        config=request.config or template.config,
    )
    wf = service.create_definition(wf_request)
    return wf


# --- Clone / export ----------------------------------------------------------


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinitionResponse, status_code=201)
async def clone_workflow(
    workflow_id: int,
    request: CloneWorkflowRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.write")),
):
    service = WorkflowService(db, current_user)
    return service.clone_workflow(workflow_id, request.name)


@router.get("/{workflow_id}/export")
async def export_workflow(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export the latest version of a workflow as JSON."""
    service = WorkflowService(db, current_user)
    wf = service.get_definition(workflow_id)
    latest = wf.versions[0] if wf.versions else None
    return success_response(
        {
            "name": wf.name,
            "description": wf.description,
            "category": wf.category,
            "nodes": latest.nodes if latest else [],
            "edges": latest.edges if latest else [],
            "config": latest.config if latest else {},
        }
    )


# --- Job queue ---------------------------------------------------------------


@router.get("/jobs")
async def list_jobs(
    status: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("workflows.read")),
):
    service = WorkflowService(db, current_user)
    return success_response(
        [
            {"id": j.id, "execution_id": j.execution_id, "status": j.status}
            for j in service.list_jobs(status)
        ]
    )


# Router-level error handlers are not supported by APIRouter; global
# exception handlers in api/main.py translate shared exceptions.
