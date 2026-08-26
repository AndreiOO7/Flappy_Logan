import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import ForeignKey, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    skins: Mapped[List["UserSkin"]] = relationship("UserSkin", back_populates="user", cascade="all, delete-orphan")
    equipped: Mapped["UserEquipped"] = relationship("UserEquipped", back_populates="user", uselist=False, cascade="all, delete-orphan")
    game_results: Mapped[List["GameResult"]] = relationship("GameResult", back_populates="user", cascade="all, delete-orphan")


class UserSkin(Base):
    __tablename__ = 'user_skins'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    skin_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="skins")

    __table_args__ = (UniqueConstraint('user_id', 'skin_id', name='_user_skin_uc'),)


class UserEquipped(Base):
    __tablename__ = 'user_equipped'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    birds: Mapped[str] = mapped_column(String(50), default="bird-default")
    pipes: Mapped[str] = mapped_column(String(50), default="pipe-default")
    backgrounds: Mapped[str] = mapped_column(String(50), default="bg-default")

    user: Mapped["User"] = relationship("User", back_populates="equipped")


class GameResult(Base):
    __tablename__ = 'game_results'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="game_results")