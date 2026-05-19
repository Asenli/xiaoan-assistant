from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import get_current_user, verify_widget_token
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse, MenuTreeNode, MenuCardResponse
from app.services import menu_service
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/menus", tags=["menus"])


@router.post("", response_model=MenuResponse)
async def create_menu(
    data: MenuCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    menu = await menu_service.create_menu(db, data.model_dump())
    await log_event(db, "menu", "create", user_id=user["user_id"],
                    resource_type="menu", resource_id=menu.id, detail=f"Created menu: {menu.name}")
    return menu


@router.get("", response_model=list[MenuResponse])
async def list_menus(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await menu_service.get_all_menus(db, active_only=active_only)


@router.get("/tree", response_model=list[MenuTreeNode])
async def get_menu_tree(db: AsyncSession = Depends(get_db)):
    return await menu_service.build_menu_tree(db)


@router.get("/search", response_model=list[MenuCardResponse])
async def search_menus(
    keyword: str = Query(...),
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    menus = await menu_service.search_menus_by_keyword(db, keyword, limit=limit)
    cards = []
    for m in menus:
        breadcrumb = await menu_service.get_menu_breadcrumb(db, m.id)
        cards.append(MenuCardResponse(
            menu_id=m.id, menu_name=m.name, route_path=m.route_path,
            breadcrumb=breadcrumb, description=m.description, icon=m.icon,
        ))
    return cards


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(menu_id: str, db: AsyncSession = Depends(get_db)):
    menus = await menu_service.get_all_menus(db, active_only=False)
    for m in menus:
        if m.id == menu_id:
            return m
    raise HTTPException(status_code=404, detail="菜单不存在")


@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: str, data: MenuUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        menu = await menu_service.update_menu(db, menu_id, data.model_dump(exclude_none=True))
        await log_event(db, "menu", "update", user_id=user["user_id"],
                        resource_type="menu", resource_id=menu_id, detail=f"Updated menu: {menu.name}")
        return menu
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await menu_service.delete_menu(db, menu_id)
    if not ok:
        raise HTTPException(status_code=404, detail="菜单不存在")
    await log_event(db, "menu", "delete", user_id=user["user_id"],
                    resource_type="menu", resource_id=menu_id)
    return {"message": "菜单已删除"}


@router.post("/batch-import")
async def batch_import(
    menus: list[dict],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await menu_service.batch_import_menus(db, menus)
    await log_event(db, "menu", "batch_import", user_id=user["user_id"],
                    detail=f"Imported {count} menus")
    return {"message": f"成功导入 {count} 个菜单", "count": count}
