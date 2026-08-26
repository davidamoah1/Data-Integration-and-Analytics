"""REST routes for user/organization in-app notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from notifications.models import Notification
from shared.database import get_db
from shared.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "channel": n.channel,
        "subject": n.subject,
        "body": n.body,
        "status": n.status,
        "read": n.read,
        "created_at": str(n.created_at) if n.created_at else None,
        "sent_at": str(n.sent_at) if n.sent_at else None,
    }


@router.get("", response_model=list[dict])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List notifications for the current user."""
    query = db.query(Notification).filter(
        (Notification.user_id == current_user["id"]) | (Notification.user_id.is_(None))
    )
    if unread_only:
        query = query.filter(Notification.read.is_(False))
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [_serialize(n) for n in notifications]


@router.post("/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id is not None and notification.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
    notification.read = True
    db.commit()
    return {"id": notification.id, "read": True}


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a notification."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id is not None and notification.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
    db.delete(notification)
    db.commit()
    return {"deleted": True, "id": notification_id}
