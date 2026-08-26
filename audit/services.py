"""Audit service and routes â€” log retrieval and security event tracking."""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from audit.models import AuditLog, SecurityLog, SystemLog
from shared.database import get_db
from shared.dependencies import require_any_role, require_permissions
from shared.response import success_response
from shared.tenant import get_current_organization_id, is_super_admin


class AuditService:
    def __init__(self, db: DbSession):
        self.db = db

    def list_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: int = None,
        action: str = None,
        organization_id: int = None,
    ) -> dict:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        count_query = select(func.count()).select_from(AuditLog)
        if organization_id is not None:
            query = query.where(AuditLog.organization_id == organization_id)
            count_query = count_query.where(AuditLog.organization_id == organization_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)

        total = self.db.execute(count_query).scalar()
        offset = (page - 1) * page_size
        logs = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()

        return {
            "logs": [self._audit_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def list_security_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        severity: str = None,
        organization_id: int = None,
    ) -> dict:
        query = select(SecurityLog).order_by(SecurityLog.created_at.desc())
        count_query = select(func.count()).select_from(SecurityLog)
        if organization_id is not None:
            query = query.where(SecurityLog.organization_id == organization_id)
            count_query = count_query.where(SecurityLog.organization_id == organization_id)
        if severity:
            query = query.where(SecurityLog.severity == severity)
            count_query = count_query.where(SecurityLog.severity == severity)

        total = self.db.execute(count_query).scalar()
        offset = (page - 1) * page_size
        logs = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()

        return {
            "logs": [self._security_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def list_system_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        level: str = None,
    ) -> dict:
        query = select(SystemLog).order_by(SystemLog.created_at.desc())
        count_query = select(func.count()).select_from(SystemLog)
        if level:
            query = query.where(SystemLog.log_level == level)
            count_query = count_query.where(SystemLog.log_level == level)

        total = self.db.execute(count_query).scalar()
        offset = (page - 1) * page_size
        logs = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()

        return {
            "logs": [self._system_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def create_security_log(
        self,
        user_id: int,
        event_type: str,
        ip_address: str = None,
        user_agent: str = None,
        resource: str = None,
        severity: str = "info",
        details: dict = None,
    ):
        log = SecurityLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            severity=severity,
            details=details,
        )
        self.db.add(log)
        self.db.flush()
        return log

    @staticmethod
    def _audit_to_dict(log: AuditLog) -> dict:
        return {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }

    @staticmethod
    def _security_to_dict(log: SecurityLog) -> dict:
        return {
            "id": log.id,
            "user_id": log.user_id,
            "event_type": log.event_type,
            "ip_address": log.ip_address,
            "severity": log.severity,
            "created_at": log.created_at,
        }

    @staticmethod
    def _system_to_dict(log: SystemLog) -> dict:
        return {
            "id": log.id,
            "log_level": log.log_level,
            "message": log.message,
            "module": log.module,
            "created_at": log.created_at,
        }


# --- Routers ----------------------------------------------------------------

audit_router = APIRouter(prefix="/audit", tags=["Audit"])


@audit_router.get("/logs")
async def list_audit_logs(
    page: int = 1,
    page_size: int = 50,
    user_id: int = None,
    action: str = None,
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    org_id = None if is_super_admin(current_user) else get_current_organization_id(current_user, db)
    service = AuditService(db)
    return success_response(service.list_audit_logs(page, page_size, user_id, action, org_id))


@audit_router.get("/security")
async def list_security_logs(
    page: int = 1,
    page_size: int = 50,
    severity: str = None,
    current_user: dict = Depends(require_permissions("audit.view")),
    db: DbSession = Depends(get_db),
):
    org_id = None if is_super_admin(current_user) else get_current_organization_id(current_user, db)
    service = AuditService(db)
    return success_response(service.list_security_logs(page, page_size, severity, org_id))


@audit_router.get("/system")
async def list_system_logs(
    page: int = 1,
    page_size: int = 50,
    level: str = None,
    # SystemLog entries have no organization concept and can expose internal
    # platform-wide debugging details, so this is restricted to super admins.
    current_user: dict = Depends(require_any_role("super_admin")),
    db: DbSession = Depends(get_db),
):
    service = AuditService(db)
    return success_response(service.list_system_logs(page, page_size, level))
