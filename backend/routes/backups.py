from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from backend.auth import AuthenticatedUser, require_permission
from backend.database import db_session
from storage.backup import backup_service
from storage.restore import restore_service
from storage.retention import retention_service

router = APIRouter(prefix="/backups", tags=["backups"])

class BackupItem(BaseModel):
    id: int
    filename: str
    s3_key: str
    size_bytes: int
    checksum_sha256: str
    backup_type: str
    created_at: str
    created_by_uid: Optional[str] = None
    created_by_email: Optional[str] = None
    status: str

class RestoreRequest(BaseModel):
    target_dir: Optional[str] = "/data"

@router.get("", response_model=List[BackupItem])
def list_backups(
    limit: int = Query(default=50, ge=1, le=100),
    user: AuthenticatedUser = Depends(require_permission("backup:read"))
):
    with db_session() as conn:
        cursor = conn.execute(
            """
            SELECT id, filename, s3_key, size_bytes, checksum_sha256, backup_type, created_at, created_by_uid, created_by_email, status
            FROM backups
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.post("/create", response_model=BackupItem)
def create_backup(
    backup_type: str = Query(default="manual"),
    user: AuthenticatedUser = Depends(require_permission("backup:create"))
):
    try:
        res = backup_service.create_backup(
            backup_type=backup_type,
            created_by_uid=user.uid,
            created_by_email=user.email
        )
        # Apply retention policy after manual creation as well
        retention_service.apply_retention()
        
        with db_session() as conn:
            cursor = conn.execute("SELECT * FROM backups WHERE id = ?", (res["id"],))
            record = cursor.fetchone()
            return dict(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {e}")

@router.post("/{backup_id}/restore")
def restore_backup(
    backup_id: int,
    req: RestoreRequest = RestoreRequest(),
    user: AuthenticatedUser = Depends(require_permission("backup:restore"))
):
    try:
        res = restore_service.restore_backup(
            backup_id=backup_id,
            target_dir=req.target_dir or "/data",
            restored_by_uid=user.uid,
            restored_by_email=user.email
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore operation failed: {e}")
