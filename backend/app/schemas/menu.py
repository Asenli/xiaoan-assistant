from pydantic import BaseModel
from datetime import datetime


class MenuCreate(BaseModel):
    name: str
    parent_id: str | None = None
    level: int = 0
    sort_order: int = 0
    route_path: str = ""
    icon: str = ""
    description: str = ""
    business_desc: str = ""
    keywords: str = ""
    related_knowledge_doc_ids: str | None = None


class MenuUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None
    level: int | None = None
    sort_order: int | None = None
    route_path: str | None = None
    icon: str | None = None
    description: str | None = None
    business_desc: str | None = None
    keywords: str | None = None
    related_knowledge_doc_ids: str | None = None
    is_visible: bool | None = None
    is_active: bool | None = None


class MenuResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    level: int
    sort_order: int
    route_path: str
    icon: str
    description: str
    business_desc: str
    keywords: str
    related_knowledge_doc_ids: str | None
    is_visible: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuTreeNode(BaseModel):
    """前端级联/树形组件使用的菜单节点."""
    id: str
    name: str
    route_path: str
    icon: str
    description: str
    level: int
    children: list["MenuTreeNode"] = []


class MenuCardResponse(BaseModel):
    """返回给聊天界面的可点击菜单卡片."""
    menu_id: str
    menu_name: str
    route_path: str
    breadcrumb: str        # e.g. "财务管理 > 结算对账"
    description: str
    icon: str
