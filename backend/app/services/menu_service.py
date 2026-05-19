"""系统菜单路由映射服务 — CRUD + 关键词搜索 + 树形结构."""
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.menu import SystemMenu


async def create_menu(db: AsyncSession, data: dict) -> SystemMenu:
    menu = SystemMenu(**data)
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return menu


async def update_menu(db: AsyncSession, menu_id: str, data: dict) -> SystemMenu:
    result = await db.execute(select(SystemMenu).where(SystemMenu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise ValueError("菜单不存在")
    for key, value in data.items():
        if value is not None and hasattr(menu, key):
            setattr(menu, key, value)
    await db.commit()
    await db.refresh(menu)
    return menu


async def delete_menu(db: AsyncSession, menu_id: str) -> bool:
    result = await db.execute(select(SystemMenu).where(SystemMenu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        return False
    # 删除子菜单
    children = await db.execute(
        select(SystemMenu).where(SystemMenu.parent_id == menu_id)
    )
    for child in children.scalars().all():
        await db.delete(child)
    await db.delete(menu)
    await db.commit()
    return True


async def get_all_menus(db: AsyncSession, active_only: bool = True) -> list[SystemMenu]:
    q = select(SystemMenu).order_by(SystemMenu.level, SystemMenu.sort_order)
    if active_only:
        q = q.where(SystemMenu.is_active == True)
    result = await db.execute(q)
    return result.scalars().all()


async def build_menu_tree(db: AsyncSession) -> list[dict]:
    menus = await get_all_menus(db)
    menu_map = {m.id: {**m.__dict__, "children": []} for m in menus}
    roots = []
    for m in menus:
        node = menu_map[m.id]
        node.pop("_sa_instance_state", None)
        if m.parent_id and m.parent_id in menu_map:
            menu_map[m.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


async def search_menus_by_keyword(db: AsyncSession, keyword: str, limit: int = 10) -> list[SystemMenu]:
    """根据关键词搜索匹配的菜单项 — 匹配名称、关键词、描述."""
    pattern = f"%{keyword}%"
    result = await db.execute(
        select(SystemMenu)
        .where(
            SystemMenu.is_active == True,
            SystemMenu.is_visible == True,
            or_(
                SystemMenu.name.ilike(pattern),
                SystemMenu.keywords.ilike(pattern),
                SystemMenu.description.ilike(pattern),
                SystemMenu.business_desc.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    return result.scalars().all()


async def get_menu_breadcrumb(db: AsyncSession, menu_id: str) -> str:
    """获取菜单的面包屑路径，如 '财务管理 > 结算对账'."""
    result = await db.execute(select(SystemMenu).where(SystemMenu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        return ""

    parts = [menu.name]
    current_parent_id = menu.parent_id
    while current_parent_id:
        parent_result = await db.execute(
            select(SystemMenu).where(SystemMenu.id == current_parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            parts.insert(0, parent.name)
            current_parent_id = parent.parent_id
        else:
            break
    return " > ".join(parts)


async def batch_import_menus(db: AsyncSession, menus: list[dict]) -> int:
    """批量导入菜单 — 用于初始化系统菜单结构."""
    count = 0
    for item in menus:
        menu = SystemMenu(**item)
        db.add(menu)
        count += 1
    await db.commit()
    return count
