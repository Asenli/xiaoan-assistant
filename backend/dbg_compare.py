"""对比 ChromaDB 存储向量 vs 当前模型生成向量是否一致."""
import asyncio, sys, json, numpy as np
sys.path.insert(0, '.')
from app.services.embedding_service import embed_text, embed_texts, get_collection

async def main():
    col = get_collection()
    count = col.count()
    print(f"ChromaDB 向量数: {count}")

    if count == 0:
        print("无向量，无法对比")
        return

    # 1. 获取 ChromaDB 中的全部数据
    data = col.get(include=["documents", "embeddings", "metadatas"])

    for i in range(len(data["ids"])):
        storage_vec = np.array(data["embeddings"][i])
        doc_text = data["documents"][i][:100]
        meta = data["metadatas"][i]
        doc_name = meta.get("filename", "?")
        doc_id = meta.get("document_id", "?")
        print(f"\n--- Chunk {i}: {doc_name} ---")
        print(f"  内容前100字: {doc_text}")
        print(f"  ChromaDB向量模: {np.linalg.norm(storage_vec):.4f}")

        # 2. 用当前模型重新生成 embedding
        try:
            fresh_vecs = await embed_texts([data["documents"][i]])
            fresh_vec = np.array(fresh_vecs[0])
            print(f"  当前模型向量模: {np.linalg.norm(fresh_vec):.4f}")

            # 3. 对比差异
            diff = np.linalg.norm(storage_vec - fresh_vec)
            cos_sim = float(np.dot(storage_vec, fresh_vec) / (np.linalg.norm(storage_vec) * np.linalg.norm(fresh_vec)))
            print(f"  向量差异(L2距离): {diff:.6f}")
            print(f"  余弦相似度: {cos_sim:.4f}")

            if diff < 0.01:
                print(f"  ✓ 向量一致！")
            elif cos_sim > 0.8:
                print(f"  ⚠ 高度相似 ({cos_sim:.4f})，但略有差异")
            else:
                print(f"  ✗ 严重不一致！ChromaDB 存的是旧模型的向量")

        except Exception as e:
            print(f"  生成对比向量失败: {e}")

    # 4. 测试查询 "商品模块优化了哪些内容"
    print(f"\n\n=== 查询测试 ===")
    query = "商品模块优化了哪些内容"
    query_vec = np.array(await embed_text(query))
    print(f"查询向量模: {np.linalg.norm(query_vec):.4f}")

    # 用 query 向量对比 ChromaDB 中所有向量
    for i, (vec, meta) in enumerate(zip(data["embeddings"], data["metadatas"])):
        db_vec = np.array(vec)
        cos_sim = float(np.dot(query_vec, db_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(db_vec)))
        print(f"  Query vs ChromaDB[{i}] ({meta.get('filename','?')}): {cos_sim:.4f}")

    # 用 query 向量对比 当前模型生成的新向量
    print(f"\n=== 对比关键: 查询向量 vs 当前模型重新生成 ===")
    for i in range(len(data["documents"])):
        fresh_vecs = await embed_texts([data["documents"][i]])
        fresh_vec = np.array(fresh_vecs[0])
        cos_sim = float(np.dot(query_vec, fresh_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(fresh_vec)))
        print(f"  Query vs Fresh[{i}]: {cos_sim:.4f} (应为真实相似度)")

if __name__ == "__main__":
    asyncio.run(main())
