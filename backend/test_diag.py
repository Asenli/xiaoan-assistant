"""诊断：直接对比 query embedding 和 doc embedding 的相似度."""
import asyncio, sys
sys.path.insert(0, '.')
import numpy as np
from app.services.embedding_service import embed_texts, embed_text, get_collection
from app.services.knowledge_service import _extract_text
import glob, os

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

async def main():
    # 1. 找到上传的文档
    files = glob.glob("storage/documents/*.docx")
    if not files:
        print("未找到 docx 文件")
        return

    filepath = files[0]
    print(f"文件: {os.path.basename(filepath)}")

    # 2. 提取文本
    full_text = _extract_text(filepath, ".docx")
    print(f"提取: {len(full_text)} 字符")
    print(f"内容预览:\n{full_text}\n")

    # 3. 查询文本
    query = "商品模块优化"
    print(f"查询: '{query}'")

    # 4. 分别 embedding
    query_vec = await embed_text(query)
    doc_vecs = await embed_texts([full_text])
    doc_vec = doc_vecs[0]

    # 5. 直接计算余弦相似度
    direct_sim = cosine_sim(query_vec, doc_vec)
    print(f"\n直接余弦相似度: {direct_sim:.4f}")

    # 6. 查看向量的模
    print(f"Query 向量模: {np.linalg.norm(query_vec):.4f}")
    print(f"Doc 向量模: {np.linalg.norm(doc_vec):.4f}")

    # 7. 检查向量是否归一化
    print(f"Query 归一化后模: {np.linalg.norm(query_vec / np.linalg.norm(query_vec)):.4f}")
    print(f"Doc 归一化后模: {np.linalg.norm(doc_vec / np.linalg.norm(doc_vec)):.4f}")

    # 8. 查看 ChromaDB 中的向量
    col = get_collection()
    print(f"\nChromaDB 向量总数: {col.count()}")

    if col.count() > 0:
        # 取第一条向量
        result = col.get(limit=1, include=["documents", "embeddings", "metadatas"])
        if result["embeddings"] and result["embeddings"][0]:
            chroma_vec = result["embeddings"][0]
            chroma_doc = result["documents"][0][:100] if result["documents"] else ""
            print(f"ChromaDB 第一条: {result['metadatas'][0].get('filename', '?')}")
            print(f"ChromaDB 内容预览: {chroma_doc}...")
            print(f"ChromaDB 向量模: {np.linalg.norm(chroma_vec):.4f}")

            # 计算 query 和 chroma 向量的直接相似度
            chroma_sim = cosine_sim(query_vec, chroma_vec)
            print(f"Query vs ChromaDB[0] 直接余弦相似度: {chroma_sim:.4f}")

            # 检查 ChromaDB 向量和 doc_vec 是否相同
            vec_diff = np.linalg.norm(np.array(chroma_vec) - np.array(doc_vec))
            print(f"ChromaDB向量 vs 当前Doc向量的差异: {vec_diff:.6f}")

    print("\n=== 诊断结论 ===")
    if direct_sim > 0.5:
        print("Embedding 模型正常，文档和查询语义匹配良好")
        print("问题可能在 ChromaDB 检索层")
    elif direct_sim > 0.2:
        print("相似度中等偏低，可能是文档内容与查询语义差距较大")
    else:
        print(f"相似度极低 ({direct_sim:.4f})，可能原因:")
        print("  1. 文档内容与查询确实不相关")
        print("  2. Embedding 模型对中文短文本效果不佳")
        print(f"  3. 请检查上面的文档内容预览是否包含'商品模块优化'相关内容")

if __name__ == "__main__":
    asyncio.run(main())
