"""Provider-agnostic LLM factory supporting OpenAI / 通义千问 / DeepSeek / 智谱."""
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings

REQUEST_TIMEOUT = 30  # 超时秒数，避免假 API Key 导致无限等待


class LLMFactory:
    """Creates LLM and Embedding instances based on config."""

    @staticmethod
    def _openai_config() -> dict:
        cfg = {
            "api_key": settings.openai_api_key,
            "model": settings.openai_model,
            "request_timeout": REQUEST_TIMEOUT,
        }
        if settings.openai_base_url:
            cfg["base_url"] = settings.openai_base_url
        return cfg

    @staticmethod
    def _validate_api_key(provider: str) -> str:
        """验证 API Key 是否已配置."""
        key_map = {
            "openai": ("OPENAI_API_KEY", settings.openai_api_key),
            "tongyi": ("DASHSCOPE_API_KEY", settings.dashscope_api_key),
            "deepseek": ("DEEPSEEK_API_KEY", settings.deepseek_api_key),
            "zhipu": ("OPENAI_API_KEY or DASHSCOPE_API_KEY",
                       settings.openai_api_key or settings.dashscope_api_key),
        }
        env_var, key = key_map.get(provider, ("API_KEY", ""))
        if not key or key.startswith("sk-xxx"):
            raise RuntimeError(
                f"LLM Provider '{provider}' 的 API Key 未配置或无效。"
                f"请在 backend/.env 中设置有效的 {env_var}"
            )
        return key

    @classmethod
    def create_chat_model(cls, temperature: float = 0.3, streaming: bool = True):
        provider = settings.llm_provider.lower()
        cls._validate_api_key(provider)

        if provider == "openai":
            return ChatOpenAI(**cls._openai_config(), temperature=temperature, streaming=streaming)
        elif provider == "tongyi":
            return ChatOpenAI(
                api_key=settings.dashscope_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                model="qwen-plus",
                temperature=temperature,
                streaming=streaming,
                request_timeout=REQUEST_TIMEOUT,
            )
        elif provider == "deepseek":
            return ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=temperature,
                streaming=streaming,
                request_timeout=REQUEST_TIMEOUT,
            )
        elif provider == "zhipu":
            return ChatOpenAI(
                api_key=settings.openai_api_key or settings.dashscope_api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4",
                model="glm-4",
                temperature=temperature,
                streaming=streaming,
                request_timeout=REQUEST_TIMEOUT,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @classmethod
    def create_embeddings(cls):
        provider = settings.llm_provider.lower()
        cls._validate_api_key(provider)

        if provider == "openai":
            return OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model=settings.openai_embedding_model,
                base_url=settings.openai_base_url or None,
                request_timeout=REQUEST_TIMEOUT,
            )
        elif provider == "tongyi":
            return DashScopeEmbeddings(
                dashscope_api_key=settings.dashscope_api_key,
                model="text-embedding-v2",
            )
        elif provider == "deepseek":
            return OpenAIEmbeddings(
                api_key=settings.deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                model="text-embedding-ada-002",
                request_timeout=REQUEST_TIMEOUT,
            )
        elif provider == "zhipu":
            return OpenAIEmbeddings(
                api_key=settings.openai_api_key or settings.dashscope_api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4",
                model="embedding-2",
                request_timeout=REQUEST_TIMEOUT,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
