from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.models import UserWord, Word
from app.schemas import UserWordRead, UserWordReview
from app.srs import seeding_card

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.get("/due", response_model=list[UserWordRead])
async def get_due(user_id: int, limit: int = Query(default=10, le=50), db: AsyncSession = Depends(get_db)):
    return await crud.get_due_words(db, user_id, limit)


@router.post("/review")
async def review_word(data: UserWordReview, db: AsyncSession = Depends(get_db)):
    result = await crud.review_word(db, data.user_id, data.word_id, data.rating)
    if result is None:
        return {"detail": "Wort nicht gefunden"}
    return result


@router.post("/assign")
async def assign_words(data: dict, db: AsyncSession = Depends(get_db)):
    """Assigns random new words to a user at their level. Used when user has no due words."""
    user_id = data.get("user_id")
    level = data.get("level", "A0")
    count = data.get("count", 10)

    if not user_id:
        return {"detail": "user_id required"}

    # Get words at user's level that aren't yet assigned
    result = await db.execute(
        select(Word).where(
            Word.level == level,
            ~Word.id.in_(
                select(UserWord.word_id).where(UserWord.user_id == user_id)
            )
        ).order_by(func.random()).limit(count)
    )
    words = result.scalars().all()

    assigned = []
    for word in words:
        # Check if UserWord already exists
        result = await db.execute(
            select(UserWord).where(UserWord.user_id == user_id, UserWord.word_id == word.id)
        )
        if result.scalar_one_or_none() is None:
            card = seeding_card(word.id)
            card.pop("word_id", None)
            uw = UserWord(user_id=user_id, word_id=word.id, source="lesson", **card)
            db.add(uw)
            assigned.append({
                "word_id": word.id,
                "spanish": word.spanish,
                "german": word.german,
                "unit": word.unit or "",
            })

    await db.commit()
    return {"words": assigned, "count": len(assigned)}


@router.post("/add")
async def add_word(data: dict, db: AsyncSession = Depends(get_db)):
    """Hermes adds a new word from conversation. Creates Word + UserWord."""
    user_id = data.get("user_id")
    spanish = data.get("spanish")
    german = data.get("german")
    word_type = data.get("word_type", "conversation")
    unit = data.get("unit", "conversation")
    level = data.get("level", "A1")

    if not user_id or not spanish or not german:
        return {"detail": "user_id, spanish und german required"}

    from sqlalchemy import select
    result = await db.execute(select(Word).where(Word.spanish == spanish))
    word = result.scalar_one_or_none()

    if word is None:
        word = Word(
            spanish=spanish, german=german,
            word_type=word_type, unit=unit, level=level,
        )
        db.add(word)
        await db.flush()

    result = await db.execute(
        select(UserWord).where(UserWord.user_id == user_id, UserWord.word_id == word.id)
    )
    if result.scalar_one_or_none() is None:
        card = seeding_card(word.id)
        uw = UserWord(user_id=user_id, word_id=word.id, source="conversation", **card)
        db.add(uw)
        await db.commit()
        return {"added": True, "word_id": word.id, "spanish": spanish}
    
    return {"added": False, "word_id": word.id, "reason": "already exists"}
