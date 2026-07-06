from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")


class UserAuth(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="Никнейм пользователя")
    password: str = Field(..., min_length=4, description="Пароль пользователя")

    @field_validator("username")
    @classmethod
    def validate_username_chars(cls, value: str) -> str:
        if not USERNAME_REGEX.match(value):
            raise ValueError("Юзернейм должен содержать только латиницу, цифры и нижнее подчеркивание (_)")
        return value


class ProfileUpdate(BaseModel):
    currentPassword: str = Field(..., description="Текущий пароль для подтверждения")
    newUsername: Optional[str] = Field(None, min_length=3, max_length=20, description="Новый юзернейм")
    newPassword: Optional[str] = Field(None, min_length=4, description="Новый пароль")

    @field_validator("newUsername")
    @classmethod
    def validate_new_username(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not USERNAME_REGEX.match(value):
            raise ValueError("Новый юзернейм должен содержать только латиницу, цифры и нижнее подчеркивание (_)")
        return value


class BuySkinRequest(BaseModel):
    skinId: str = Field(..., description="ID покупаемого скина")


class EquipSkinRequest(BaseModel):
    skinId: str = Field(..., description="ID надеваемого скина")
    category: str = Field(..., description="Категория скина (birds, pipes, backgrounds)")

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        allowed_categories = {"birds", "pipes", "backgrounds"}
        if value not in allowed_categories:
            raise ValueError("Категория должна быть одной из: birds, pipes, backgrounds")
        return value


class GameResultRequest(BaseModel):
    score: int = Field(..., ge=0, description="Количество набранных очков")
    gamesPlayed: Optional[int] = None