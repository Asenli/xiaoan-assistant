"""确保 ChromaDB 集合使用余弦距离（先删后建）."""
import sys, os, shutil
sys.path.insert(0, '.')
from app.services.embedding_service import chroma_client, KNOWLEDGE_COLLECTION

try:
    chroma_client.delete_collection(name=KNOWLEDGE_COLLECTION)
    print(f"已删除旧集合: {KNOWLEDGE_COLLECTION}")
except Exception:
    print(f"集合不存在，跳过删除")

# 新建集合，指定余弦距离
collection = chroma_client.create_collection(
    name=KNOWLEDGE_COLLECTION,
    metadata={"hnsw:space": "cosine"},
)
print(f"已新建集合: {KNOWLEDGE_COLLECTION}")
print(f"集合元数据: {collection.metadata}")
print(f"\n✅ 完成！新集合使用余弦距离，score = 1 - distance 就是正确相似度。")
print(f"请重新上传文档。")
