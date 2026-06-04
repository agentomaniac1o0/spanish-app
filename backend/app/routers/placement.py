from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import PlacementQuestion, PlacementResult

router = APIRouter(prefix="/placement", tags=["placement"])


@router.get("/question/{index}")
async def get_question(index: int):
    return await crud.get_placement_question(index)


@router.post("/evaluate", response_model=PlacementResult)
async def evaluate_placement(answers: list[dict]):
    return await crud.submit_placement_answer(answers)
