from fastapi import Depends, status, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import backend.models as models
import backend.schemas as schemas
from core.database import get_db
from core.auth_utils import get_password_hash, verify_password, create_access_token, get_current_user
from core.database import format_user_response


router = APIRouter(prefix="/api/auth", tags=["Authentication & Authorization"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserAuth, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(models.User.username == user_data.username)
    result = await db.execute(query)
    if result.scalars().first():
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": {"code": "CONFLICT", "message": "Пользователь с данным именем уже существует."}}
        )

    new_user = models.User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(new_user)
    await db.flush()

    default_skins = ["bird-default", "pipe-default", "bg-default"]
    for s_id in default_skins:
        db.add(models.UserSkin(user_id=new_user.id, skin_id=s_id))

    db.add(models.UserEquipped(user_id=new_user.id))

    await db.commit()
    await db.refresh(new_user)

    return {
        "success": True,
        "user": format_user_response(new_user, default_skins)
    }


@router.post("/login")
async def login(user_data: schemas.UserAuth, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(models.User.username == user_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Неверный логин или пароль"}}
        )

    skins_query = select(models.UserSkin.skin_id).where(models.UserSkin.user_id == user.id)
    skins_result = await db.execute(skins_query)
    user_skins = list(skins_result.scalars().all())

    token = create_access_token(data={"userId": str(user.id), "sub": user.username})

    return {
        "success": True,
        "token": token,
        "user": format_user_response(user, user_skins)
    }


@router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    skins_query = select(models.UserSkin.skin_id).where(models.UserSkin.user_id == current_user.id)
    skins_result = await db.execute(skins_query)
    user_skins = list(skins_result.scalars().all())

    return {
        "success": True,
        "user": format_user_response(current_user, user_skins)
    }


@router.put("/profile", status_code=status.HTTP_201_CREATED)
async def update_profile(data: schemas.ProfileUpdate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(data.currentPassword, current_user.password_hash):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Текущий пароль неверен."}}
        )
    is_changed = False

    if data.newUsername and data.newUsername != current_user.username:
        query = select(models.User).where(models.User.username == data.newUsername)
        result = await db.execute(query)
        if result.scalars().first():
            return JSONResponse(
                status_code=409,
                content={"success": False,
                         "error": {"code": "CONFLICT", "message": "Данное имя занято."}}
            )
        current_user.username = data.newUsername
        is_changed = True

    if data.newPassword:
        current_user.password_hash = get_password_hash(data.newPassword)
        is_changed = True

    if not data.newPassword and not data.newUsername:
        return JSONResponse(
            status_code=400,
            content={"success": False,
                     "error": {"code": "BAD_REQUEST", "message": "Не переданы данные для обновления."}}
        )

    if is_changed:
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)

    skins_query = select(models.UserSkin.skin_id).where(models.UserSkin.user_id == current_user.id)
    skins_result = await db.execute(skins_query)
    user_skins = list(skins_result.scalars().all())

    return {
        "success": True,
        "user": format_user_response(current_user, user_skins)
    }