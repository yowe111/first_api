"""
routers/users.py — ЭНДПОИНТЫ ПОЛЬЗОВАТЕЛЕЙ.

Здесь показан пример ЗАЩИЩЁННОГО эндпоинта: чтобы его вызвать,
нужно прислать действительный токен (получить его можно на /auth/login).
"""

from typing import Annotated

# APIRouter — группа эндпоинтов; Depends — подключение зависимости.
from fastapi import APIRouter, Depends

# Наша зависимость: она проверит токен и вернёт текущего пользователя.
from src.dependencies import get_current_user
# Модель пользователя (для подсказки типа).
from src.models import User
# Схема ответа (без пароля).
from src.schemas import UserRead
from src.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Роутер: все адреса начинаются с /users, группа «Пользователи» в /docs.
router = APIRouter(prefix="/users", tags=["Пользователи"])


# Эндпоинт GET /users/me — «покажи данные обо мне».
# GET — тип запроса для ПОЛУЧЕНИЯ данных.
# response_model=UserRead — ответ в форме схемы UserRead.
@router.get("/me", response_model=UserRead)
async def read_me(
    # Вот здесь и происходит «защита»:
    # Depends(get_current_user) требует валидный токен. Если токена нет
    # или он неверный — FastAPI сам вернёт ошибку 401 и до тела функции
    # выполнение даже не дойдёт.
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Возвращает данные текущего пользователя (того, чей токен прислан)."""
    # Просто возвращаем пользователя; FastAPI отдаст его как JSON по UserRead.
    return current_user

@router.get("/", response_model=UserRead)
async def read_users(session: Annotated[AsyncSession, Depends(get_session)]
    ):
    users = await session.execute(select(User).all())

    return users 
