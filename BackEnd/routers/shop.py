from fastapi import APIRouter, Depends
import os
import json
import models
import schemas
from core.auth_utils import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import JSONResponse

router = APIRouter(prefix="/api/shop", tags=["Shop"])

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "skins_catalog.json")

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    SKINS_CATALOG = json.load(f)


@router.get("/skins")
async def get_skins():
    return {
        "success": True,
        "skins": SKINS_CATALOG
    }


@router.get("/skins/user-skins")
async def get_user_skins(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(models.UserSkin).where(models.UserSkin.user_id == current_user.id)
    result = await db.execute(query)
    owned_skins = result.scalars().all()
    return {
        "success": True,
        "skins": owned_skins
    }


@router.post("/buy")
async def buy_skin(
        data: schemas.BuySkinRequest,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    skin_id = data.skinId

    request_skin = None
    for skin in SKINS_CATALOG:
        if skin['id'] == skin_id:
            request_skin = skin

    if not request_skin:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "BAD_REQUEST", "message": "Скин не найден в каталоге магазина."}
            }
        )
    query = select(models.UserSkin).where(models.UserSkin.user_id == current_user.id, models.UserSkin.skin_id == skin_id)
    result = await db.execute(query)
    if result.scalars().first():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "BAD_REQUEST", "message": "Этот скин у вас уже приобретен."}
            }
        )

    if current_user.balance < request_skin["price"]:
        return JSONResponse(
            status_code=402,
            content={
                "success": False,
                "error": {"code": "PAYMENT_REQUIRED", "message": "Недостаточно монет для покупки."}
            }
        )

    current_user.balance -= request_skin["price"]
    new_skin = models.UserSkin(skin_id=skin_id, user_id=current_user.id)

    db.add(new_skin)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {
        "success": True,
        "balance": current_user.balance,
        "skinId": skin_id,
    }


@router.get("/equipped")
async def get_equipped(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(models.UserEquipped).where(models.UserEquipped.user_id == current_user.id)
    execute_result = await db.execute(query)
    equipped_record = execute_result.scalar_one_or_none()

    if not equipped_record:
        equipped_skins = {
            "birds": "bird-default",
            "pipes": "pipe-default",
            "backgrounds": "bg-default"
        }
    else:
        equipped_skins = {
            "birds": equipped_record.birds,
            "pipes": equipped_record.pipes,
            "backgrounds": equipped_record.backgrounds
        }

    return {
        "success": True,
        "equipped": equipped_skins
    }


@router.post("/equip")
async def change_equipment(
        data: schemas.EquipSkinRequest,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    skin_id = data.skinId
    category = data.category

    query = select(models.UserSkin).where(models.UserSkin.user_id == current_user.id, models.UserSkin.skin_id == skin_id)
    executed_result = await db.execute(query)
    result = executed_result.scalar_one_or_none()
    if not result:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "BAD_REQUEST", "message": "Этот скин вам не принадлежит."}
            }
        )

    request_skin = None
    for skin in SKINS_CATALOG:
        if skin['id'] == skin_id and skin['category'] == data.category:
            request_skin = skin

    if not request_skin:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "BAD_REQUEST", "message": "Скин не найден или не соответствует категории."}
            }
        )

    query_equipped = select(models.UserEquipped).where(models.UserEquipped.user_id == current_user.id)
    execute_equipped = await db.execute(query_equipped)
    equipped_record = execute_equipped.scalar_one_or_none()

    if not equipped_record:
        equipped_record = models.UserEquipped(user_id=current_user.id)
        db.add(equipped_record)

    setattr(equipped_record, category, skin_id)

    await db.commit()
    await db.refresh(equipped_record)

    return {
        "success": True,
        "equipped": {
            "birds": equipped_record.birds,
            "pipes": equipped_record.pipes,
            "backgrounds": equipped_record.backgrounds
        }
    }