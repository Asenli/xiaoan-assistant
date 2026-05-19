from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_base_url: str = ""
    dashscope_api_key: str = ""
    deepseek_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./storage/xiaoan.db"
    chroma_path: str = "./storage/chroma"
    document_path: str = "./storage/documents"

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    widget_api_key: str = "xiaoan-widget-key-change-in-production"

    # RAG Config
    chunk_size: int = 512
    chunk_overlap: int = 100
    retrieval_top_k: int = 6
    retrieval_score_threshold: float = 0.35
    rerank_enabled: bool = False
    hybrid_search_enabled: bool = True
    bm25_weight: float = 0.3
    vector_weight: float = 0.7

    class Config:
        env_file = ".env"


settings = Settings()
Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
Path(settings.document_path).mkdir(parents=True, exist_ok=True)
