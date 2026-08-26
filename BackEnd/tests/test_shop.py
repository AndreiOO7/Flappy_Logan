import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth_utils import create_access_token
from routers.shop import SKINS_CATALOG
import models

pytestmark = pytest.mark.asyncio


async def test_get_skins_catalog(client: AsyncClient):
    """Проверка получения реального каталога"""
    response = await client.get("/api/shop/skins")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["skins"] == SKINS_CATALOG


async def test_get_user_skins_success(client: AsyncClient, db_session: AsyncSession):
    """Получение списка купленных скинов пользователя"""
    user = models.User(username="collector", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    db_session.add_all([
        models.UserSkin(user_id=user.id, skin_id="bird-default"),
        models.UserSkin(user_id=user.id, skin_id="pipe-default")
    ])
    await db_session.commit()

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/shop/skins/user-skins", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert len(data["skins"]) == 2


async def test_buy_skin_success(client: AsyncClient, db_session: AsyncSession):
    """Покупка первого платного скина из реального каталога"""
    target_skin = SKINS_CATALOG[0]
    initial_balance = target_skin["price"] + 100

    user = models.User(username="rich_buyer", password_hash="pass", balance=initial_balance)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/shop/buy", json={"skinId": target_skin["id"]}, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["balance"] == 100
    assert data["skinId"] == target_skin["id"]

    skin_query = await db_session.execute(
        select(models.UserSkin).where(models.UserSkin.user_id == user.id, models.UserSkin.skin_id == target_skin["id"])
    )
    assert skin_query.scalar_one_or_none() is not None


async def test_buy_skin_not_found(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 400 при покупке несуществующего скина"""
    user = models.User(username="buyer", password_hash="pass", balance=1000)
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/shop/buy", json={"skinId": "non-existent-skin-id"}, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "BAD_REQUEST"


async def test_buy_skin_already_owned(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 400 при повторной покупке"""
    target_skin = SKINS_CATALOG[0]
    user = models.User(username="owner", password_hash="pass", balance=target_skin["price"] * 2)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    db_session.add(models.UserSkin(user_id=user.id, skin_id=target_skin["id"]))
    await db_session.commit()

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/shop/buy", json={"skinId": target_skin["id"]}, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["message"] == "Этот скин у вас уже приобретен."


async def test_buy_skin_insufficient_funds(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 402 при нехватке монет"""
    target_skin = next(s for s in SKINS_CATALOG if s["price"] > 0)
    user = models.User(username="poor_buyer", password_hash="pass", balance=target_skin["price"] - 1)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/shop/buy", json={"skinId": target_skin["id"]}, headers=headers)
    assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"]["code"] == "PAYMENT_REQUIRED"


async def test_get_equipped_default(client: AsyncClient, db_session: AsyncSession):
    """Дефолтная экипировка для нового пользователя"""
    user = models.User(username="fresh_user", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/shop/equipped", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["equipped"] == {
        "birds": "bird-default",
        "pipes": "pipe-default",
        "backgrounds": "bg-default"
    }


async def test_equip_skin_success(client: AsyncClient, db_session: AsyncSession):
    """Успешное надевание реального скина"""
    target_skin = SKINS_CATALOG[0]
    user = models.User(username="fashion_user", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    db_session.add(models.UserSkin(user_id=user.id, skin_id=target_skin["id"]))
    db_session.add(models.UserEquipped(user_id=user.id))
    await db_session.commit()

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"skinId": target_skin["id"], "category": target_skin["category"]}
    response = await client.post("/api/shop/equip", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["equipped"][target_skin["category"]] == target_skin["id"]


async def test_equip_skin_not_owned(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 400 при попытке надеть некупленный скин"""
    target_skin = SKINS_CATALOG[0]
    user = models.User(username="tricky_user", password_hash="pass")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"skinId": target_skin["id"], "category": target_skin["category"]}
    response = await client.post("/api/shop/equip", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["message"] == "Этот скин вам не принадлежит."