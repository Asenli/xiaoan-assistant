"""向量嵌入服务 — ChromaDB + Provider-agnostic embedding."""
import logging
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
    """获取 ChromaDB 集合（集合必须用余弦距离，score=1-distance 直接得出余弦相似度）. """
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


def search_vectors(query_embedding: list[float], n_results: int = 6, where: dict | None = None) -> dict:
    collection = get_collection()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
