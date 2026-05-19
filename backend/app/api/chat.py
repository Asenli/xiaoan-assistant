import json
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user, get_optional_user, verify_widget_token
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, WidgetChatRequest, FeedbackRequest
from app.services.chat_service import generate_chat_stream
from app.services.menu_service import search_menus_by_keyword, get_menu_breadcrumb
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class CreateConvBody(BaseModel):
    title: str = "新对话"


# === Widget / Embedded Chat (Guest Users) ===
# NOTE: /widget must come BEFORE /{conversation_id} to avoid route conflict

@router.post("/widget")
async def widget_chat(
    req: WidgetChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """嵌入式组件聊天 — 支持游客访问，通过 API Key 或来源域名验证."""
    # 支持通过 Authorization header 或 query param 传递 widget token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    if not verify_widget_token(token):
        # 也允许从 query param 传 token
        token_param = request.query_params.get("token", "")
        if not token_param or not verify_widget_token(token_param):
            raise HTTPException(status_code=401, detail="Invalid widget token")

    guest_id = req.guest_id or str(uuid.uuid4())
    conversation_id = req.conversation_id

    # 创建或查找对话
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.guest_id == guest_id
            )
        )
        conv = result.scalar_one_or_none()
    else:
        conv = None

    if not conv:
        conv = Conversation(guest_id=guest_id, title=req.query[:50] if len(req.query) > 50 else req.query)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    user_msg = Message(conversation_id=conv.id, role="user", content=req.query)
    db.add(user_msg)
    await db.commit()

    menu_cards = await _fetch_menu_cards(db, req.query)

    async def stream():
        full_answer = ""
        sources = []
        menu_cards_data = []
        steps_data = []

        async for chunk in generate_chat_stream(
            query=req.query,
            menu_cards=menu_cards,
            guest_id=guest_id,
        ):
            yield chunk
            data = json.loads(chunk.removeprefix("data: "))
            if data.get("type") == "text":
                full_answer += data.get("content", "")
            elif data.get("type") == "sources":
                sources = data.get("sources", [])
            elif data.get("type") == "menu_cards":
                menu_cards_data = data.get("menu_cards", data if isinstance(data, list) else [])
            elif data.get("type") == "steps":
                steps_data = data.get("steps", [])

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_answer,
            sources=json.dumps(sources, ensure_ascii=False),
            menu_cards=json.dumps(menu_cards_data, ensure_ascii=False),
            steps=json.dumps(steps_data, ensure_ascii=False),
        )
        db.add(assistant_msg)
        await db.commit()

        await log_event(
            db, "chat", "widget_ask", guest_id=guest_id,
            resource_type="conversation", resource_id=conv.id,
            detail=req.query[:200],
        )

        # 返回 guest_id 和 conversation_id
        yield "data: " + json.dumps({
            "type": "meta",
            "guest_id": guest_id,
            "conversation_id": conv.id,
        }, ensure_ascii=False) + "\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# === Conversations (must come BEFORE /{conversation_id}) ===

@router.get("/conversations")
async def list_conversations(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user["user_id"])
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return {
        "conversations": [
            {"id": c.id, "title": c.title, "created_at": c.created_at.isoformat(),
             "updated_at": c.updated_at.isoformat()}
            for c in convs
        ]
    }


@router.post("/conversations")
async def create_conversation(
    title: str = "新对话",
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(user_id=user["user_id"], title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return {"id": conv.id, "title": conv.title}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user["user_id"],
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    await db.delete(conv)
    await db.commit()
    return {"message": "已删除"}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user["user_id"],
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    msgs = result.scalars().all()
    return [
        {
            "id": m.id, "role": m.role, "content": m.content,
            "sources": m.sources, "menu_cards": m.menu_cards,
            "steps": m.steps, "intent": m.intent,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    req: FeedbackRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    msg.feedback = req.feedback
    await db.commit()
    await log_event(
        db, "chat", "feedback", user_id=user["user_id"],
        resource_type="message", resource_id=message_id,
        detail=f"Feedback: {req.feedback}",
    )
    return {"message": "反馈已记录"}


# === Admin / Logged-in User Chat ===

@router.post("/{conversation_id}")
async def chat_with_auth(
    conversation_id: str,
    req: ChatRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user["user_id"],
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    user_msg = Message(conversation_id=conversation_id, role="user", content=req.query)
    db.add(user_msg)
    await db.commit()

    menu_cards = await _fetch_menu_cards(db, req.query)

    async def stream():
        full_answer = ""
        sources = []
        menu_cards_data = []
        steps_data = []

        async for chunk in generate_chat_stream(
            query=req.query,
            menu_cards=menu_cards,
            user_id=user["user_id"],
            document_ids=req.document_ids,
        ):
            yield chunk
            data = json.loads(chunk.removeprefix("data: "))
            if data.get("type") == "text":
                full_answer += data.get("content", "")
            elif data.get("type") == "sources":
                sources = data.get("sources", [])
            elif data.get("type") == "menu_cards":
                menu_cards_data = data.get("menu_cards", data if isinstance(data, list) else [])
            elif data.get("type") == "steps":
                steps_data = data.get("steps", [])

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_answer,
            sources=json.dumps(sources, ensure_ascii=False),
            menu_cards=json.dumps(menu_cards_data, ensure_ascii=False),
            steps=json.dumps(steps_data, ensure_ascii=False),
        )
        db.add(assistant_msg)
        await db.commit()

        await log_event(
            db, "chat", "ask", user_id=user["user_id"],
            resource_type="conversation", resource_id=conversation_id,
            detail=req.query[:200],
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


# === Helpers ===

async def _fetch_menu_cards(db: AsyncSession, query: str, limit: int = 5) -> list[dict]:
    """预查询菜单卡片 — 在 API 层处理 DB 查询."""
    menus = await search_menus_by_keyword(db, query, limit=limit)
    cards = []
    for m in menus:
        breadcrumb = await get_menu_breadcrumb(db, m.id)
        cards.append({
            "menu_id": m.id,
            "menu_name": m.name,
            "route_path": m.route_path,
            "breadcrumb": breadcrumb,
            "description": m.description,
            "icon": m.icon,
        })
    return cards
