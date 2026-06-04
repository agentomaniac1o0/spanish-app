from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import ConversationContext, GrammarPointRead, StatsResponse

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.get("/context", response_model=ConversationContext)
async def get_context(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_conversation_context(db, user_id)


@router.get("/grammar", response_model=list[GrammarPointRead])
async def get_grammar(level: str = Query(default=None), db: AsyncSession = Depends(get_db)):
    return await crud.get_grammar_points(db, level)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_stats(db, user_id)
