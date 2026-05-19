"""测试：读取 docx → 分块 → embedding → ChromaDB 全流程."""
import asyncio, sys
sys.path.insert(0, '.')
from app.services.knowledge_service import _extract_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.embedding_service import embed_texts, get_collection
from app.config import settings

async def main():
    # 1. 找到已上传的文件
    import glob
    files = glob.glob("storage/documents/*.docx")
    if not files:
        print("未找到 .docx 文件，请先上传文档")
        return

    filepath = files[0]
    print(f"测试文件: {filepath}")

    # 2. 提取文本
    full_text = _extract_text(filepath, ".docx")
    print(f"提取文本: {len(full_text)} 字符")
    print(f"前200字: {full_text[:200]}")

    # 3. 分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""],
    )
    chunks = splitter.split_text(full_text)
    chunks = [c for c in chunks if c.strip()]
    print(f"\n分块: {len(chunks)} 个")
    for i, c in enumerate(chunks):
        print(f"  [{i}] {len(c)} 字: {c[:80]}...")

    # 4. Embedding
    if chunks:
        print(f"\n开始 Embedding {len(chunks)} 个 chunks...")
        try:
            embeddings = await embed_texts(chunks)
            print(f"Embedding 成功: {len(embeddings)} 条, dim={len(embeddings[0])}")
        except Exception as e:
            print(f"Embedding 失败: {e}")
            return
    else:
        print("无有效分块")
        return

    # 5. ChromaDB 状态
    col = get_collection()
    print(f"\nChromaDB 当前向量数: {col.count()}")

if __name__ == '__main__':
    asyncio.run(main())
