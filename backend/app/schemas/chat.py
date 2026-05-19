from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    document_ids: list[str] | None = None
    conversation_id: str | None = None
    guest_id: str | None = None


class WidgetChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    guest_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[dict] = []
    menu_cards: list[dict] = []
    steps: list[dict] = []
    intent: str = ""


class FeedbackRequest(BaseModel):
    message_id: str
    feedback: int  # 1 = positive, -1 = negative
