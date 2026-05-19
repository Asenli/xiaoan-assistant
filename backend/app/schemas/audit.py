from pydantic import BaseModel
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    user_id: str | None
    guest_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: str | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
