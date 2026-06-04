from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import UserWordRead, UserWordReview

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.get("/due", response_model=list[UserWordRead])
async def get_due(user_id: int, limit: int = Query(default=10, le=50), db: AsyncSession = Depends(get_db)):
    return await crud.get_due_words(db, user_id, limit)


@router.post("/review")
async def review_word(data: UserWordReview, user_id: int, db: AsyncSession = Depends(get_db)):
    result = await crud.review_word(db, user_id, data.word_id, data.rating)
    if result is None:
        return {"detail": "Wort nicht gefunden"}
    return result
