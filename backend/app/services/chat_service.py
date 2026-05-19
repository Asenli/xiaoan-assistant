"""聊天服务 — 编排 RAG + 意图识别 + 菜单推荐 + SSE 流式输出."""
import json
from typing import AsyncGenerator

from app.config import settings
from app.core.llm_factory import LLMFactory
from app.services.rag_service import detect_intent, hybrid_retrieve, build_rag_context, extract_action_steps

SYSTEM_PROMPT = """你是"小安助手"，一个专业的食安管理系统客服助手，负责帮助用户解答系统使用问题。

## 你的能力范围
1. **菜单导航**: 引导用户找到正确的系统功能菜单和页面
2. **操作指导**: 提供系统功能的操作步骤和教程
3. **法规解答**: 解答食品安全相关法规、标准、规定
4. **系统问题**: 解答系统使用中的常见问题

## 回答规则
1. 基于提供的知识库文档内容回答，不要编造信息。
2. 如果文档中没有相关信息，明确告知用户并提供建议（如联系管理员）。
3. 回答使用中文，简洁、专业、友好。
4. 当涉及系统功能菜单时，明确指出菜单路径和页面名称。
5. 操作步骤要清晰、有序，方便用户按步骤执行。
6. 涉及食安法规时，注明具体法规名称和条款。
7. 引用信息时注明来源文档。

## 回答格式
- 对于菜单导航问题：先给出菜单路径，再简要说明该页面的功能
- 对于操作步骤问题：按序号列出操作步骤
- 对于法规问题：引用法规原文并给出解读
- 对于一般问题：简洁直接回答"""

DEFAULT_FALLBACK = """抱歉，我在当前知识库中未找到与您问题相关的信息。

**可能原因：**
1. 知识库中尚无与该问题相关的文档（当前仅有少量文档）
2. 问题与已有文档内容语义差异较大
3. 文档内容太少，无法有效匹配

**建议：**
- 尝试用文档中已有的关键词提问
- 联系管理员上传更多相关知识文档（如结算对账操作指南、食安法规等）
- 输入"菜单列表"查看系统功能入口"""


async def generate_chat_stream(
    query: str,
    menu_cards: list[dict],
    user_id: str | None = None,
    guest_id: str | None = None,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
) -> AsyncGenerator[str, None]:
    """
    流式聊天 — SSE 事件流，包含 text / sources / menu_cards / steps / intent / done.

    menu_cards 由 API 层通过 menu_service 预先查询并传入，保持服务层无 DB 依赖。
    """
    top_k = top_k or settings.retrieval_top_k

    # 1. 意图识别
    intent, confidence = await detect_intent(query)
    yield _sse("intent", {"intent": intent, "confidence": confidence})

    # 2. 混合检索
    chunks = await hybrid_retrieve(query=query, top_k=top_k, document_ids=document_ids)

    # 3. 发送来源
    yield _sse("sources", {"sources": [
        {"document_name": c["document_name"], "document_id": c["document_id"], "score": c["score"]}
        for c in chunks
    ]})

    # 4. 发送菜单卡片
    if menu_cards:
        yield _sse("menu_cards", {"menu_cards": menu_cards})

    # 5. 操作步骤提取并发送
    action_steps = await extract_action_steps(chunks)
    if action_steps:
        yield _sse("steps", {"steps": action_steps})

    # 6. 无结果时的降级处理
    if not chunks and not menu_cards:
        yield _sse("text", {"content": DEFAULT_FALLBACK})
        yield _sse("done", {})
        return

    # 7. 构建 LLM 上下文
    context = await build_rag_context(query, chunks)
    menu_ctx = _build_menu_context(menu_cards)

    llm = LLMFactory.create_chat_model(temperature=0.3)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(query, context, menu_ctx)},
    ]

    full_answer = ""
    async for chunk in llm.astream(messages):
        content = chunk.content
        if content:
            full_answer += content
            yield _sse("text", {"content": content})

    yield _sse("done", {"answer": full_answer})


def _build_menu_context(menu_cards: list[dict]) -> str:
    if not menu_cards:
        return ""
    parts = ["\n## 相关系统菜单\n"]
    for mc in menu_cards:
        desc = mc.get("description", "")
        parts.append(
            f"- **{mc['breadcrumb']}**"
            f"{' → `' + mc['route_path'] + '`' if mc.get('route_path') else ''}"
            f"{': ' + desc if desc else ''}"
        )
    return "\n".join(parts)


def _build_user_prompt(query: str, context: str, menu_context: str) -> str:
    parts = []
    if context:
        parts.append(f"## 知识库参考资料\n{context}")
    if menu_context:
        parts.append(menu_context)
    parts.append(f"## 用户问题\n{query}\n\n请根据以上信息回答用户的问题。如果涉及系统功能菜单，请明确告知菜单路径。")
    return "\n\n".join(parts)


def _sse(event_type: str, data) -> str:
    """构建 SSE 事件，data 必须为 dict."""
    payload = {"type": event_type}
    payload.update(data)
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
