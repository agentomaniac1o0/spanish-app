from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import UserProgress, UserRead, UserRegister

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRead)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await crud.get_or_create_user(db, data.telegram_id, data.username)
    return user


@router.get("/{user_id}/progress", response_model=UserProgress)
async def get_progress(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_progress(db, user_id)
