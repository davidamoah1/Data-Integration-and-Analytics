"""Workflow service layer with tenant isolation, versioning, and orchestration."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from audit.service import log_audit_event
from notifications.models import Notification
from shared.exceptions import AuthorizationError, NotFoundError
from shared.tenant import is_super_admin
from workflows.engine import WorkflowEngine
from workflows.models import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowJob,
    WorkflowLineage,
    WorkflowTemplate,
    WorkflowVersion,
)


class WorkflowService:
    """Business logic for workflow definitions, versions, executions, and templates."""

    def __init__(self, db: DbSession, current_user: dict):
        self.db = db
        self.current_user = current_user
        self.engine = WorkflowEngine(db)

    # --- Tenant helpers -------------------------------------------------------

    def _org_id(self) -> int | None:
        return self.current_user.get("organization_id")

    def _notify_user(self, user_id: int, subject: str, body: str) -> None:
        notification = Notification(
            user_id=user_id,
            channel="in_app",
            subject=subject,
            body=body,
            status="pending",
        )
        self.db.add(notification)

    def _ensure_org_access(self, resource_org_id: int | None) -> None:
        if is_super_admin(self.current_user):
            return
        if resource_org_id != self._org_id():
            raise AuthorizationError("Access denied for this resource.")

    def _query_org_scoped(self, model):
        query = self.db.query(model)
        if not is_super_admin(self.current_user):
            query = query.filter(model.organization_id == self._org_id())
        return query

    # --- Definitions ----------------------------------------------------------

    def create_definition(self, request) -> WorkflowDefinition:
        from workflows.schemas import WorkflowDefinitionCreate

        req: WorkflowDefinitionCreate = request
        wf = WorkflowDefinition(
            organization_id=self._org_id(),
            created_by=self.current_user["id"],
            name=req.name,
            description=req.description,
            category=req.category,
        )
        self.db.add(wf)
        self.db.commit()
        self.db.refresh(wf)
        # Create initial draft version
        version = WorkflowVersion(
            workflow_id=wf.id,
            version_number=1,
            status="draft",
            nodes=[n.model_dump() for n in req.nodes],
            edges=[e.model_dump() for e in req.edges],
            config=req.config,
            created_by=self.current_user["id"],
        )
        self.db.add(version)
        self.db.commit()
        return wf

    def list_definitions(self, category: str | None = None) -> list[WorkflowDefinition]:
        query = self._query_org_scoped(WorkflowDefinition).filter(
            WorkflowDefinition.is_deleted == 0
        )
        if category:
            query = query.filter(WorkflowDefinition.category == category)
        return query.order_by(WorkflowDefinition.updated_at.desc()).all()

    def get_definition(self, workflow_id: int) -> WorkflowDefinition:
        wf = (
            self._query_org_scoped(WorkflowDefinition)
            .filter(WorkflowDefinition.id == workflow_id, WorkflowDefinition.is_deleted == 0)
            .first()
        )
        if not wf:
            raise NotFoundError("Workflow not found")
        return wf

    def update_definition(self, workflow_id: int, request) -> WorkflowDefinition:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        if request.name is not None:
            wf.name = request.name
        if request.description is not None:
            wf.description = request.description
        if request.category is not None:
            wf.category = request.category
        if request.is_active is not None:
            wf.is_active = int(request.is_active)
        self.db.commit()
        self.db.refresh(wf)
        return wf

    def delete_definition(self, workflow_id: int) -> None:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        wf.is_deleted = 1
        self.db.commit()

    # --- Versions --------------------------------------------------------------

    def create_version(self, workflow_id: int, request) -> WorkflowVersion:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        max_version = (
            self.db.query(func.max(WorkflowVersion.version_number))
            .filter(WorkflowVersion.workflow_id == workflow_id)
            .scalar()
            or 0
        )
        version = WorkflowVersion(
            workflow_id=workflow_id,
            version_number=max_version + 1,
            status="draft",
            nodes=[n.model_dump() for n in request.nodes],
            edges=[e.model_dump() for e in request.edges],
            config=request.config,
            created_by=self.current_user["id"],
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version(self, version_id: int) -> WorkflowVersion:
        version = self.db.query(WorkflowVersion).filter(WorkflowVersion.id == version_id).first()
        if not version:
            raise NotFoundError("Version not found")
        wf = self.get_definition(version.workflow_id)
        self._ensure_org_access(wf.organization_id)
        return version

    def publish_version(self, workflow_id: int, version_id: int) -> WorkflowVersion:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        version = (
            self.db.query(WorkflowVersion)
            .filter(WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == workflow_id)
            .first()
        )
        if not version:
            raise NotFoundError("Version not found")
        # Archive previously published versions
        self.db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.status == "published"
        ).update({"status": "archived"})
        version.status = "published"
        wf.published_version_id = version.id
        self.db.commit()
        self.db.refresh(version)
        return version

    def archive_version(self, workflow_id: int, version_id: int) -> WorkflowVersion:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        version = (
            self.db.query(WorkflowVersion)
            .filter(WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == workflow_id)
            .first()
        )
        if not version:
            raise NotFoundError("Version not found")
        version.status = "archived"
        if wf.published_version_id == version.id:
            wf.published_version_id = None
        self.db.commit()
        self.db.refresh(version)
        return version

    # --- Executions ------------------------------------------------------------

    def execute_workflow(self, workflow_id: int, request) -> WorkflowExecution:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        version_id = request.version_id or wf.published_version_id
        if not version_id:
            raise NotFoundError("No published version available for execution")
        version = (
            self.db.query(WorkflowVersion)
            .filter(WorkflowVersion.id == version_id, WorkflowVersion.workflow_id == workflow_id)
            .first()
        )
        if not version:
            raise NotFoundError("Version not found")
        execution = self.engine.execute(
            workflow_id=workflow_id,
            version=version,
            triggered_by=self.current_user["id"],
            organization_id=self._org_id(),
            trigger_type=request.trigger_type,
            initial_inputs=request.inputs,
        )
        self._notify_user(
            user_id=self.current_user["id"],
            subject=f"Workflow execution {execution.status}",
            body=f"Execution {execution.execution_id} for workflow '{wf.name}' finished with status {execution.status}.",
        )
        log_audit_event(
            db=self.db,
            action="workflow.execute",
            user_id=self.current_user["id"],
            organization_id=self._org_id(),
            resource_type="workflow_execution",
            resource_id=execution.execution_id,
        )
        self.db.commit()
        return execution

    def get_execution(self, execution_id: str) -> WorkflowExecution:
        execution = (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.execution_id == execution_id)
            .first()
        )
        if not execution:
            raise NotFoundError("Execution not found")
        self._ensure_org_access(execution.organization_id)
        return execution

    def list_executions(self, filters: dict[str, Any] | None = None) -> list[WorkflowExecution]:
        filters = filters or {}
        query = self.db.query(WorkflowExecution)
        if not is_super_admin(self.current_user):
            query = query.filter(WorkflowExecution.organization_id == self._org_id())
        if filters.get("workflow_id"):
            query = query.filter(WorkflowExecution.workflow_id == filters["workflow_id"])
        if filters.get("status"):
            query = query.filter(WorkflowExecution.status == filters["status"])
        if filters.get("trigger_type"):
            query = query.filter(WorkflowExecution.trigger_type == filters["trigger_type"])
        return (
            query.order_by(WorkflowExecution.created_at.desc())
            .limit(filters.get("limit", 50))
            .offset(filters.get("offset", 0))
            .all()
        )

    def cancel_execution(self, execution_id: str) -> WorkflowExecution:
        execution = self.get_execution(execution_id)
        if execution.status not in ("pending", "running", "retrying"):
            raise AuthorizationError("Only pending or running executions can be cancelled")
        execution.status = "cancelled"
        self.db.commit()
        return execution

    # --- Job queue -------------------------------------------------------------

    def list_jobs(self, status: str | None = None) -> list[WorkflowJob]:
        query = self.db.query(WorkflowJob)
        if status:
            query = query.filter(WorkflowJob.status == status)
        return query.order_by(WorkflowJob.created_at.desc()).limit(100).all()

    # --- Lineage ---------------------------------------------------------------

    def get_lineage(self, execution_id: str) -> list[WorkflowLineage]:
        execution = self.get_execution(execution_id)
        return (
            self.db.query(WorkflowLineage)
            .filter(WorkflowLineage.execution_id == execution.execution_id)
            .order_by(WorkflowLineage.id)
            .all()
        )

    # --- Templates --------------------------------------------------------------

    def create_template(self, request) -> WorkflowTemplate:
        template = WorkflowTemplate(
            created_by=self.current_user["id"],
            name=request.name,
            description=request.description,
            category=request.category,
            nodes=[n.model_dump() for n in request.nodes],
            edges=[e.model_dump() for e in request.edges],
            config=request.config,
            is_public=int(request.is_public),
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def list_templates(
        self, include_public: bool = True, category: str | None = None
    ) -> list[WorkflowTemplate]:
        query = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == 1)
        if not is_super_admin(self.current_user):
            query = query.filter(
                (WorkflowTemplate.created_by == self.current_user["id"])
                | (WorkflowTemplate.is_public == 1)
            )
        elif not include_public:
            query = query.filter(WorkflowTemplate.created_by == self.current_user["id"])
        if category:
            query = query.filter(WorkflowTemplate.category == category)
        return query.order_by(WorkflowTemplate.created_at.desc()).all()

    def get_template(self, template_id: int) -> WorkflowTemplate:
        template = (
            self.db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == template_id, WorkflowTemplate.is_active == 1)
            .first()
        )
        if not template:
            raise NotFoundError("Template not found")
        if (
            not template.is_public
            and not is_super_admin(self.current_user)
            and template.created_by != self.current_user["id"]
        ):
            raise AuthorizationError("Access denied for this template")
        return template

    def delete_template(self, template_id: int) -> None:
        template = self.get_template(template_id)
        if not is_super_admin(self.current_user) and template.created_by != self.current_user["id"]:
            raise AuthorizationError("Only the owner or super admin can delete a template")
        template.is_active = 0
        self.db.commit()

    def clone_workflow(self, workflow_id: int, new_name: str) -> WorkflowDefinition:
        wf = self.get_definition(workflow_id)
        self._ensure_org_access(wf.organization_id)
        latest_version = (
            self.db.query(WorkflowVersion)
            .filter(WorkflowVersion.workflow_id == workflow_id)
            .order_by(WorkflowVersion.version_number.desc())
            .first()
        )
        clone = WorkflowDefinition(
            organization_id=wf.organization_id,
            created_by=self.current_user["id"],
            name=new_name,
            description=wf.description,
            category=wf.category,
        )
        self.db.add(clone)
        self.db.commit()
        if latest_version:
            version = WorkflowVersion(
                workflow_id=clone.id,
                version_number=1,
                status="draft",
                nodes=latest_version.nodes,
                edges=latest_version.edges,
                config=latest_version.config,
                created_by=self.current_user["id"],
            )
            self.db.add(version)
            self.db.commit()
        return clone
