"""Collaboration service — comments, sharing, workspaces, version control."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import SharedResource, WorkspaceComment


class CollaborationService:
    """Service for collaboration features."""

    def __init__(self, db: DbSession):
        self.db = db

    # ─── Comments ────────────────────────────────────────────

    def add_comment(
        self,
        org_id: int,
        user_id: int,
        resource_type: str,
        resource_id: int,
        content: str,
        parent_id: int | None = None,
        mentions: list[int] | None = None,
    ) -> WorkspaceComment:
        comment = WorkspaceComment(
            organization_id=org_id,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            parent_id=parent_id,
            content=content,
            mentions=mentions or [],
        )
        self.db.add(comment)
        self.db.commit()
        return comment

    def list_comments(
        self,
        org_id: int,
        resource_type: str,
        resource_id: int,
    ) -> list[WorkspaceComment]:
        return self.db.execute(
            select(WorkspaceComment)
            .where(
                WorkspaceComment.organization_id == org_id,
                WorkspaceComment.resource_type == resource_type,
                WorkspaceComment.resource_id == resource_id,
            )
            .order_by(WorkspaceComment.created_at.asc())
        ).scalars().all()

    def resolve_comment(self, comment_id: int, org_id: int) -> WorkspaceComment:
        comment = self.db.execute(
            select(WorkspaceComment).where(
                WorkspaceComment.id == comment_id,
                WorkspaceComment.organization_id == org_id,
            )
        ).scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")
        comment.resolved = True
        self.db.commit()
        return comment

    def delete_comment(self, comment_id: int, org_id: int) -> None:
        comment = self.db.execute(
            select(WorkspaceComment).where(
                WorkspaceComment.id == comment_id,
                WorkspaceComment.organization_id == org_id,
            )
        ).scalar_one_or_none()
        if comment:
            self.db.delete(comment)
            self.db.commit()

    # ─── Sharing ─────────────────────────────────────────────

    def share_resource(
        self,
        org_id: int,
        user_id: int,
        resource_type: str,
        resource_id: int,
        shared_with_user_id: int | None = None,
        shared_with_role: str | None = None,
        permission: str = "view",
        expires_at: datetime | None = None,
    ) -> SharedResource:
        share = SharedResource(
            organization_id=org_id,
            resource_type=resource_type,
            resource_id=resource_id,
            shared_with_user_id=shared_with_user_id,
            shared_with_role=shared_with_role,
            permission=permission,
            shared_by=user_id,
            expires_at=expires_at,
        )
        self.db.add(share)
        self.db.commit()
        return share

    def list_shares(
        self,
        org_id: int,
        resource_type: str,
        resource_id: int,
    ) -> list[SharedResource]:
        return self.db.execute(
            select(SharedResource).where(
                SharedResource.organization_id == org_id,
                SharedResource.resource_type == resource_type,
                SharedResource.resource_id == resource_id,
            )
        ).scalars().all()

    def revoke_share(self, share_id: int, org_id: int) -> None:
        share = self.db.execute(
            select(SharedResource).where(
                SharedResource.id == share_id,
                SharedResource.organization_id == org_id,
            )
        ).scalar_one_or_none()
        if share:
            self.db.delete(share)
            self.db.commit()

    def check_permission(
        self,
        org_id: int,
        user_id: int,
        resource_type: str,
        resource_id: int,
        required_permission: str = "view",
    ) -> bool:
        """Check if a user has permission to access a shared resource."""
        shares = self.db.execute(
            select(SharedResource).where(
                SharedResource.organization_id == org_id,
                SharedResource.resource_type == resource_type,
                SharedResource.resource_id == resource_id,
            )
        ).scalars().all()

        permission_hierarchy = {"view": 1, "comment": 2, "edit": 3, "admin": 4}
        required_level = permission_hierarchy.get(required_permission, 1)

        for share in shares:
            # Check expiry
            if share.expires_at and share.expires_at < datetime.now(timezone.utc):
                continue

            # Direct user share
            if share.shared_with_user_id == user_id:
                user_level = permission_hierarchy.get(share.permission, 0)
                if user_level >= required_level:
                    return True

            # Role-based share (would need to check user's role)
            # For now, role-based shares grant view access to all org members

        return False
