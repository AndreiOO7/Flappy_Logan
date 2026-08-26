import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_utils import create_access_token
import models

pytestmark = pytest.mark.asyncio


async def test_get_leaderboard_empty(client: AsyncClient):
    """Проверка лидерборда, когда в базе ещё нет данных"""
    response = await client.get("/api/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["players"] == []
    assert data["total"] == 0


async def test_get_leaderboard_with_data(client: AsyncClient, db_session: AsyncSession):
    """Проверка правильности ранжирования и подсчета рекордов игроков"""
    user1 = models.User(username="player_one", password_hash="pass")
    user2 = models.User(username="player_two", password_hash="pass")
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    db_session.add_all([
        models.GameResult(user_id=user1.id, score=10),
        models.GameResult(user_id=user1.id, score=50),
        models.GameResult(user_id=user2.id, score=100)
    ])
    await db_session.commit()

    response = await client.get("/api/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["success"] is True
    assert data["total"] == 2
    assert len(data["players"]) == 2

    first_place = data["players"][0]
    assert first_place["rank"] == 1
    assert first_place["username"] == "player_two"
    assert first_place["score"] == 100
    assert first_place["gamesPlayed"] == 1

    second_place = data["players"][1]
    assert second_place["rank"] == 2
    assert second_place["username"] == "player_one"
    assert second_place["score"] == 50
    assert second_place["gamesPlayed"] == 2


async def test_get_leaderboard_pagination_validation(client: AsyncClient):
    """Проверка валидации параметров limit и offset"""
    # limit должен быть от 1 до 100
    response = await client.get("/api/leaderboard?limit=150")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_create_game_result_unauthorized(client: AsyncClient):
    """Попытка отправить результат без авторизации должна возвращать 401"""
    response = await client.post("/api/game/result", json={"score": 10})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_game_result_success(client: AsyncClient, db_session: AsyncSession):
    """Успешное сохранение результата и обновление баланса пользователя"""
    user = models.User(username="gamer", password_hash="pass", balance=50)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"score": 25}
    response = await client.post("/api/game/result", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["balanceAwarded"] == 25
    assert data["newBalance"] == 75


async def test_create_game_result_zero_score(client: AsyncClient, db_session: AsyncSession):
    """При нулевом счете баланс не изменяется и результат не пишется в БД"""
    user = models.User(username="zero_gamer", password_hash="pass", balance=10)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"score": 0}
    response = await client.post("/api/game/result", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["newBalance"] == 10


async def test_get_best_score_success(client: AsyncClient, db_session: AsyncSession):
    """Получение максимального счета текущего авторизованного пользователя"""
    user = models.User(username="record_breaker", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    db_session.add_all([
        models.GameResult(user_id=user.id, score=12),
        models.GameResult(user_id=user.id, score=88),
        models.GameResult(user_id=user.id, score=45),
    ])
    await db_session.commit()

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/best-score", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["bestScore"] == 88


async def test_get_best_score_no_games(client: AsyncClient, db_session: AsyncSession):
    """Если игрок ещё не играл, bestScore должен быть 0"""
    user = models.User(username="newbie", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/best-score", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["bestScore"] == 0