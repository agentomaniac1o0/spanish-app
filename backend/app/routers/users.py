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


@router.get("/{user_id}/context")
async def get_context(user_id: int, db: AsyncSession = Depends(get_db)):
    """User context for Hermes: level, known words, recent topics, grammar."""
    ctx = await crud.get_conversation_context(db, user_id)
    if not ctx:
        return {"error": "User not found"}
    due = await crud.get_due_words(db, user_id, limit=5)
    ctx["due_words"] = due
    return ctx


@router.get("/{user_id}/check-progression")
async def check_progression(user_id: int, db: AsyncSession = Depends(get_db)):
    """Check if user can advance to next level."""
    result = await crud.check_level_progression(db, user_id)
    if not result:
        return {"error": "User not found"}
    return result


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Full stats for /progreso command."""
    stats = await crud.get_stats(db, user_id)
    if not stats:
        return {"error": "User not found"}
    return {
        "level": stats["level"],
        "xp": stats["xp"],
        "streak": stats["streak"],
        "total_words": stats["total_words_learned"],
        "due_words": stats["words_due_today"],
        "lessons_completed": stats["lessons_completed"],
        "words_by_state": stats["words_by_state"],
    }
