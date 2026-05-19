from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    title: str
    category: str
    tags: str
    file_size: int
    file_type: str
    version: int
    chunk_count: int
    is_public: bool
    status: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentVersionResponse(BaseModel):
    id: str
    version: int
    file_size: int
    chunk_count: int
    change_note: str
    updated_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    category: str | None = None
    tags: str | None = None
    is_public: bool | None = None
    change_note: str | None = None


class DocumentSearchRequest(BaseModel):
    query: str
    category: str | None = None
    top_k: int = 6


class ChunkResponse(BaseModel):
    content: str
    document_name: str
    document_id: str
    score: float
    chunk_id: str
