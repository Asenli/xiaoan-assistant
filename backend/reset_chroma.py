"""清空 ChromaDB 集合 + 清空文档表（保留 admin 用户）."""
import asyncio, sys
sys.path.insert(0, '.')
from app.database import init_db, async_session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.embedding_service import get_collection
from sqlalchemy import text

async def main():
    # 1. 清空 ChromaDB
    collection = get_collection()
    count_before = collection.count()
    if count_before > 0:
        all_ids = collection.get()["ids"]
        collection.delete(ids=all_ids)
    count_after = collection.count()
    print(f"ChromaDB: {count_before} → {count_after} 条")

    # 2. 清空 SQLite 中的文档和 chunk 记录
    await init_db()
    async with async_session() as db:
        # 清空文档和分块表
        await db.execute(text("DELETE FROM document_chunks"))
        await db.execute(text("DELETE FROM knowledge_documents"))
        await db.execute(text("DELETE FROM document_versions"))
        await db.commit()
        print("文档记录已清空")

    print("\n✅ 重置完成！请重新上传文档 → http://localhost:5173/admin/knowledge")
    print("或使用 python seed_knowledge.py 导入示例文档")

if __name__ == "__main__":
    asyncio.run(main())
