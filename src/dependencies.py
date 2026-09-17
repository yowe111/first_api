"""
dependencies.py — ЗАВИСИМОСТИ FASTAPI.

Что такое «зависимость»?
Это функция, результат которой FastAPI автоматически подставляет в обработчик
запроса. Например, «дай мне сессию базы» или «дай мне текущего пользователя».

Главная зависимость здесь — get_current_user. Она достаёт токен из запроса,
проверяет его и возвращает пользователя. Любой эндпоинт, который её использует,
автоматически становится ЗАЩИЩЁННЫМ (без токена туда не попасть).
"""

# Annotated — способ «приклеить» к типу дополнительную информацию.
# В FastAPI его используют вместе с Depends, чтобы объявлять зависимости.
from typing import Annotated

# Depends — объявление зависимости; HTTPException — способ вернуть ошибку;
# status — понятные названия HTTP-кодов (например, 401).
from fastapi import Depends, HTTPException, status

# OAuth2PasswordBearer — готовый инструмент FastAPI, который умеет
# доставать токен из заголовка запроса `Authorization: Bearer <токен>`.
from fastapi.security import OAuth2PasswordBearer

# select — строим SQL-запрос «выбрать ...» средствами SQLAlchemy.
from sqlalchemy import select

# AsyncSession — тип асинхронной сессии базы (для подсказки типа).
from sqlalchemy.ext.asyncio import AsyncSession

# Наши собственные модули:
from src.database import get_session       # зависимость, дающая сессию
from src.models import User                # модель пользователя (таблица)
from src.security import decode_access_token  # проверка/разбор токена


# Создаём объект, который будет извлекать токен из запроса.
# tokenUrl="/auth/login" — подсказка для документации: по этому адресу
# клиент получает токен (страница /docs использует это для кнопки Authorize).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Зависимость: получить текущего пользователя по токену.
# У функции два аргумента, и оба — тоже зависимости:
# - token: FastAPI достанет токен из заголовка через oauth2_scheme;
# - session: FastAPI откроет сессию базы через get_session.
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    # Проверяем токен и достаём из него логин (sub).
    username = decode_access_token(token)

    # Если токен плохой (None) — возвращаем ошибку 401 «не авторизован».
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,          # код 401
            detail="Неверный или просроченный токен",          # текст ошибки
            headers={"WWW-Authenticate": "Bearer"},            # стандартный заголовок
        )

    # Ищем пользователя в базе по логину из токена.
    # select(User).where(...) — «выбрать пользователя, у которого username такой-то».
    result = await session.execute(select(User).where(User.username == username))
    # scalar_one_or_none() — вернуть один объект или None, если не найден.
    user = result.scalar_one_or_none()

    # Токен валиден, но такого пользователя уже нет (например, удалили) — тоже 401.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Всё хорошо — возвращаем пользователя. FastAPI подставит его в обработчик.
    return user
