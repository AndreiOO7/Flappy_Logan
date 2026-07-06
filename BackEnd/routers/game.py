from fastapi import APIRouter, Depends, Query
import models
import schemas
from core.auth_utils import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

router = APIRouter(prefix="/api", tags=["Game & Leaderboard"])

@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)):
    total_query = select(func.count(func.distinct(models.GameResult.user_id)))
    total_result = await db.execute(total_query)
    total_players = total_result.scalar() or 0
    query = (
        select(
            models.User.username,
            func.max(models.GameResult.score).label("max_score"),
            func.count(models.GameResult.id).label("games_played"),)
        .join(models.GameResult, models.User.id == models.GameResult.user_id)
        .group_by(models.User.id, models.User.username)
        .order_by(desc("max_score"))
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    leaderboard_rows = result.all()

    players_list = []

    for index, row in enumerate(leaderboard_rows):
        rank = index + offset + 1

        players_list.append({
            "rank": rank,
            "username": row.username,
            "score": row.max_score,
            "gamesPlayed": row.games_played,
        })

    return {
        "success": True,
        "players": players_list,
        "total": total_players,
    }


@router.post("/game/result")
async def create_game_result(
        data: schemas.GameResultRequest,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    score = data.score

    new_result = models.GameResult(
        user_id=current_user.id,
        score=score
    )
    db.add(new_result)

    current_user.balance += score
    db.add(current_user)

    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "balanceAwarded": score,
        "newBalance": current_user.balance,
    }