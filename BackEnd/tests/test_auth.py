import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth_utils import create_access_token, get_password_hash, verify_password
import models

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient, db_session: AsyncSession):
    """Успешная регистрация и автосоздание дефолтных скинов"""
    payload = {"username": "new_user", "password": "password123"}
    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == "new_user"

    user_query = await db_session.execute(select(models.User).where(models.User.username == "new_user"))
    user = user_query.scalars().first()
    assert user is not None

    skins_query = await db_session.execute(select(models.UserSkin.skin_id).where(models.UserSkin.user_id == user.id))
    user_skins = set(skins_query.scalars().all())
    assert user_skins == {"bird-default", "pipe-default", "bg-default"}


async def test_register_duplicate_username(client: AsyncClient):
    """Ошибка 409 при попытке зарегистрировать занятый ник"""
    payload = {"username": "existing_user", "password": "password123"}
    await client.post("/api/auth/register", json=payload)

    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    """Успешный вход через JSON"""
    user = models.User(username="auth_user", password_hash=get_password_hash("secret123"))
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/login", json={"username": "auth_user", "password": "secret123"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "auth_user"


async def test_swagger_login_success(client: AsyncClient, db_session: AsyncSession):
    """Успешный вход через OAuth2 form-data (для Swagger)"""
    user = models.User(username="swagger_user", password_hash=get_password_hash("secret123"))
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/swagger-login", data={"username": "swagger_user", "password": "secret123"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


async def test_login_wrong_credentials(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 401 при неверном пароле или несуществующем пользователе"""
    user = models.User(username="real_user", password_hash=get_password_hash("correct_pass"))
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/auth/login", json={"username": "real_user", "password": "wrong_pass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["success"] is False

    response = await client.post("/api/auth/login", json={"username": "unknown_user", "password": "correct_pass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_me_success(client: AsyncClient, db_session: AsyncSession):
    """Успешное получение данных профиля авторизованного юзера"""
    user = models.User(username="me_user", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"]["username"] == "me_user"


async def test_get_me_unauthorized(client: AsyncClient):
    """Ошибка 401 при запросе без Bearer токена"""
    response = await client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_update_profile_username_success(client: AsyncClient, db_session: AsyncSession):
    """Успешное обновление имени пользователя"""
    user = models.User(username="old_name", password_hash=get_password_hash("pass123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"currentPassword": "pass123", "newUsername": "new_name"}
    response = await client.put("/api/auth/profile", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user"]["username"] == "new_name"


async def test_update_profile_password_success(client: AsyncClient, db_session: AsyncSession):
    """Успешная смена пароля"""
    user = models.User(username="pass_changer", password_hash=get_password_hash("old_pass123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"currentPassword": "old_pass123", "newPassword": "new_super_pass"}
    response = await client.put("/api/auth/profile", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED

    await db_session.refresh(user)
    assert verify_password("new_super_pass", user.password_hash) is True


async def test_update_profile_wrong_current_password(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 401 при указании некорректного текущего пароля"""
    user = models.User(username="wrong_current", password_hash=get_password_hash("real_pass"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"currentPassword": "invalid_pass", "newUsername": "brand_new"}
    response = await client.put("/api/auth/profile", json=payload, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_update_profile_occupied_username(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 409 при попытке сменить имя на уже занятое"""
    user1 = models.User(username="user1", password_hash=get_password_hash("pass"))
    user2 = models.User(username="user2", password_hash=get_password_hash("pass"))
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)

    token = create_access_token(data={"userId": str(user1.id), "sub": user1.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"currentPassword": "pass", "newUsername": "user2"}
    response = await client.put("/api/auth/profile", json=payload, headers=headers)
    assert response.status_code == status.HTTP_409_CONFLICT


async def test_update_profile_empty_payload(client: AsyncClient, db_session: AsyncSession):
    """Ошибка 400, если не передано ни новое имя, ни новый пароль"""
    user = models.User(username="lazy_user", password_hash=get_password_hash("pass"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"currentPassword": "pass"}
    response = await client.put("/api/auth/profile", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST