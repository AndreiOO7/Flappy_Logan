import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio

# Проверка базового ответа эндпоинта таблицы лидеров, когда в базе данных еще нет записей.
async def test_get_leaderboard_empty(client: AsyncClient):
    response = await client.get("/api/leaderboard")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["success"] is True
    assert "players" in data
    assert "total" in data
    assert len(data["players"]) == 0
    assert data["total"] == 0


# Проверка негативного сценария: попытка отправить результат игры без валидного JWT-токена авторизации (должен вернуться статус 401).
async def test_create_game_result_unauthorized(client: AsyncClient):
    payload = {
        "score": 150
    }
    response = await client.post("/api/game/result", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Проверка работы валидатора Query-параметров. Если лимит превышает 100, FastAPI должен автоматически выдать ошибку 422.
async def test_leaderboard_pagination_invalid_params(client: AsyncClient):
    invalid_params = {"limit": 150, "offset": 0}
    response = await client.get("/api/leaderboard", params=invalid_params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT