"""API routes for file storage operations.

Endpoints:
  - POST   /api/files/upload          — Upload a file
  - GET    /api/files                 — List files for organization
  - GET    /api/files/{file_id}       — Get file metadata
  - GET    /api/files/{file_id}/download — Download file content
  - GET    /api/files/{file_id}/url   — Get presigned/public URL
  - DELETE /api/files/{file_id}       — Delete a file
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id
from storage.service import FileService

router = APIRouter(prefix="/api/files", tags=["file-storage"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file to object storage. Returns file metadata."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)

    content = await file.read()
    record = svc.upload(
        organization_id=org_id,
        filename=file.filename or "unnamed",
        data=content,
        content_type=file.content_type,
        uploaded_by=current_user["id"],
    )
    return record.to_dict()


@router.get("")
async def list_files(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List files for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)
    files = svc.list_files(org_id, limit=limit, offset=offset)
    total = svc.get_file_count(org_id)
    return {"files": [f.to_dict() for f in files], "count": len(files), "total": total}


@router.get("/{file_id}")
async def get_file_metadata(
    file_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get metadata for a specific file."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)
    record = svc.get_file(file_id, org_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record.to_dict()


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Download file content."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)
    try:
        data, record = svc.download(file_id, org_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found") from None

    return Response(
        content=data,
        media_type=record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{record.filename}"',
        },
    )


@router.get("/{file_id}/url")
async def get_file_url(
    file_id: str,
    expires: int = Query(3600, ge=60, le=86400),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a presigned or public URL for the file."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)
    try:
        url = svc.get_url(file_id, org_id, expires=expires)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found") from None
    return {"url": url, "expires_in": expires}


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a file from storage."""
    org_id = get_current_organization_id(current_user, db)
    svc = FileService(db)
    deleted = svc.delete(file_id, org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"deleted": True, "file_id": file_id}
