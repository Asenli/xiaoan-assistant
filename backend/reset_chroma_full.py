"""彻底重置 ChromaDB：删除集合 + 删除 SQLite 文档记录."""
import asyncio, sys, os, shutil
sys.path.insert(0, '.')
from app.database import init_db, async_session
from app.config import settings
from app.services.embedding_service import KNOWLEDGE_COLLECTION
from sqlalchemy import text

async def main():
    # 1. 关闭所有 ChromaDB 连接，删除物理文件
    chroma_path = settings.chroma_path
    print(f"删除 ChromaDB 数据: {chroma_path}")
    shutil.rmtree(chroma_path, ignore_errors=True)
    os.makedirs(chroma_path, exist_ok=True)

    # 2. 重新创建集合（新建时会用 cosine 距离）
    from app.services.embedding_service import get_collection
    col = get_collection()  # 这会创建新集合
    print(f"新集合创建完成, 向量数: {col.count()}")
    print(f"集合元数据: {col.metadata}")

    # 3. 清空 SQLite 中的文档记录
    await init_db()
    async with async_session() as db:
        await db.execute(text("DELETE FROM document_chunks"))
        await db.execute(text("DELETE FROM knowledge_documents"))
        await db.execute(text("DELETE FROM document_versions"))
        await db.commit()
        print("SQLite 文档记录已清空")

    print("\n✅ 重置完成！新集合将使用余弦距离。")
    print("请重新上传文档。")

if __name__ == "__main__":
    asyncio.run(main())
