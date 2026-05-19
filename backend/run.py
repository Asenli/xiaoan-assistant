"""启动脚本 — 初始化种子数据 + 启动 FastAPI 服务."""
import asyncio
import uvicorn


async def setup():
    from app.database import init_db
    await init_db()
    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(setup())

    # Try to seed
    try:
        from seed_data import seed
        asyncio.run(seed())
    except Exception as e:
        print(f"Seed skipped: {e}")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
