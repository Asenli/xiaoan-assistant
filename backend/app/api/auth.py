from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import register_user, login_user
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await register_user(db, req.username, req.password)
        await log_event(db, "auth", "register", user_id=result["user_id"], detail=f"User {req.username} registered")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await login_user(db, req.username, req.password)
        await log_event(db, "auth", "login", user_id=result["user_id"], detail="User logged in")
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
