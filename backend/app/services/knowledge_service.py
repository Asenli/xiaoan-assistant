"""知识库文档服务 — 上传、切片、向量化、版本管理、检索."""
import hashlib
import logging
import os
import traceback
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import docx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.knowledge import KnowledgeDocument, DocumentChunk, DocumentVersion
from app.services.embedding_service import embed_texts, add_vectors, delete_vectors

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}


def _extract_text(file_path: str, ext: str) -> str:
    if ext == ".pdf":
        pages = []
        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)
    elif ext == ".docx":
        try:
            doc = docx.Document(file_path)
        except Exception as e:
            # python-docx 只能读取真正的 .docx (Office Open XML) 格式
            # 如果文件是旧版 .doc 改后缀名为 .docx，或者文件损坏，会报 PackageNotFoundError
            raise ValueError(
                f"无法读取 .docx 文件，可能原因：\n"
                f"1. 该文件是旧版 .doc 格式（需用 Word 另存为 .docx）\n"
                f"2. 文件已损坏\n"
                f"3. 文件不是有效的 Word 文档\n\n"
                f"建议：用 Word 打开后「另存为」→ 选择「Word 文档 (.docx)」"
            )
        # 用 \n（单换行）而非 \n\n 连接段落，
        # 避免 RecursiveCharacterTextSplitter 把每行短文本都拆成独立 chunk 导致语义碎片化
        return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


async def upload_document(
    db: AsyncSession, file: UploadFile, user_id: str, category: str = "general",
    tags: str = "", is_public: bool = True, change_note: str = "",
) -> KnowledgeDocument:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    await file.seek(0)
    file_hash = hashlib.sha256(content).hexdigest()

    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.file_hash == file_hash)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    doc_id = str(uuid.uuid4())
    save_path = Path(settings.document_path) / f"{doc_id}{ext}"
    save_path.write_bytes(content)

    title = Path(file.filename).stem

    doc = KnowledgeDocument(
        id=doc_id,
        filename=file.filename,
        title=title,
        category=category,
        tags=tags,
        file_hash=file_hash,
        file_path=str(save_path),
        file_size=len(content),
        file_type=ext.lstrip("."),
        version=1,
        is_public=is_public,
        status="processing",
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.commit()

    try:
        full_text = _extract_text(str(save_path), ext)
        if not full_text.strip():
            raise ValueError("未能从文档中提取到文本内容")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""],
        )
        chunks = splitter.split_text(full_text)
        # 过滤空字符串和纯空白 chunk（千问 API 不接受空内容）
        chunks = [c for c in chunks if c.strip()]
        if not chunks:
            raise ValueError("文本分块后无有效内容，请检查文档格式")

        logger.info(f"文档分块完成: {len(chunks)} 个有效片段")
        print(f"[UPLOAD] {file.filename}: 提取 {len(full_text)} 字符, 分块 {len(chunks)} 个, 开始 Embedding...")
        embeddings = await embed_texts(chunks)
        chroma_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": doc_id, "filename": file.filename, "chunk_index": i,
             "category": category, "tags": tags, "user_id": user_id}
            for i in range(len(chunks))
        ]
        add_vectors(chroma_ids, chunks, embeddings, metadatas)
        print(f"[UPLOAD] {file.filename}: Embedding 完成, 写入 {len(embeddings)} 条向量到 ChromaDB")

        for i, chunk_text in enumerate(chunks):
            db.add(DocumentChunk(
                document_id=doc_id, chroma_id=chroma_ids[i],
                chunk_index=i, content=chunk_text, token_count=len(chunk_text),
            ))

        doc.status = "ready"
        doc.chunk_count = len(chunks)
    except Exception as e:
        doc.status = "failed"
        doc.chunk_count = 0
        logger.error(f"文档处理失败 [{file.filename}]: {e}")
        logger.error(traceback.format_exc())
        await db.commit()
        raise RuntimeError(f"文档处理失败: {str(e)}") from e

    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document(
    db: AsyncSession, document_id: str, user_id: str,
    file: UploadFile | None = None, title: str | None = None,
    category: str | None = None, tags: str | None = None,
    is_public: bool | None = None, change_note: str = "",
) -> KnowledgeDocument:
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError("文档不存在")

    if title is not None:
        doc.title = title
    if category is not None:
        doc.category = category
    if tags is not None:
        doc.tags = tags
    if is_public is not None:
        doc.is_public = is_public

    if file:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}")

        content = await file.read()
        new_hash = hashlib.sha256(content).hexdigest()
        save_path = Path(settings.document_path) / f"{document_id}_{doc.version + 1}{ext}"
        save_path.write_bytes(content)

        version_snapshot = DocumentVersion(
            document_id=document_id, version=doc.version,
            file_hash=doc.file_hash, file_path=doc.file_path,
            file_size=doc.file_size, chunk_count=doc.chunk_count,
            change_note=change_note, updated_by=user_id,
        )
        db.add(version_snapshot)

        old_chroma_ids = await db.execute(
            select(DocumentChunk.chroma_id).where(DocumentChunk.document_id == document_id)
        )
        old_ids = [row[0] for row in old_chroma_ids.all()]
        delete_vectors(old_ids)
        await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        full_text = _extract_text(str(save_path), ext)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""],
        )
        chunks = splitter.split_text(full_text)
        embeddings = await embed_texts(chunks)
        new_chroma_ids = [f"{document_id}_v{doc.version + 1}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "filename": file.filename, "chunk_index": i,
             "category": category or doc.category, "tags": tags or doc.tags, "user_id": user_id}
            for i in range(len(chunks))
        ]
        add_vectors(new_chroma_ids, chunks, embeddings, metadatas)

        for i, chunk_text in enumerate(chunks):
            db.add(DocumentChunk(
                document_id=document_id, chroma_id=new_chroma_ids[i],
                chunk_index=i, content=chunk_text, token_count=len(chunk_text),
            ))

        doc.filename = file.filename
        doc.file_hash = new_hash
        doc.file_path = str(save_path)
        doc.file_size = len(content)
        doc.file_type = ext.lstrip(".")
        doc.version += 1
        doc.chunk_count = len(chunks)
        doc.status = "ready"

    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, document_id: str) -> bool:
    result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return False

    chroma_ids_result = await db.execute(
        select(DocumentChunk.chroma_id).where(DocumentChunk.document_id == document_id)
    )
    chroma_ids = [row[0] for row in chroma_ids_result.all()]
    delete_vectors(chroma_ids)

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()
    return True


async def get_documents(db: AsyncSession, user_id: str | None = None,
                        category: str | None = None, status: str | None = None,
                        page: int = 1, page_size: int = 20) -> tuple[list[KnowledgeDocument], int]:
    q = select(KnowledgeDocument)
    if user_id:
        q = q.where(KnowledgeDocument.uploaded_by == user_id)
    if category:
        q = q.where(KnowledgeDocument.category == category)
    if status:
        q = q.where(KnowledgeDocument.status == status)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(KnowledgeDocument.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all(), total


async def get_document_versions(db: AsyncSession, document_id: str) -> list[DocumentVersion]:
    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version.desc())
    )
    return result.scalars().all()
