"""向量嵌入服务 — ChromaDB + Provider-agnostic embedding (via LangChain)."""
import logging
import numpy as np
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

chroma_client = chromadb.PersistentClient(
    path=settings.chroma_path,
    settings=ChromaSettings(anonymized_telemetry=False),
)

KNOWLEDGE_COLLECTION = "xiaoan_knowledge"


def get_collection():
    """获取或创建 ChromaDB 集合（显式指定余弦距离，否则默认 L2 会导致检索分数错误）. """
    return chroma_client.get_or_create_collection(
        name=KNOWLEDGE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


async def embed_text(text: str) -> list[float]:
    embeddings = LLMFactory.create_embeddings()
    return await embeddings.aembed_query(text)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = LLMFactory.create_embeddings()
    return await embeddings.aembed_documents(texts)


def add_vectors(ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    collection = get_collection()
    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)


def delete_vectors(ids: list[str]):
    collection = get_collection()
    if ids:
        collection.delete(ids=ids)


def update_vector(chroma_id: str, text: str, embedding: list[float], metadata: dict):
    collection = get_collection()
    collection.update(ids=[chroma_id], documents=[text], embeddings=[embedding], metadatas=[metadata])


def search_vectors(query_embedding: list[float], n_results: int = 6, where: dict | None = None) -> dict:
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances", "embeddings"],
    )
    # ChromaDB 可能默认用 L2 距离而非余弦距离，
    # 导致 score=1-distance 算出的相似度错误。
    # 直接用向量计算余弦相似度，保证结果准确。
    if results["ids"] and results["ids"][0]:
        qv = np.array(query_embedding)
        for i in range(len(results["ids"][0])):
            sv = np.array(results["embeddings"][0][i])
            # 余弦相似度 = dot(A,B) / (|A||B|)
            cos_sim = float(np.dot(qv, sv) / (np.linalg.norm(qv) * np.linalg.norm(sv)))
            orig_distance = results["distances"][0][i]
            # 覆盖掉 ChromaDB 返回的错误距离
            results["distances"][0][i] = round(1.0 - cos_sim, 4)  # 转为余弦距离
            logger.info(
                f"向量检索: ChromaDB原始距离={orig_distance:.4f} "
                f"→ 余弦相似度={cos_sim:.4f} "
                f"(doc={results['metadatas'][0][i].get('filename','?')})"
            )
            print(
                f"[EMBED] query vs {results['metadatas'][0][i].get('filename','?')}: "
                f"ChromaDB原始距离={orig_distance:.4f} "
                f"→ numpy余弦相似度={cos_sim:.4f}"
            )
    return results
