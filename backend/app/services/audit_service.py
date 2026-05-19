"""审计日志服务 — 记录所有关键操作和问答交互."""
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def log_event(
    db: AsyncSession,
    event_type: str,
    action: str,
    user_id: str | None = None,
    guest_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    log_entry = AuditLog(
        id=str(uuid.uuid4()),
        event_type=event_type,
        user_id=user_id,
        guest_id=guest_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.commit()


async def get_audit_logs(
    db: AsyncSession,
    event_type: str | None = None,
    user_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AuditLog], int]:
    q = select(AuditLog)
    if event_type:
        q = q.where(AuditLog.event_type == event_type)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all(), total
