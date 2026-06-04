from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import LessonComplete, LessonRead, LessonSummary

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/list", response_model=list[LessonSummary])
async def list_lessons(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_lesson_list(db, user_id)


@router.get("/next")
async def get_next(user_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await crud.get_next_lesson(db, user_id)
    if lesson is None:
        return {"detail": "Keine Lektionen mehr verfügbar"}
    content = await crud.get_lesson_content(db, lesson.id)
    return LessonRead.model_validate(content)


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    content = await crud.get_lesson_content(db, lesson_id)
    if content is None:
        return {"detail": "Lektion nicht gefunden"}
    return LessonRead.model_validate(content)


@router.post("/{lesson_id}/complete")
async def complete(lesson_id: int, data: LessonComplete, user_id: int, db: AsyncSession = Depends(get_db)):
    await crud.complete_lesson(db, user_id, lesson_id, data.score, data.time_spent)
    return {"status": "completed"}
