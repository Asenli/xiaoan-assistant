from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import get_current_user
from app.schemas.knowledge import (
    DocumentResponse, DocumentListResponse, DocumentVersionResponse, DocumentUpdateRequest,
)
from app.services import knowledge_service
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/upload", response_model=DocumentResponse)
async def upload(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    tags: str = Form(default=""),
    is_public: bool = Form(default=True),
    change_note: str = Form(default=""),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        doc = await knowledge_service.upload_document(
            db, file, user["user_id"],
            category=category, tags=tags, is_public=is_public, change_note=change_note,
        )
        await log_event(
            db, "knowledge", "upload", user_id=user["user_id"],
            resource_type="document", resource_id=doc.id,
            detail=f"Uploaded {file.filename} ({doc.file_size} bytes)",
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_docs(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    docs, total = await knowledge_service.get_documents(
        db, user_id=user["user_id"], category=category, status=status, page=page, page_size=page_size,
    )
    return {"documents": docs, "total": total}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_doc(
    document_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    docs, _ = await knowledge_service.get_documents(db, user_id=user["user_id"])
    for doc in docs:
        if doc.id == document_id:
            return doc
    raise HTTPException(status_code=404, detail="文档不存在")


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_doc(
    document_id: str,
    file: UploadFile | None = File(default=None),
    title: str | None = Form(default=None),
    category: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    is_public: bool | None = Form(default=None),
    change_note: str = Form(default=""),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        doc = await knowledge_service.update_document(
            db, document_id, user["user_id"],
            file=file, title=title, category=category,
            tags=tags, is_public=is_public, change_note=change_note,
        )
        await log_event(
            db, "knowledge", "update", user_id=user["user_id"],
            resource_type="document", resource_id=doc.id,
            detail=f"Updated document (v{doc.version})",
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}")
async def delete_doc(
    document_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await knowledge_service.delete_document(db, document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文档不存在")
    await log_event(
        db, "knowledge", "delete", user_id=user["user_id"],
        resource_type="document", resource_id=document_id,
    )
    return {"message": "文档已删除"}


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def get_versions(
    document_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.get_document_versions(db, document_id)
