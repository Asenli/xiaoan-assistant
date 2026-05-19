from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import get_current_user
from app.schemas.audit import AuditListResponse
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
async def list_audit_logs(
    event_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logs, total = await get_audit_logs(
        db, event_type=event_type, user_id=user["user_id"], page=page, page_size=page_size,
    )
    return {"logs": logs, "total": total}
