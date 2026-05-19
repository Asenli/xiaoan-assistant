import asyncio, sys
sys.path.insert(0, '.')
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings

async def test():
    e = DashScopeEmbeddings(
        dashscope_api_key=settings.dashscope_api_key,
        model='text-embedding-v2',
    )
    texts = ['你好世界', '结算对账操作流程介绍', '食品安全法规要点解释']
    try:
        result = await e.aembed_documents(texts)
        print(f'OK: {len(result)} embeddings, dim={len(result[0])}')
    except Exception as ex:
        print(f'FAIL: {type(ex).__name__}: {ex}')

asyncio.run(test())
