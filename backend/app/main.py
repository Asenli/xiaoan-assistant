from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import auth, knowledge, menu, chat, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    _check_api_key()
    yield


def _check_api_key():
    """启动时检查 API Key 是否已配置，未配置则打印警告."""
    from app.config import settings
    provider = settings.llm_provider.lower()
    key_map = {
        "openai": settings.openai_api_key,
        "tongyi": settings.dashscope_api_key,
        "deepseek": settings.deepseek_api_key,
        "zhipu": settings.openai_api_key or settings.dashscope_api_key,
    }
    api_key = key_map.get(provider, "")
    if not api_key or api_key.startswith("sk-xxx"):
        print("=" * 60)
        print("⚠ 警告: LLM API Key 未配置!")
        print(f"  当前 Provider: {provider}")
        print("  请在 backend/.env 中设置有效的 API Key")
        print("  否则 文档上传/聊天/Embedding 功能将无法使用")
        print("  菜单管理、审计日志等不需要 LLM 的功能正常")
        print("=" * 60)


app = FastAPI(
    title="小安助手 XiaoAn Assistant",
    description="基于 RAG 的食安管理系统智能客服助手",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(menu.router)
app.include_router(chat.router)
app.include_router(audit.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "xiaoan-assistant"}
